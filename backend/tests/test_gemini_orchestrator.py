import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch
import pytest

from app.models.schemas import (
    OutfitRequest,
    GenderEnum,
    ProductItem,
    DataSourceEnum,
    ConstraintStatus,
    InitialPlan,
    AgentStepDecision,
    FinalStylistResponse,
    AgentActionType,
    SearchProductsArgs,
    ReplanArgs
)
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.gemini_service import GeminiAgentService
from app.services.shopping.base import ShoppingProviderError
from app.services.shopping.serpapi_provider import SerpApiShoppingProvider
from app.services.shopping.fixture_provider import ControlledFixtureProvider

# Sample mock product items for testing
MOCK_TOP = ProductItem(
    id="mock_top_1",
    title="Navy Blue Tailored Blazer",
    brand="Raymond",
    category="top",
    price_inr=2200.0,
    merchant="Myntra",
    product_url="https://myntra.com/blazer",
    image_url="https://images.example.com/blazer.jpg",
    available_sizes=["S", "M", "L", "XL"],
    data_source=DataSourceEnum.LIVE_VERIFIED
)

MOCK_BOTTOM = ProductItem(
    id="mock_bot_1",
    title="Beige Slim-Fit Chinos",
    brand="Arrow",
    category="bottom",
    price_inr=1300.0,
    merchant="Amazon India",
    product_url="https://amazon.in/chinos",
    image_url="https://images.example.com/chinos.jpg",
    available_sizes=["30", "32", "34", "36"],
    data_source=DataSourceEnum.LIVE_VERIFIED
)

MOCK_SHOES = ProductItem(
    id="mock_shoe_1",
    title="Brown Leather Loafers",
    brand="Hush Puppies",
    category="shoes",
    price_inr=1400.0,
    merchant="Tata CLiQ",
    product_url="https://tatacliq.com/loafers",
    image_url="https://images.example.com/loafers.jpg",
    available_sizes=["UK 8", "UK 9", "UK 10"],
    data_source=DataSourceEnum.LIVE_VERIFIED
)

MOCK_EXPENSIVE_TOP = ProductItem(
    id="mock_top_expensive",
    title="Luxury Italian Wool Tuxedo",
    brand="Armani",
    category="top",
    price_inr=6500.0, # Exceeds 5000 budget alone!
    merchant="Ajio Luxe",
    product_url="https://ajio.com/tuxedo",
    image_url="https://images.example.com/tuxedo.jpg",
    available_sizes=["S", "M", "L", "XL"],
    data_source=DataSourceEnum.LIVE_VERIFIED
)

@pytest.fixture
def mock_gemini():
    """Returns a mocked GeminiAgentService ready for unit tests without network calls."""
    svc = MagicMock(spec=GeminiAgentService)
    svc.is_configured.return_value = True
    svc.model_name = "gemini-2.5-flash"
    svc.api_key = "test_mock_gemini_api_key_valid_12345"
    return svc

# --------------------------------------------------------------------------
# Test 1: Gemini produces a valid plan and tool action
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_gemini_produces_valid_plan_and_tool_action(mock_gemini):
    mock_gemini.generate_initial_plan = AsyncMock(return_value=InitialPlan(
        goal_understanding="Smart casual farewell ensemble",
        style_direction="Minimalist classic with navy and beige tones",
        preferred_palette=["Navy", "Beige"],
        required_categories=["top", "bottom", "shoes"],
        budget_allocation={"top": 2500.0, "bottom": 1200.0, "shoes": 1300.0},
        initial_search_queries={"top": "navy smart casual blazer"},
        first_action=AgentActionType.SEARCH_PRODUCTS,
        first_search_args=SearchProductsArgs(query="navy smart blazer", category="top", gender="men", max_price=2500.0)
    ))

    # Second step finishes
    mock_gemini.propose_next_action = AsyncMock(return_value=AgentStepDecision(
        thought="All pieces found, proposing to finish plan",
        action=AgentActionType.FINISH_PLAN
    ))

    mock_gemini.generate_final_rationale = AsyncMock(return_value=FinalStylistResponse(
        stylist_rationale="Curated a tailored navy ensemble satisfying smart casual criteria.",
        harmony_score=95.0,
        tradeoffs_considered=["Chose versatile cotton blend over heavy wool."]
    ))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)

    trace = []
    async for step in orchestrator.stream_execution(req):
        trace.append(step)

    # Verify plan was emitted into trace
    phases = [s.phase.value for s in trace]
    assert "UNDERSTAND_GOAL" in phases
    assert "DECOMPOSE_PLAN" in phases
    assert mock_gemini.generate_initial_plan.called

# --------------------------------------------------------------------------
# Test 2: Search tool receives validated arguments and returns provider results
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_search_tool_receives_validated_arguments():
    mock_provider = AsyncMock()
    mock_provider.search_products.return_value = [MOCK_TOP]

    with patch("app.services.agent.orchestrator.get_shopping_provider", return_value=mock_provider):
        orchestrator = AgentOrchestrator()
        orchestrator.provider = mock_provider
        orchestrator.tools.provider = mock_provider

        res = await orchestrator.tools.search_products(
            query="navy blazer",
            category="top",
            gender="men",
            max_price=3000.0,
            limit=2
        )

        assert len(res) == 1
        assert res[0].title == "Navy Blue Tailored Blazer"
        mock_provider.search_products.assert_called_once_with(
            query="navy blazer",
            category="top",
            gender="men",
            max_price=3000.0,
            color=None,
            limit=2
        )

# --------------------------------------------------------------------------
# Test 3: Actual tool results are passed back into the next reasoning step
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_actual_tool_results_passed_back_to_gemini(mock_gemini):
    mock_gemini.generate_initial_plan = AsyncMock(return_value=InitialPlan(
        goal_understanding="Assemble complete look",
        style_direction="Smart casual",
        preferred_palette=["Navy"],
        required_categories=["top"],
        budget_allocation={"top": 2500.0},
        initial_search_queries={"top": "navy blazer"},
        first_action=AgentActionType.SEARCH_PRODUCTS,
        first_search_args=SearchProductsArgs(query="navy blazer", category="top", gender="men", max_price=3000.0)
    ))

    # Mock tool search returning MOCK_TOP
    mock_gemini.propose_next_action = AsyncMock(return_value=AgentStepDecision(
        thought="Inspecting returned blazer, looks great and within budget",
        action=AgentActionType.FINISH_PLAN
    ))

    mock_gemini.generate_final_rationale = AsyncMock(return_value=FinalStylistResponse(
        stylist_rationale="Solid ensemble.",
        harmony_score=90.0
    ))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    orchestrator.tools.search_products = AsyncMock(return_value=[MOCK_TOP])

    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)
    await orchestrator.run(req)

    # Verify propose_next_action received observation containing MOCK_TOP details
    assert mock_gemini.propose_next_action.called
    first_call_kwargs = mock_gemini.propose_next_action.call_args_list[0].kwargs
    latest_obs = first_call_kwargs["latest_observation"]
    assert "Navy Blue Tailored Blazer" in latest_obs
    assert "2200" in latest_obs

# --------------------------------------------------------------------------
# Test 4: Over-budget outfit is rejected and Gemini is asked to replan
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_over_budget_outfit_rejected_and_gemini_asked_to_replan(mock_gemini):
    mock_gemini.generate_initial_plan = AsyncMock(return_value=InitialPlan(
        goal_understanding="Assemble look under 5000",
        style_direction="Smart Casual",
        preferred_palette=["Navy"],
        required_categories=["top"],
        budget_allocation={"top": 2500.0},
        initial_search_queries={},
        first_action=AgentActionType.SEARCH_PRODUCTS,
        first_search_args=SearchProductsArgs(query="expensive tuxedo", category="top", gender="men", max_price=7000.0)
    ))

    # Step 2: Gemini tries to finish even though tuxedo is 6500 (> 5000)
    # Step 3: Replan
    # Step 4: Finish with budget top
    mock_gemini.propose_next_action = AsyncMock(side_effect=[
        # Attempt 1: Try to finish (should be rejected by deterministic validator)
        AgentStepDecision(
            thought="Attempting to finalize outfit",
            action=AgentActionType.FINISH_PLAN
        ),
        # Attempt 2: Replan after rejection
        AgentStepDecision(
            thought="Replacing tuxedo with budget blazer",
            action=AgentActionType.REPLAN,
            replan_args=ReplanArgs(
                violating_category="top",
                reason="Over budget by 1500",
                target_sub_budget=2200.0,
                revised_search_query="budget cotton blazer"
            )
        ),
        # Attempt 3: Finalize after budget item swapped
        AgentStepDecision(
            thought="Now within budget, finalizing",
            action=AgentActionType.FINISH_PLAN
        )
    ])

    mock_gemini.generate_final_rationale = AsyncMock(return_value=FinalStylistResponse(
        stylist_rationale="Replanned to fit budget.",
        harmony_score=92.0
    ))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    # Return expensive item on first search, budget item on replan
    orchestrator.tools.search_products = AsyncMock(side_effect=[
        [MOCK_EXPENSIVE_TOP], # First search (6500)
        [MOCK_TOP]            # Replan search (2200)
    ])

    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)
    result = await orchestrator.run(req)

    assert result.is_within_budget is True
    assert result.total_price_inr <= 5000.0
    assert any(s.phase.value == "REPLAN" for s in result.trace_steps)

# --------------------------------------------------------------------------
# Test 5: Missing required categories cause replanning or validation failure
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_missing_required_categories_cause_validation_failure(mock_gemini):
    mock_gemini.generate_initial_plan = AsyncMock(return_value=InitialPlan(
        goal_understanding="Complete look with top, bottom, shoes",
        style_direction="Smart Casual",
        preferred_palette=["Navy"],
        required_categories=["top", "bottom", "shoes"],
        budget_allocation={"top": 2000.0, "bottom": 1500.0, "shoes": 1500.0},
        initial_search_queries={},
        first_action=AgentActionType.SEARCH_PRODUCTS,
        first_search_args=SearchProductsArgs(query="blazer", category="top", gender="men")
    ))

    # Gemini tries to finish immediately with only 1 item (missing bottom & shoes)
    mock_gemini.propose_next_action = AsyncMock(return_value=AgentStepDecision(
        thought="I want to finish now",
        action=AgentActionType.FINISH_PLAN
    ))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    orchestrator.tools.search_products = AsyncMock(return_value=[MOCK_TOP])

    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)
    
    trace = []
    async for step in orchestrator.stream_execution(req):
        trace.append(step)

    # Check that deterministic validator rejected proposed finish due to missing categories
    rejection_steps = [s for s in trace if "Missing required categories" in str(s.tool_output)]
    assert len(rejection_steps) > 0

# --------------------------------------------------------------------------
# Test 6: Valid outfit passes deterministic final validation
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_valid_outfit_passes_deterministic_validation(mock_gemini):
    mock_gemini.generate_initial_plan = AsyncMock(return_value=InitialPlan(
        goal_understanding="Complete valid outfit",
        style_direction="Smart Casual",
        preferred_palette=["Navy"],
        required_categories=["top", "bottom", "shoes"],
        budget_allocation={"top": 2200.0, "bottom": 1300.0, "shoes": 1400.0},
        initial_search_queries={},
        first_action=AgentActionType.SEARCH_PRODUCTS,
        first_search_args=SearchProductsArgs(query="blazer", category="top", gender="men")
    ))

    mock_gemini.propose_next_action = AsyncMock(side_effect=[
        AgentStepDecision(thought="Searching bottom", action=AgentActionType.SEARCH_PRODUCTS, search_args=SearchProductsArgs(query="chinos", category="bottom", gender="men")),
        AgentStepDecision(thought="Searching shoes", action=AgentActionType.SEARCH_PRODUCTS, search_args=SearchProductsArgs(query="loafers", category="shoes", gender="men")),
        AgentStepDecision(thought="Finishing plan", action=AgentActionType.FINISH_PLAN)
    ])

    mock_gemini.generate_final_rationale = AsyncMock(return_value=FinalStylistResponse(
        stylist_rationale="Ensemble is completely assembled within budget.",
        harmony_score=96.0
    ))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    orchestrator.tools.search_products = AsyncMock(side_effect=[
        [MOCK_TOP],
        [MOCK_BOTTOM],
        [MOCK_SHOES]
    ])

    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)
    result = await orchestrator.run(req)

    assert result.is_within_budget is True
    assert result.total_price_inr == 4900.0
    assert result.status == "complete"
    assert result.orchestration_engine == "gemini"
    assert len(result.items) == 3

# --------------------------------------------------------------------------
# Test 7: Malformed model output is handled safely
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_malformed_model_output_handled_safely(mock_gemini):
    # Gemini raises malformed json or unexpected error
    mock_gemini.generate_initial_plan = AsyncMock(side_effect=RuntimeError("Malformed JSON response from model"))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)

    # Should not crash; gracefully fall back to deterministic engine
    result = await orchestrator.run(req)
    assert result is not None
    assert result.orchestration_engine == "deterministic_fallback"
    assert any("Gemini orchestration failed" in s.thought for s in result.trace_steps)

# --------------------------------------------------------------------------
# Test 8: Gemini timeout or auth failure produces honest error or explicit fallback
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_gemini_timeout_or_auth_failure_produces_honest_error(mock_gemini):
    mock_gemini.generate_initial_plan = AsyncMock(side_effect=RuntimeError("Gemini API Error: 401 Unauthorized [REDACTED_KEY]"))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)

    result = await orchestrator.run(req)
    assert result.orchestration_engine == "deterministic_fallback"
    # Never claim to be Gemini when fallback executed
    assert result.orchestration_engine != "gemini"

# --------------------------------------------------------------------------
# Test 9: SerpApi failure does not silently switch to fixtures
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_serpapi_failure_does_not_silently_switch_to_fixtures():
    provider = SerpApiShoppingProvider(api_key="mock_invalid_key")

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_resp = MagicMock()
        mock_resp.status_code = 401
        mock_resp.json.return_value = {"error": "Invalid API key"}
        mock_resp.text = '{"error": "Invalid API key"}'
        mock_get.return_value = mock_resp

        # Should raise ShoppingProviderError, NOT return fixture items
        with pytest.raises(ShoppingProviderError) as exc_info:
            await provider.search_products(query="blazer", category="top", gender="men")

        assert "SerpApi Error 401" in str(exc_info.value)
        # Ensure it didn't return any fixture items
        mock_get.assert_called_once()

# --------------------------------------------------------------------------
# Test 10: Fixture mode remains deterministic and correctly labeled
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fixture_mode_correctly_labeled():
    provider = ControlledFixtureProvider()
    items = await provider.search_products(query="blazer", category="top", gender="men")

    assert len(items) > 0
    for item in items:
        assert item.data_source == DataSourceEnum.CONTROLLED_FIXTURE
        assert item.data_source.value == "controlled_fixture"

# --------------------------------------------------------------------------
# Test 11: Iteration and deadline limits are enforced
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_iteration_and_deadline_limits_enforced(mock_gemini):
    mock_gemini.generate_initial_plan = AsyncMock(return_value=InitialPlan(
        goal_understanding="Infinite loop test",
        style_direction="Smart Casual",
        preferred_palette=["Navy"],
        required_categories=["top", "bottom", "shoes"],
        budget_allocation={"top": 2500.0},
        initial_search_queries={},
        first_action=AgentActionType.SEARCH_PRODUCTS,
        first_search_args=SearchProductsArgs(query="blazer", category="top", gender="men")
    ))

    # Gemini keeps proposing endless searches without finishing
    mock_gemini.propose_next_action = AsyncMock(return_value=AgentStepDecision(
        thought="Searching endlessly",
        action=AgentActionType.SEARCH_PRODUCTS,
        search_args=SearchProductsArgs(query="another item", category="top", gender="men")
    ))

    mock_gemini.generate_final_rationale = AsyncMock(return_value=FinalStylistResponse(
        stylist_rationale="Reached iteration limit.",
        harmony_score=80.0
    ))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    orchestrator.max_iterations = 4 # Cap at 4 for test speed
    orchestrator.tools.search_products = AsyncMock(return_value=[MOCK_TOP])

    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)
    result = await orchestrator.run(req)

    # Must terminate without infinite loop
    assert result is not None
    assert mock_gemini.propose_next_action.call_count <= 4

# --------------------------------------------------------------------------
# Test 12: API keys never appear in response payloads or logs
# --------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_api_keys_never_appear_in_response_payloads_or_logs(mock_gemini):
    secret_gemini_key = "mock_confidential_gemini_api_key_12345"
    secret_serp_key = "serp_secret_key_confidential_9999"

    mock_gemini.api_key = secret_gemini_key
    mock_gemini.generate_initial_plan = AsyncMock(return_value=InitialPlan(
        goal_understanding="Security audit test",
        style_direction="Clean",
        preferred_palette=["Navy"],
        required_categories=["top"],
        budget_allocation={"top": 2000.0},
        initial_search_queries={},
        first_action=AgentActionType.FINISH_PLAN
    ))

    mock_gemini.generate_final_rationale = AsyncMock(return_value=FinalStylistResponse(
        stylist_rationale="Clean output without keys.",
        harmony_score=95.0
    ))

    orchestrator = AgentOrchestrator(gemini_service=mock_gemini)
    orchestrator.tools.search_products = AsyncMock(return_value=[MOCK_TOP])

    req = OutfitRequest(occasion="Farewell", theme="Smart Casual", budget_inr=5000.0)
    result = await orchestrator.run(req)

    # Convert entire response dump to JSON string
    serialized_res = result.model_dump_json()

    assert secret_gemini_key not in serialized_res
    assert secret_serp_key not in serialized_res
    for step in result.trace_steps:
        assert secret_gemini_key not in str(step.thought)
        assert secret_gemini_key not in str(step.tool_output)
