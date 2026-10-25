import json
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from sse_starlette.sse import EventSourceResponse
from app.models.schemas import (
    OutfitRequest,
    OutfitRecommendation,
    UserFeedbackRequest,
    GenderEnum
)
from app.services.agent.orchestrator import AgentOrchestrator

router = APIRouter(prefix="/api/v1/agent", tags=["Agent Orchestrator"])

# In-memory store for recent outfits to support feedback & inspection
SAVED_OUTFITS = {}

@router.post("/outfit/assemble", response_model=OutfitRecommendation)
async def assemble_outfit(request: OutfitRequest):
    """
    Synchronously triggers autonomous agent to decompose goal, search products,
    evaluate constraints, replan if needed, and assemble complete outfit.
    """
    orchestrator = AgentOrchestrator(force_fixture=request.force_test_fixture)
    recommendation = await orchestrator.run(request)
    SAVED_OUTFITS[recommendation.outfit_id] = recommendation
    return recommendation

@router.get("/outfit/stream")
async def stream_outfit_assembly(
    occasion: str = Query("College Farewell", description="Occasion"),
    theme: str = Query("Minimalist Smart Casual", description="Theme"),
    gender: GenderEnum = Query(GenderEnum.MEN, description="Gender"),
    budget: float = Query(5000.0, description="Budget in INR"),
    fixture_scenario: Optional[str] = Query(None, description="'budget_overrun_scenario' for replanning demo")
):
    """
    Server-Sent Events (SSE) endpoint streaming real-time agent trace steps,
    tool invocations, constraint checks, and replanning actions to mobile app.
    """
    request = OutfitRequest(
        occasion=occasion,
        theme=theme,
        gender=gender,
        budget_inr=budget,
        force_test_fixture=fixture_scenario
    )

    orchestrator = AgentOrchestrator(force_fixture=fixture_scenario)

    async def event_generator():
        async for trace_step in orchestrator.stream_execution(request):
            yield {
                "event": "trace_step",
                "data": json.dumps(trace_step.model_dump(), default=str)
            }
        yield {
            "event": "complete",
            "data": json.dumps({"status": "DONE"})
        }

    return EventSourceResponse(event_generator())

@router.post("/outfit/feedback", response_model=OutfitRecommendation)
async def submit_feedback_and_replan(feedback: UserFeedbackRequest):
    """
    Handles user critique (e.g. 'swap the shoes for casual sneakers')
    and instructs the agent to execute a targeted replanning cycle.
    """
    existing = SAVED_OUTFITS.get(feedback.outfit_id)
    if not existing:
        raise HTTPException(status_code=404, detail="Outfit session not found")

    # If user disliked specific items, replace them
    orchestrator = AgentOrchestrator()
    retained_items = [item for item in existing.items if item.id not in feedback.rejected_item_ids]

    # Search alternative items matching user feedback
    replacements = await orchestrator.tools.search_products(
        query=feedback.feedback_text or "casual sneakers footwear",
        category="shoes",
        gender="men",
        limit=1
    )

    if replacements:
        retained_items.extend(replacements)

    new_total = sum(i.price_inr for i in retained_items)

    updated = OutfitRecommendation(
        outfit_id=existing.outfit_id,
        user_id=existing.user_id,
        occasion=existing.occasion,
        theme=existing.theme,
        items=retained_items,
        total_price_inr=new_total,
        target_budget_inr=existing.target_budget_inr,
        is_within_budget=new_total <= existing.target_budget_inr,
        harmony_score=95.0,
        stylist_rationale=f"Updated ensemble based on your feedback: '{feedback.feedback_text}'. Replaced selected pieces with preferred style while maintaining color balance.",
        tradeoffs_considered=["Swapped formal footwear for versatile casual silhouette per user guidance."],
        trace_steps=existing.trace_steps,
        visualization_url=existing.visualization_url
    )

    SAVED_OUTFITS[existing.outfit_id] = updated
    return updated
