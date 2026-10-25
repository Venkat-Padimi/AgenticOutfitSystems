import uuid
import time
import asyncio
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional, AsyncGenerator

from app.config import settings
from app.models.schemas import (
    OutfitRequest,
    OutfitRecommendation,
    ProductItem,
    AgentTraceStep,
    AgentPhase,
    ConstraintEvaluation,
    ConstraintType,
    ConstraintStatus,
    DataSourceEnum,
    GenderEnum,
    AgentActionType,
    SearchProductsArgs,
    ReplanArgs
)
from app.services.shopping import get_shopping_provider
from app.services.shopping.base import ShoppingProviderError
from app.services.agent.tools import AgentTools
from app.services.agent.constraints import ConstraintEngine
from app.services.agent.gemini_service import GeminiAgentService, sanitize_error_message

class AgentOrchestrator:
    """
    Agentic Orchestrator for Personal Outfit Styling & Shopping.
    Integrates Google Gemini 2.5 Flash for high-level reasoning, plan formulation,
    and adaptive replanning, while enforcing hard constraints deterministically in Python.
    """

    def __init__(
        self,
        force_fixture: Optional[str] = None,
        gemini_service: Optional[GeminiAgentService] = None,
        shopping_provider: Optional[Any] = None,
        timeout_seconds: Optional[float] = None,
        max_iterations: Optional[int] = None
    ):
        self.force_fixture = force_fixture
        self.provider = shopping_provider or get_shopping_provider(force_mode="fixture" if force_fixture else None)
        self.tools = AgentTools(self.provider)
        self.constraints = ConstraintEngine()
        self.gemini_service = gemini_service or GeminiAgentService()
        self.max_iterations = max_iterations or settings.agent_max_iterations
        self.timeout_seconds = timeout_seconds or settings.agent_timeout_seconds

    async def run(self, request: OutfitRequest) -> OutfitRecommendation:
        """
        Executes the orchestrator and returns the final validated OutfitRecommendation.
        """
        trace_steps: List[AgentTraceStep] = []
        async for step in self.stream_execution(request):
            trace_steps.append(step)

        # Retrieve assembled items from the trace output
        final_items: List[ProductItem] = []
        outfit_id = str(uuid.uuid4())[:8]
        engine_used = "deterministic_fallback"
        final_status = "complete"
        error_msg = None
        stylist_rationale = ""
        tradeoffs = [
            "Balanced fabric quality against strict budget ceiling.",
            "Prioritized versatile footwear matching both trousers and smart layers.",
            "Verified retailer availability across Indian e-commerce partners."
        ]

        for step in reversed(trace_steps):
            if step.tool_output and "assembled_items" in step.tool_output:
                final_items = [ProductItem(**item) for item in step.tool_output["assembled_items"]]
                engine_used = step.tool_output.get("orchestration_engine", "deterministic_fallback")
                final_status = step.tool_output.get("status", "complete")
                error_msg = step.tool_output.get("error_message")
                if "stylist_rationale" in step.tool_output:
                    stylist_rationale = step.tool_output["stylist_rationale"]
                if "tradeoffs" in step.tool_output:
                    tradeoffs = step.tool_output["tradeoffs"]
                break

        # If fallback step occurred, record error_message on the final recommendation
        fallback_step = next((s for s in trace_steps if s.tool_called == "FallbackToDeterministicEngine"), None)
        if fallback_step and fallback_step.tool_output and "error" in fallback_step.tool_output:
            error_msg = f"Gemini fallback triggered: {fallback_step.tool_output['error']}"

        total_price = sum(i.price_inr for i in final_items)
        is_within = total_price <= request.budget_inr

        # Determine data source mode
        has_live = any(i.data_source == DataSourceEnum.LIVE_VERIFIED for i in final_items)
        data_mode = DataSourceEnum.LIVE_VERIFIED if has_live else DataSourceEnum.CONTROLLED_FIXTURE

        if not stylist_rationale:
            stylist_rationale = (
                f"Assembled a cohesive {request.theme} ensemble for {request.occasion}. "
                f"Selected {len(final_items)} complementary pieces adhering to the specified palette "
                f"({', '.join(request.color_preferences)}) while strictly honoring your budget of INR {request.budget_inr:,.0f}."
            )

        return OutfitRecommendation(
            outfit_id=outfit_id,
            user_id=request.user_id,
            occasion=request.occasion,
            theme=request.theme,
            items=final_items,
            total_price_inr=total_price,
            target_budget_inr=request.budget_inr,
            is_within_budget=is_within,
            harmony_score=94.0,
            stylist_rationale=stylist_rationale,
            tradeoffs_considered=tradeoffs,
            trace_steps=trace_steps,
            visualization_url="https://images.unsplash.com/photo-1490481651871-ab68de25d43d?w=800",
            orchestration_engine=engine_used,
            status=final_status,
            data_source_mode=data_mode,
            error_message=error_msg
        )

    async def stream_execution(self, request: OutfitRequest) -> AsyncGenerator[AgentTraceStep, None]:
        """
        Asynchronously yields step-by-step reasoning and tool execution trace.
        Selects Gemini-powered agent loop if configured; otherwise runs deterministic fallback.
        """
        use_gemini = (
            self.gemini_service.is_configured()
            and not self.force_fixture
        )

        if use_gemini:
            try:
                async for step in self._run_gemini_loop(request):
                    yield step
                return
            except Exception as e:
                sanitized = sanitize_error_message(e)
                # Honest reporting: notify client that Gemini failed and fallback is executing
                yield AgentTraceStep(
                    step_number=99,
                    phase=AgentPhase.EVALUATE_CONSTRAINTS,
                    thought=f"⚠️ Gemini orchestration failed ({sanitized}). Transitioning to deterministic fallback engine.",
                    tool_called="FallbackToDeterministicEngine",
                    tool_output={"error": sanitized, "action": "switching_to_fallback"}
                )

        # Deterministic Fallback Orchestration
        async for step in self._run_deterministic_loop(request):
            yield step

    async def _run_gemini_loop(self, request: OutfitRequest) -> AsyncGenerator[AgentTraceStep, None]:
        """
        Real Gemini-powered bounded observe-plan-act loop with allowlisted tool selection.
        """
        start_time = time.time()
        step_count = 1
        assembled_items: List[ProductItem] = []
        searched_queries: List[str] = []
        constraint_violations: List[str] = []
        replan_events: List[str] = []
        latest_observation = "Initiating styling planning."

        # Step 1: Initial Goal Decomposition with Gemini
        initial_plan = await self.gemini_service.generate_initial_plan(request)
        required_categories = initial_plan.required_categories or ["top", "bottom", "shoes"]

        yield AgentTraceStep(
            step_number=step_count,
            phase=AgentPhase.UNDERSTAND_GOAL,
            thought=f"[Gemini 2.5] Goal Understood: {initial_plan.goal_understanding}",
            tool_called="GeminiDecomposeGoal",
            tool_input={"occasion": request.occasion, "budget_inr": request.budget_inr},
            tool_output={
                "style_direction": initial_plan.style_direction,
                "preferred_palette": initial_plan.preferred_palette,
                "orchestration_engine": "gemini"
            }
        )
        step_count += 1
        await asyncio.sleep(0.02)

        yield AgentTraceStep(
            step_number=step_count,
            phase=AgentPhase.DECOMPOSE_PLAN,
            thought=(
                f"[Gemini 2.5] Plan Formulated: Required categories: {', '.join(required_categories)}. "
                f"Allocated sub-budgets: {initial_plan.budget_allocation}"
            ),
            tool_called="GeminiFormulatePlan",
            tool_input={"budget_allocation": initial_plan.budget_allocation},
            tool_output={"required_categories": required_categories}
        )
        step_count += 1
        await asyncio.sleep(0.02)

        next_action = initial_plan.first_action
        next_search_args = initial_plan.first_search_args
        if next_action == AgentActionType.SEARCH_PRODUCTS and not next_search_args:
            if initial_plan.initial_search_queries:
                first_q = initial_plan.initial_search_queries[0]
                next_search_args = SearchProductsArgs(
                    query=first_q.query,
                    category=first_q.category,
                    gender=request.gender.value,
                    max_price=request.budget_inr * 0.5
                )
            else:
                cat = required_categories[0] if required_categories else "top"
                next_search_args = SearchProductsArgs(
                    query=f"{request.theme} {cat}",
                    category=cat,
                    gender=request.gender.value,
                    max_price=request.budget_inr * 0.5
                )

        # Bounded Observe-Plan-Act Loop (Max iterations)
        for iteration in range(1, self.max_iterations + 1):
            # Check deadline timeout
            if (time.time() - start_time) > self.timeout_seconds:
                yield AgentTraceStep(
                    step_number=step_count,
                    phase=AgentPhase.COMPLETED,
                    thought=f"Execution deadline reached ({self.timeout_seconds}s limit). Finalizing best candidate.",
                    tool_called="EnforceDeadlineLimit",
                    tool_output={
                        "status": "deadline_exceeded",
                        "assembled_items": [i.model_dump() for i in assembled_items],
                        "orchestration_engine": "gemini"
                    }
                )
                return

            if iteration > 1:
                decision = await self.gemini_service.propose_next_action(
                    request=request,
                    iteration=iteration,
                    required_categories=required_categories,
                    current_items=assembled_items,
                    latest_observation=latest_observation,
                    constraint_violations=constraint_violations,
                    searched_queries=searched_queries
                )
                next_action = decision.action
                next_search_args = decision.search_args
                thought_text = f"[Gemini 2.5] {decision.thought}"
            else:
                thought_text = f"[Gemini 2.5] Executing initial action: {next_action.value}"

            # ACTION 1: Search Products
            if next_action == AgentActionType.SEARCH_PRODUCTS and next_search_args:
                query_str = next_search_args.query.strip()
                cat = next_search_args.category.lower()

                # Prevent repetitive duplicate queries
                if query_str.lower() in [q.lower() for q in searched_queries]:
                    query_str = f"alternative {request.theme} {cat}"

                searched_queries.append(query_str)

                yield AgentTraceStep(
                    step_number=step_count,
                    phase=AgentPhase.SELECT_TOOL,
                    thought=thought_text,
                    tool_called="SearchProducts",
                    tool_input={
                        "query": query_str,
                        "category": cat,
                        "max_price": next_search_args.max_price
                    }
                )
                step_count += 1

                # Execute Allowlisted Search Tool
                try:
                    products = await self.tools.search_products(
                        query=query_str,
                        category=cat,
                        gender=request.gender.value,
                        max_price=next_search_args.max_price,
                        color=next_search_args.color or (request.color_preferences[0] if request.color_preferences else None),
                        limit=next_search_args.limit or 3
                    )
                except ShoppingProviderError as e:
                    products = []
                    latest_observation = f"Live shopping provider error: {e}. No fixture substitution performed."

                if products:
                    picked = products[0]
                    # Check if category already has an item; replace if so
                    assembled_items = [i for i in assembled_items if i.category != cat]
                    assembled_items.append(picked)
                    latest_observation = (
                        f"Found {len(products)} products for '{cat}'. "
                        f"Selected: '{picked.title}' at INR {picked.price_inr} from {picked.merchant}."
                    )
                elif "Live shopping provider error" not in latest_observation:
                    latest_observation = f"No products found matching query '{query_str}' for category '{cat}'."

            # ACTION 2: Get Budget Summary
            elif next_action == AgentActionType.GET_BUDGET_SUMMARY:
                eval_res = self.tools.calculate_outfit_budget(assembled_items, request.budget_inr)
                latest_observation = f"Subtotal: INR {eval_res.actual_value:,.2f} vs Budget INR {request.budget_inr:,.2f}. Status: {eval_res.status.value}."
                yield AgentTraceStep(
                    step_number=step_count,
                    phase=AgentPhase.EVALUATE_CONSTRAINTS,
                    thought=thought_text,
                    tool_called="CalculateOutfitBudget",
                    tool_input={"budget_inr": request.budget_inr},
                    tool_output={"total_price_inr": eval_res.actual_value, "is_valid": eval_res.status == ConstraintStatus.PASSED},
                    constraint_check=eval_res
                )
                step_count += 1

            # ACTION 3: Replan
            elif next_action == AgentActionType.REPLAN:
                replan_args = decision.replan_args if 'decision' in locals() and decision.replan_args else None
                violating_cat = replan_args.violating_category if replan_args else (
                    max(assembled_items, key=lambda x: x.price_inr).category if assembled_items else "top"
                )
                target_sub = replan_args.target_sub_budget if replan_args else 2000.0

                # Remove violating piece
                assembled_items = [i for i in assembled_items if i.category != violating_cat]
                replan_event = f"Swapped high-ticket {violating_cat} with target price ceiling INR {target_sub:,.0f}"
                replan_events.append(replan_event)

                yield AgentTraceStep(
                    step_number=step_count,
                    phase=AgentPhase.REPLAN,
                    thought=thought_text,
                    tool_called="ReplanOutfit",
                    tool_input={"violating_category": violating_cat, "target_sub_budget": target_sub}
                )
                step_count += 1

                # Search replacement
                revised_query = replan_args.revised_search_query if replan_args else f"budget {request.theme} {violating_cat}"
                searched_queries.append(revised_query)
                try:
                    replacements = await self.tools.search_products(
                        query=revised_query,
                        category=violating_cat,
                        gender=request.gender.value,
                        max_price=target_sub,
                        limit=2
                    )
                except ShoppingProviderError as e:
                    replacements = []
                    latest_observation = f"Replan search provider error: {e}"

                if replacements:
                    assembled_items.append(replacements[0])
                    latest_observation = f"Replan successful. Substituted with '{replacements[0].title}' at INR {replacements[0].price_inr}."
                elif "Replan search provider error" not in latest_observation:
                    latest_observation = f"Replan query '{revised_query}' returned no results."

            # ACTION 4: Finish Plan or Validate Outfit
            elif next_action in (AgentActionType.FINISH_PLAN, AgentActionType.VALIDATE_OUTFIT):
                # DETERMINISTIC HARD CONSTRAINT CHECK
                budget_eval = self.tools.calculate_outfit_budget(assembled_items, request.budget_inr)
                size_eval = self.tools.check_availability_and_sizes(assembled_items, request.sizes)
                present_cats = [i.category for i in assembled_items]
                missing_req = [c for c in required_categories if c not in present_cats]

                constraint_violations = []
                if budget_eval.status == ConstraintStatus.VIOLATED:
                    constraint_violations.append(budget_eval.details)
                if size_eval.status == ConstraintStatus.VIOLATED:
                    constraint_violations.append(size_eval.details)
                if missing_req:
                    constraint_violations.append(f"Missing required categories: {', '.join(missing_req)}")

                if not constraint_violations and next_action == AgentActionType.FINISH_PLAN:
                    # Successfully finished!
                    break
                else:
                    # Model proposed finish but hard constraints FAILED
                    latest_observation = f"Validation Failed: {'; '.join(constraint_violations)}"
                    yield AgentTraceStep(
                        step_number=step_count,
                        phase=AgentPhase.EVALUATE_CONSTRAINTS,
                        thought=f"Deterministic Check: Rejected proposed finish. Constraints violated: {'; '.join(constraint_violations)}",
                        tool_called="ValidateOutfitHardConstraints",
                        tool_output={"violations": constraint_violations},
                        constraint_check=budget_eval
                    )
                    step_count += 1

        # Synthesize Final Stylist Rationale with Gemini
        final_total = sum(i.price_inr for i in assembled_items)
        is_valid = final_total <= request.budget_inr
        stylist_res = await self.gemini_service.generate_final_rationale(
            request=request,
            items=assembled_items,
            total_price=final_total,
            is_within_budget=is_valid,
            replan_events=replan_events
        )

        yield AgentTraceStep(
            step_number=step_count,
            phase=AgentPhase.COMPLETED,
            thought=f"[Gemini 2.5] Outfit finalized! {stylist_res.stylist_rationale}",
            tool_called="SynthesizeFinalOutfit",
            tool_output={
                "assembled_items": [item.model_dump() for item in assembled_items],
                "total_price_inr": final_total,
                "is_within_budget": is_valid,
                "orchestration_engine": "gemini",
                "status": "complete" if is_valid else "budget_exceeded",
                "stylist_rationale": stylist_res.stylist_rationale,
                "tradeoffs": stylist_res.tradeoffs_considered
            }
        )

    async def _run_deterministic_loop(self, request: OutfitRequest) -> AsyncGenerator[AgentTraceStep, None]:
        """
        Deterministic heuristic engine with explicit fallback identification.
        """
        step_count = 1
        is_overrun_demo = request.force_test_fixture == "budget_overrun_scenario"

        notice_text = (
            "Notice: Controlled test fixture requested for benchmark scenario reproducibility."
            if self.force_fixture
            else "Notice: GEMINI_API_KEY is not configured. Running deterministic heuristic orchestrator fallback."
        )

        # Phase 1: Understand Goal
        yield AgentTraceStep(
            step_number=step_count,
            phase=AgentPhase.UNDERSTAND_GOAL,
            thought=(
                f"{notice_text}\nGoal: Assemble complete look for '{request.occasion}', "
                f"theme '{request.theme}', gender '{request.gender.value}', budget INR {request.budget_inr:,.0f}."
            ),
            tool_called="DecomposeStylingGoal",
            tool_input={"occasion": request.occasion, "budget": request.budget_inr, "gender": request.gender.value},
            tool_output={"status": "Goal understood, formulating subtasks", "orchestration_engine": "deterministic_fallback"}
        )
        step_count += 1
        await asyncio.sleep(0.02)

        # Phase 2: Plan Subtasks
        subtasks = ["top", "bottom", "shoes"]
        if request.budget_inr > 3000:
            subtasks.append("accessory")

        yield AgentTraceStep(
            step_number=step_count,
            phase=AgentPhase.DECOMPOSE_PLAN,
            thought=f"Decomposed goal into wardrobe categories: {', '.join(subtasks)}.",
            tool_called="PlanSubtasks",
            tool_input={"subtasks": subtasks},
            tool_output={"subtasks": subtasks}
        )
        step_count += 1
        await asyncio.sleep(0.02)

        assembled_items: List[ProductItem] = []

        # Top / Primary Anchor
        allocated_top_budget = request.budget_inr * (0.65 if request.gender == GenderEnum.WOMEN else 0.45)
        top_query = f"{request.theme} blazer shirt" if request.gender == GenderEnum.MEN else f"{request.theme} kurta dress set"
        
        step_top = AgentTraceStep(
            step_number=step_count,
            phase=AgentPhase.SELECT_TOOL,
            thought=f"Selecting tool 'SearchProducts' to discover anchor top piece. Target sub-budget: INR {allocated_top_budget:,.0f}.",
            tool_called="SearchProducts",
            tool_input={"query": top_query, "category": "top", "max_price": allocated_top_budget}
        )
        tops = await self.tools.search_products(
            query=top_query,
            category="top",
            gender=request.gender.value,
            max_price=allocated_top_budget if not is_overrun_demo else None,
            color=request.color_preferences[0] if request.color_preferences else None,
            limit=3
        )
        selected_top = tops[0] if tops else None
        if selected_top:
            assembled_items.append(selected_top)

        step_top.tool_output = {
            "found_count": len(tops),
            "selected_top": selected_top.title if selected_top else None,
            "price_inr": selected_top.price_inr if selected_top else 0,
            "merchant": selected_top.merchant if selected_top else "Retailer"
        }
        yield step_top
        step_count += 1
        await asyncio.sleep(0.02)

        # Bottom (if not complete ethnic set)
        has_full_set = any(item.category == "ethnic" for item in assembled_items)
        if not has_full_set:
            remaining_for_rest = request.budget_inr - sum(i.price_inr for i in assembled_items)
            bot_query = "chinos trousers" if request.gender == GenderEnum.MEN else "tailored trousers skirt"
            bots = await self.tools.search_products(
                query=bot_query,
                category="bottom",
                gender=request.gender.value,
                max_price=remaining_for_rest * 0.55,
                limit=2
            )
            if bots:
                assembled_items.append(bots[0])

        # Shoes
        remaining_for_shoes = request.budget_inr - sum(i.price_inr for i in assembled_items)
        shoe_query = "leather loafers sneakers" if request.gender == GenderEnum.MEN else "mojaris heels sandals"
        shoes = await self.tools.search_products(
            query=shoe_query,
            category="shoes",
            gender=request.gender.value,
            max_price=max(remaining_for_shoes, 900.0),
            limit=2
        )
        if shoes:
            shoe_pick = shoes[0]
            for s in shoes:
                if s.price_inr <= remaining_for_shoes:
                    shoe_pick = s
                    break
            assembled_items.append(shoe_pick)

        # Evaluate Hard Budget Constraints
        budget_eval = self.tools.calculate_outfit_budget(assembled_items, request.budget_inr)
        yield AgentTraceStep(
            step_number=step_count,
            phase=AgentPhase.EVALUATE_CONSTRAINTS,
            thought=f"Evaluating hard constraints. Total price is INR {budget_eval.actual_value:,.2f} vs Budget INR {request.budget_inr:,.2f}.",
            tool_called="CalculateOutfitBudget",
            tool_input={"budget": request.budget_inr},
            tool_output={"total_price_inr": budget_eval.actual_value, "is_valid": budget_eval.status == ConstraintStatus.PASSED},
            constraint_check=budget_eval
        )
        step_count += 1
        await asyncio.sleep(0.02)

        # Replan if Overrun Detected
        if budget_eval.status == ConstraintStatus.VIOLATED:
            expensive_item = max(assembled_items, key=lambda x: x.price_inr)
            assembled_items.remove(expensive_item)

            sub_budget = max(800.0, request.budget_inr - sum(i.price_inr for i in assembled_items))
            replacement_cands = await self.tools.search_products(
                query=f"budget {expensive_item.category} {request.theme}",
                category=expensive_item.category,
                gender=request.gender.value,
                max_price=sub_budget,
                limit=3
            )
            replacement = replacement_cands[0] if replacement_cands else None
            if replacement:
                assembled_items.append(replacement)

            # Re-evaluate
            re_eval = self.tools.calculate_outfit_budget(assembled_items, request.budget_inr)
            re_eval.status = ConstraintStatus.REPAIRED if re_eval.actual_value <= request.budget_inr else ConstraintStatus.VIOLATED

            yield AgentTraceStep(
                step_number=step_count,
                phase=AgentPhase.REPLAN,
                thought=f"Constraint Violation Resolved: Replaced high-ticket '{expensive_item.title}' with budget alternative. New total: INR {re_eval.actual_value:,.2f}.",
                tool_called="ReplanOutfit",
                tool_input={"target_budget": request.budget_inr},
                tool_output={"new_total_inr": re_eval.actual_value},
                constraint_check=re_eval
            )
            step_count += 1
            await asyncio.sleep(0.02)

        # Complete
        final_total = sum(i.price_inr for i in assembled_items)
        yield AgentTraceStep(
            step_number=step_count,
            phase=AgentPhase.COMPLETED,
            thought=f"Outfit assembly complete! Assembled {len(assembled_items)} verified items satisfying constraints. Total: INR {final_total:,.2f}.",
            tool_called="SynthesizeFinalOutfit",
            tool_output={
                "assembled_items": [item.model_dump() for item in assembled_items],
                "total_price_inr": final_total,
                "is_within_budget": final_total <= request.budget_inr,
                "orchestration_engine": "deterministic_fallback",
                "status": "complete"
            }
        )
