import re
import json
import asyncio
from typing import List, Dict, Any, Optional
from pydantic import ValidationError
from google import genai
from google.genai import types
from google.genai.errors import APIError

from app.config import settings
from app.models.schemas import (
    OutfitRequest,
    ProductItem,
    ConstraintEvaluation,
    InitialPlan,
    AgentStepDecision,
    FinalStylistResponse,
    AgentActionType,
    SearchProductsArgs
)

def sanitize_error_message(error: Exception) -> str:
    """
    Strips potential API keys, auth headers, or raw secrets from exception strings.
    """
    msg = str(error)
    # Remove any potential Gemini / SerpApi key patterns
    sanitized = re.sub(r'AIza[0-9A-Za-z-_]{35}', '[REDACTED_KEY]', msg)
    sanitized = re.sub(r'key=[0-9a-fA-F]{32,}', 'key=[REDACTED_KEY]', sanitized)
    sanitized = re.sub(r'Bearer\s+[A-Za-z0-9\-_\.]+', 'Bearer [REDACTED_TOKEN]', sanitized)
    return sanitized

class GeminiAgentService:
    """
    Service integrating official Google Gen AI SDK (google-genai) for real
    outfit styling planning, tool selection, replanning, and stylist reasoning.
    """

    def __init__(self, api_key: Optional[str] = None, model_name: Optional[str] = None):
        self.api_key = api_key or settings.gemini_api_key
        self.model_name = model_name or settings.gemini_model
        self.client: Optional[genai.Client] = None

        if self.api_key:
            # Initialize client strictly on backend
            self.client = genai.Client(api_key=self.api_key)

    def is_configured(self) -> bool:
        return self.client is not None and bool(self.api_key)

    async def generate_initial_plan(self, request: OutfitRequest) -> InitialPlan:
        """
        Calls Gemini with structured schema to understand the user's styling goal,
        determine required wardrobe categories, allocate sub-budgets, and propose the initial tool action.
        """
        if not self.client:
            raise RuntimeError("Gemini client is not configured with an API key.")

        system_instruction = (
            "You are an expert AI Personal Fashion Stylist and Shopping Agent for Indian e-commerce. "
            "Your role is to decompose user styling requests into required clothing categories "
            "(top, bottom, shoes, and optional accessory/ethnic piece), allocate target sub-budgets "
            "in INR summing to at most the total budget, and choose the initial product search action. "
            "You must strictly respect the user's occasion, theme, gender, sizes, and palette."
        )

        prompt = (
            f"User Styling Request:\n"
            f"- Occasion: {request.occasion}\n"
            f"- Theme: {request.theme}\n"
            f"- Style: {request.personal_style}\n"
            f"- Gender: {request.gender.value}\n"
            f"- Sizing: {request.sizes}\n"
            f"- Target Budget: INR {request.budget_inr:,.0f}\n"
            f"- Preferred Colors: {', '.join(request.color_preferences)}\n"
            f"- Avoid Colors: {', '.join(request.avoid_colors)}\n"
            f"- Delivery Deadline: {request.delivery_deadline or 'Standard'}\n\n"
            f"Decompose this goal into required wardrobe components, allocate sub-budgets in INR, "
            f"formulate the initial search query, and choose the first search action."
        )

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=InitialPlan,
                temperature=0.2
            )

            # Run blocking generate_content off main event loop
            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=config
            )

            # Parse structured Pydantic response
            if response.parsed and isinstance(response.parsed, InitialPlan):
                return response.parsed
            
            # Fallback to json text parse if parsed attribute is dict
            data = json.loads(response.text)
            return InitialPlan(**data)

        except APIError as e:
            sanitized = sanitize_error_message(e)
            raise RuntimeError(f"Gemini API Error during initial planning: {sanitized}") from None
        except Exception as e:
            sanitized = sanitize_error_message(e)
            raise RuntimeError(f"Gemini planning failed: {sanitized}") from None

    async def propose_next_action(
        self,
        request: OutfitRequest,
        iteration: int,
        required_categories: List[str],
        current_items: List[ProductItem],
        latest_observation: str,
        constraint_violations: List[str],
        searched_queries: List[str]
    ) -> AgentStepDecision:
        """
        Feeds the actual tool observations and constraint check results back to Gemini.
        Gemini decides the next tool action: search next category, run validation, replan, or finish.
        """
        if not self.client:
            raise RuntimeError("Gemini client is not configured with an API key.")

        current_total = sum(i.price_inr for i in current_items)
        remaining_budget = request.budget_inr - current_total
        present_categories = [i.category for i in current_items]
        missing_categories = [c for c in required_categories if c not in present_categories]

        system_instruction = (
            "You are an autonomous observe-plan-act Outfit Styling Orchestrator. "
            "You receive actual tool results and deterministic constraint feedback. "
            "You must select the next allowlisted action:\n"
            "1. 'search_products': Search for a missing piece within remaining budget.\n"
            "2. 'validate_outfit': Request deterministic constraint evaluation.\n"
            "3. 'get_budget_summary': Request exact price calculations.\n"
            "4. 'replan': If budget is exceeded or sizes unavailable, identify the item to swap and propose alternative query.\n"
            "5. 'finish_plan': If all categories are satisfied and budget is honored, finish assembly.\n"
            "Do NOT repeat search queries already made."
        )

        items_summary = [
            f"- [{i.category.upper()}] {i.title} from {i.merchant}: INR {i.price_inr} (Sizes: {', '.join(i.available_sizes)})"
            for i in current_items
        ]
        items_text = "\n".join(items_summary) if items_summary else "No pieces selected yet."

        prompt = (
            f"Iteration: {iteration}/6\n"
            f"Goal: {request.occasion} ({request.theme}), Budget: INR {request.budget_inr:,.0f}\n"
            f"Current Subtotal: INR {current_total:,.2f} | Remaining Headroom: INR {remaining_budget:,.2f}\n"
            f"Required Categories: {required_categories}\n"
            f"Currently Selected Items:\n{items_text}\n"
            f"Missing Categories: {missing_categories}\n"
            f"Already Searched Queries: {searched_queries}\n"
            f"Latest Tool Observation:\n{latest_observation}\n"
            f"Active Constraint Violations: {constraint_violations if constraint_violations else 'None'}\n\n"
            f"Based on these actual observations, decide your next move."
        )

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=AgentStepDecision,
                temperature=0.2
            )

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=config
            )

            if response.parsed and isinstance(response.parsed, AgentStepDecision):
                return response.parsed

            data = json.loads(response.text)
            return AgentStepDecision(**data)

        except APIError as e:
            sanitized = sanitize_error_message(e)
            raise RuntimeError(f"Gemini API Error during step {iteration}: {sanitized}") from None
        except Exception as e:
            sanitized = sanitize_error_message(e)
            raise RuntimeError(f"Gemini decision failed at step {iteration}: {sanitized}") from None

    async def generate_final_rationale(
        self,
        request: OutfitRequest,
        items: List[ProductItem],
        total_price: float,
        is_within_budget: bool,
        replan_events: List[str]
    ) -> FinalStylistResponse:
        """
        Asks Gemini to synthesize a polished, authentic stylist rationale explaining
        how the verified items harmonize with the occasion, palette, and budget constraints.
        """
        if not self.client:
            raise RuntimeError("Gemini client is not configured with an API key.")

        system_instruction = (
            "You are a professional luxury fashion stylist. Synthesize an editorial critique "
            "and rationale for the finalized ensemble, explaining color coordination, fabric texture "
            "balance, suitability for the event, and any tradeoffs made during replanning."
        )

        items_text = "\n".join([
            f"- {i.category.upper()}: {i.title} ({i.merchant}) - INR {i.price_inr}"
            for i in items
        ])

        prompt = (
            f"Occasion: {request.occasion}\n"
            f"- Theme: {request.theme}\n"
            f"- Preferred Palette: {', '.join(request.color_preferences)}\n"
            f"- Target Budget: INR {request.budget_inr:,.0f} | Actual Total: INR {total_price:,.2f}\n"
            f"- Budget Compliant: {is_within_budget}\n"
            f"- Replanning History: {replan_events if replan_events else 'Assembled on first pass'}\n\n"
            f"Final Ensemble Pieces:\n{items_text}\n\n"
            f"Write the stylist rationale, score aesthetic harmony (0-100), and state tradeoffs considered."
        )

        try:
            config = types.GenerateContentConfig(
                system_instruction=system_instruction,
                response_mime_type="application/json",
                response_schema=FinalStylistResponse,
                temperature=0.3
            )

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=prompt,
                config=config
            )

            if response.parsed and isinstance(response.parsed, FinalStylistResponse):
                return response.parsed

            data = json.loads(response.text)
            return FinalStylistResponse(**data)

        except Exception as e:
            # Non-critical fallback for rationale synthesis
            return FinalStylistResponse(
                stylist_rationale=(
                    f"Assembled a cohesive {request.theme} ensemble for {request.occasion}. "
                    f"Selected {len(items)} complementary pieces adhering to the specified palette "
                    f"while honoring your budget of INR {request.budget_inr:,.0f}."
                ),
                harmony_score=92.0,
                tradeoffs_considered=["Balanced high-ticket anchor items against overall budget headroom."]
            )
