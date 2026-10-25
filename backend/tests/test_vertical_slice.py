import sys
from pathlib import Path
# Ensure backend directory is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import asyncio
import pytest
from app.models.schemas import (
    OutfitRequest,
    GenderEnum,
    ConstraintStatus,
    BlendCreateRequest,
    BlendJoinRequest
)
from app.services.shopping import get_shopping_provider
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.blend.coordinator import blend_coordinator

@pytest.mark.asyncio
async def test_shopping_provider_contract():
    """Verify that the shopping provider returns valid items conforming to schema."""
    provider = get_shopping_provider(force_mode="fixture")
    items = await provider.search_products(
        query="navy blazer",
        category="top",
        gender="men",
        limit=3
    )

    assert len(items) > 0
    first = items[0]
    assert first.price_inr > 0
    assert first.merchant in ["Myntra", "Ajio", "Amazon India", "Flipkart", "Zara India"]
    assert first.image_url.startswith("http")
    assert first.product_url.startswith("http")
    print(f"[PASSED] Provider verified: Found '{first.title}' at INR {first.price_inr} from {first.merchant}")

@pytest.mark.asyncio
async def test_scenario_1_standard_outfit_assembly():
    """Scenario 1: Agent creates a complete themed outfit under a specified budget."""
    orchestrator = AgentOrchestrator(force_fixture="fixture")
    request = OutfitRequest(
        occasion="Tech Conference Keynote",
        theme="Minimalist Smart Casual",
        gender=GenderEnum.MEN,
        budget_inr=6000.0,
        color_preferences=["Navy", "Beige"]
    )

    result = await orchestrator.run(request)
    assert len(result.items) >= 2
    assert result.is_within_budget is True
    assert result.total_price_inr <= 6000.0
    assert len(result.trace_steps) >= 4
    print(f"[PASSED] Scenario 1: Outfit total INR {result.total_price_inr} within INR 6,000 budget.")

@pytest.mark.asyncio
async def test_scenario_2_budget_overrun_detection_and_replanning():
    """Scenario 2: Agent detects selected combination exceeds budget and autonomously replans."""
    orchestrator = AgentOrchestrator(force_fixture="fixture")
    request = OutfitRequest(
        occasion="College Farewell",
        theme="Smart Casual",
        gender=GenderEnum.MEN,
        budget_inr=5000.0,
        force_test_fixture="budget_overrun_scenario" # Triggers initial overshoot
    )

    result = await orchestrator.run(request)

    # Check trace steps for violation and repair
    trace_phases = [step.phase for step in result.trace_steps]
    assert "REPLAN" in trace_phases, "Agent must trigger REPLAN phase upon constraint violation"

    replan_steps = [s for s in result.trace_steps if s.phase == "REPLAN"]
    assert len(replan_steps) > 0
    replan_step = replan_steps[0]
    assert replan_step.constraint_check.status == ConstraintStatus.REPAIRED
    assert result.is_within_budget is True
    assert result.total_price_inr <= 5000.0
    print(f"[PASSED] Scenario 2: Detected budget overrun, executed ReplanOutfit, repaired to INR {result.total_price_inr:,.2f}.")

@pytest.mark.asyncio
async def test_scenario_5_blend_group_coordination():
    """Scenario 5: Multi-user Blend coordination with differing personal budgets and styles."""
    # 1. Host creates room
    create_req = BlendCreateRequest(
        title="College Farewell 2026",
        occasion="Graduation Gala",
        shared_theme="Royal Retro",
        shared_palette=["Navy", "Champagne Gold"],
        host_name="Arjun",
        host_budget_inr=6000.0,
        host_style="Tailored sharp formal"
    )
    session = blend_coordinator.create_session(create_req)
    assert session.blend_id.startswith("blend_")
    assert len(session.members) == 1

    # 2. Friend joins
    join_req = BlendJoinRequest(
        blend_id=session.blend_id,
        member_name="Sneha",
        member_budget_inr=3500.0,
        member_style="Indo-Western fusion",
        member_gender=GenderEnum.WOMEN
    )
    joined_session = blend_coordinator.join_session(join_req)
    assert len(joined_session.members) == 2

    # 3. Trigger autonomous group coordination
    coordinated = await blend_coordinator.coordinate_outfits(session.blend_id, force_fixture="fixture")
    assert coordinated.group_cohesion_score >= 85.0

    m1_outfit = coordinated.members[0].recommended_outfit
    m2_outfit = coordinated.members[1].recommended_outfit

    assert m1_outfit is not None
    assert m2_outfit is not None
    assert m1_outfit.total_price_inr <= 6000.0
    assert m2_outfit.total_price_inr <= 3500.0
    print(f"[PASSED] Scenario 5: Harmonized Blend room '{session.title}'. Member 1: INR {m1_outfit.total_price_inr}, Member 2: INR {m2_outfit.total_price_inr}.")

if __name__ == "__main__":
    asyncio.run(test_shopping_provider_contract())
    asyncio.run(test_scenario_1_standard_outfit_assembly())
    asyncio.run(test_scenario_2_budget_overrun_detection_and_replanning())
    asyncio.run(test_scenario_5_blend_group_coordination())
    print("\n[SUCCESS] ALL VERTICAL SLICE SCENARIOS VERIFIED SUCCESSFULLY!")
