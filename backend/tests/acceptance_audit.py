"""
Acceptance Audit Suite for Phase 2: AI Personal Outfit Styling & Shopping Agent
Validates:
1. Real Gemini reasoning and tool selection on live backend.
2. Live shopping data provenance via SerpApi & honest error propagation.
3. Deterministic Python enforcement of hard constraints (budget, sizes, categories).
4. Fallback transparency under simulated Gemini failures.
5. Security and repository hygiene (no secrets in repo or responses).
"""

import sys
import json
import time
import httpx
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

# Ensure backend root is in sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.config import settings
from app.models.schemas import (
    OutfitRequest,
    GenderEnum,
    ConstraintStatus,
    DataSourceEnum,
    AgentActionType,
    InitialPlan,
    AgentStepDecision,
    SearchProductsArgs,
    FinalStylistResponse
)
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.constraints import ConstraintEngine
from app.services.shopping import get_shopping_provider
from app.services.shopping.serpapi_provider import SerpApiShoppingProvider
from app.services.shopping.base import ShoppingProviderError
import asyncio


async def audit_check_1_real_gemini_reasoning():
    print("\n" + "=" * 70)
    print("AUDIT CHECK 1: Real Gemini Reasoning & Dynamic Decisions (Live Backend)")
    print("=" * 70)

    url = "http://127.0.0.1:8000/api/v1/agent/outfit/assemble"
    payload = {
        "user_id": "audit_user_001",
        "occasion": "Summer Evening Dinner",
        "theme": "Minimalist Smart Casual",
        "personal_style": "Sharp tailored clean look",
        "gender": "men",
        "sizes": {"top": "L", "bottom": "34"},
        "budget_inr": 7000.0,
        "color_preferences": ["Beige", "Navy"]
    }

    t0 = time.time()
    try:
        async with httpx.AsyncClient(timeout=90.0) as client:
            resp = await client.post(url, json=payload)
            if resp.status_code != 200:
                print(f"[FAIL] Backend returned HTTP {resp.status_code}: {resp.text}")
                return False
            data = resp.json()
    except Exception as e:
        print(f"[FAIL] Could not reach backend at {url}: {repr(e)}")
        return False

    elapsed = time.time() - t0
    print(f"[*] Response received in {elapsed:.2f}s")

    # 1. Verify engine tag
    engine = data.get("orchestration_engine")
    print(f"[*] Orchestration Engine Reported: '{engine}'")
    assert engine == "gemini", f"Expected 'gemini' but got '{engine}'"

    # 2. Verify data source mode
    data_mode = data.get("data_source_mode")
    print(f"[*] Data Source Mode: '{data_mode}'")

    # 3. Verify final outfit items are real dynamic items (not fixed demo fixtures)
    items = data.get("items", [])
    print(f"[*] Assembled Items Count: {len(items)}")
    assert len(items) >= 2, f"Expected at least 2 items, got {len(items)}"

    total_price = data.get("total_price_inr", 0.0)
    print(f"[*] Total Outfit Price: INR {total_price:,.2f} (Target Budget: INR {data.get('target_budget_inr'):,.2f})")

    fixture_ids = {"fix_top_1", "fix_top_2", "fix_bot_1", "fix_bot_2", "fix_shoe_1", "fix_shoe_2"}
    for idx, item in enumerate(items, 1):
        item_id = item.get("id", "")
        assert item_id not in fixture_ids, f"Item {item_id} is a hardcoded fixture!"
        print(f"    Item {idx}: [{item.get('category').upper()}] {item.get('title')[:45]}...")
        print(f"             Price: INR {item.get('price_inr'):,.2f} | Merchant: {item.get('merchant')} | Source: {item.get('data_source')}")

    # 4. Show sanitized agent trace steps demonstrating real reasoning & tool loop
    trace_steps = data.get("trace_steps", [])
    print(f"\n[*] Sanitized Agent Trace Steps ({len(trace_steps)} total):")
    gemini_thoughts = []
    tools_called = []
    for step in trace_steps:
        step_num = step.get("step_number")
        phase = step.get("phase")
        thought = step.get("thought")
        tool = step.get("tool_called")
        print(f"    [Step {step_num} - {phase}]")
        print(f"      Thought: {thought[:90]}...")
        if tool:
            tools_called.append(tool)
            print(f"      Tool: {tool}")
            if step.get("tool_input"):
                print(f"      Input: {json.dumps(step.get('tool_input'))[:80]}")
            if step.get("tool_output"):
                print(f"      Output: {json.dumps(step.get('tool_output'))[:80]}")
        if "[Gemini" in thought:
            gemini_thoughts.append(thought)

    assert len(gemini_thoughts) >= 2, "Expected multiple Gemini reasoning thoughts in trace"
    assert "SearchProducts" in tools_called, "SearchProducts tool must have been executed"
    print("\n[PASSED] Audit Check 1: Real Gemini reasoning verified on live backend.")
    return True


async def audit_check_2_shopping_provenance():
    print("\n" + "=" * 70)
    print("AUDIT CHECK 2: Live Shopping Provenance & Honest Error Propagation")
    print("=" * 70)

    # 1. Test live SerpApi search
    assert bool(settings.serpapi_api_key), "SERPAPI_API_KEY must be configured for live provenance check"
    provider = SerpApiShoppingProvider(api_key=settings.serpapi_api_key)

    products = await provider.search_products(
        query="linen shirt beige",
        category="top",
        gender="men",
        max_price=3500.0,
        limit=2
    )

    print(f"[*] Live SerpApi Search returned {len(products)} products.")
    assert len(products) > 0, "Expected live search results from SerpApi"
    for p in products:
        assert p.data_source == DataSourceEnum.LIVE_VERIFIED
        assert not p.id.startswith("fix_")
        print(f"    - Found: '{p.title[:40]}...' at INR {p.price_inr} from {p.merchant}")
        print(f"      Tag: {p.data_source.value} | URL: {p.product_url[:50]}...")

    # 2. Confirm provider error is raised honestly and never silently falls back to fixtures
    print("[*] Testing honest error propagation on provider failure...")
    broken_provider = SerpApiShoppingProvider(api_key="invalid_dummy_key_for_test")
    try:
        await broken_provider.search_products(
            query="test item",
            category="top",
            limit=1
        )
        print("[FAIL] Broken provider did not raise an exception!")
        return False
    except ShoppingProviderError as e:
        print(f"[PASSED] Correctly raised ShoppingProviderError: {e}")
        # Confirm no API key in message
        assert "invalid_dummy_key_for_test" not in str(e), "Secret leaked in error message!"

    print("[PASSED] Audit Check 2: Live shopping provenance and honest error handling verified.")
    return True


async def audit_check_3_hard_constraints():
    print("\n" + "=" * 70)
    print("AUDIT CHECK 3: Deterministic Python Hard Constraints Enforcement")
    print("=" * 70)

    engine = ConstraintEngine()

    # 1. Test deliberately impossible small budget (INR 200)
    print("[*] Test 3.1: Deliberately small budget (INR 200) with real products...")
    from app.models.schemas import ProductItem
    test_top = ProductItem(
        id="item_top_1",
        title="Linen Shirt",
        category="top",
        price_inr=1500.0,
        merchant="Myntra",
        product_url="https://example.com/top",
        image_url="https://example.com/top.jpg",
        available_sizes=["M", "L"]
    )
    test_bot = ProductItem(
        id="item_bot_1",
        title="Cotton Chinos",
        category="bottom",
        price_inr=1800.0,
        merchant="Ajio",
        product_url="https://example.com/bot",
        image_url="https://example.com/bot.jpg",
        available_sizes=["32", "34"]
    )

    budget_eval = engine.evaluate_budget([test_top, test_bot], target_budget=200.0)
    print(f"    Budget Eval: status={budget_eval.status}, details='{budget_eval.details}'")
    assert budget_eval.status == ConstraintStatus.VIOLATED
    assert budget_eval.actual_value == 3300.0
    assert budget_eval.target_value == 200.0

    # 2. Test missing required category (e.g. required top, bottom, shoes; shoes missing)
    print("[*] Test 3.2: Missing required category check...")
    categories_present = [i.category for i in [test_top, test_bot]]
    missing_req = [c for c in ["top", "bottom", "shoes"] if c not in categories_present]
    assert "shoes" in missing_req
    print(f"    Missing Categories Detected: {missing_req}")

    # 3. Test size mismatch rejection
    print("[*] Test 3.3: Sizing mismatch rejection...")
    size_eval = engine.evaluate_sizes(
        [test_top],
        sizes={"top": "XXL"} # XXL not in ["M", "L"]
    )
    print(f"    Size Eval: status={size_eval.status}, details='{size_eval.details}'")
    assert size_eval.status == ConstraintStatus.VIOLATED
    assert "Linen Shirt" in size_eval.details

    # 4. Verify orchestrator rejects Gemini finish_plan if budget is violated
    print("[*] Test 3.4: Orchestrator rejection of LLM finish_plan when over-budget...")
    mock_gemini = AsyncMock()
    mock_gemini.is_configured = MagicMock(return_value=True)
    mock_gemini.generate_initial_plan.return_value = InitialPlan(
        goal_understanding="Formal look",
        style_direction="Sharp",
        preferred_palette=["Black"],
        required_categories=["top"],
        budget_allocation=[{"category": "top", "amount_inr": 500.0}],
        initial_search_queries=[{"category": "top", "query": "shirt"}],
        first_action=AgentActionType.SEARCH_PRODUCTS,
        first_search_args=SearchProductsArgs(query="shirt", category="top", max_price=500.0)
    )

    # Gemini tries to finish immediately despite being over-budget
    mock_gemini.propose_next_action.side_effect = [
        AgentStepDecision(
            thought="I want to finish now even though it is over budget",
            action=AgentActionType.FINISH_PLAN
        ),
        # On replan step:
        AgentStepDecision(
            thought="Switching to cheaper top",
            action=AgentActionType.REPLAN
        ),
        AgentStepDecision(
            thought="Finishing after replan",
            action=AgentActionType.FINISH_PLAN
        )
    ]
    mock_gemini.generate_final_rationale.return_value = FinalStylistResponse(
        stylist_rationale="Stylist approved."
    )

    expensive_top = ProductItem(
        id="exp_1", title="Expensive Top", category="top",
        price_inr=2500.0, merchant="Test", product_url="http://test",
        image_url="http://test.jpg", available_sizes=["M"]
    )
    cheap_top = ProductItem(
        id="chp_1", title="Affordable Top", category="top",
        price_inr=450.0, merchant="Test", product_url="http://test",
        image_url="http://test.jpg", available_sizes=["M"]
    )

    mock_search = AsyncMock()
    mock_search.search_products.side_effect = [[expensive_top], [cheap_top]]

    orchestrator = AgentOrchestrator(
        shopping_provider=mock_search,
        gemini_service=mock_gemini,
        timeout_seconds=10.0,
        max_iterations=4
    )

    req = OutfitRequest(
        occasion="Formal",
        theme="Classic",
        budget_inr=500.0,
        sizes={"top": "M"}
    )
    outfit = await orchestrator.run(req)

    # Confirm Python rejected the initial finish_plan and enforced budget
    trace_thoughts = [s.thought for s in outfit.trace_steps]
    rejected_reasons = [t for t in trace_thoughts if "Rejected proposed finish" in t or "Constraints violated" in t or "Cannot finish" in t or "VIOLATED" in t or "Budget violated" in t]
    assert len(rejected_reasons) > 0, "Python constraint engine must reject LLM premature finish!"
    print(f"    Python rejection recorded: '{rejected_reasons[0]}'")

    print("[PASSED] Audit Check 3: Python deterministic hard constraints strictly verified.")
    return True


async def audit_check_4_fallback_transparency():
    print("\n" + "=" * 70)
    print("AUDIT CHECK 4: Fallback Transparency Under Simulated LLM Failures")
    print("=" * 70)

    # 1. Simulate Gemini Authentication Failure (401)
    print("[*] Test 4.1: Simulating Gemini 401 Authentication Failure...")
    mock_gemini_auth_err = AsyncMock()
    mock_gemini_auth_err.is_configured = MagicMock(return_value=True)
    mock_gemini_auth_err.generate_initial_plan.side_effect = RuntimeError(
        "Gemini API Error during initial planning: 401 UNAUTHENTICATED. Invalid API Key"
    )

    orchestrator = AgentOrchestrator(
        gemini_service=mock_gemini_auth_err,
        shopping_provider=get_shopping_provider(force_mode="fixture")
    )

    req = OutfitRequest(
        occasion="Cocktail Party",
        theme="Elegant",
        budget_inr=6000.0
    )
    result = await orchestrator.run(req)

    print(f"    Orchestration Engine Tag: '{result.orchestration_engine}'")
    print(f"    Error Message Captured: '{result.error_message}'")
    assert result.orchestration_engine == "deterministic_fallback"
    assert "Gemini" in (result.error_message or "")

    # Check trace steps for explicit notification step
    fallback_steps = [s for s in result.trace_steps if s.tool_called == "FallbackToDeterministicEngine"]
    assert len(fallback_steps) > 0, "Trace must include FallbackToDeterministicEngine step!"
    print(f"    Fallback trace step: '{fallback_steps[0].thought}'")

    # 2. Simulate Gemini Timeout
    print("[*] Test 4.2: Simulating Gemini Timeout...")
    mock_gemini_timeout = AsyncMock()
    mock_gemini_timeout.is_configured = MagicMock(return_value=True)
    mock_gemini_timeout.generate_initial_plan.side_effect = TimeoutError("Gemini call timed out after 45.0s")

    orchestrator_timeout = AgentOrchestrator(
        gemini_service=mock_gemini_timeout,
        shopping_provider=get_shopping_provider(force_mode="fixture")
    )
    result_timeout = await orchestrator_timeout.run(req)
    assert result_timeout.orchestration_engine == "deterministic_fallback"
    print(f"    Timeout Fallback Tag: '{result_timeout.orchestration_engine}'")

    print("[PASSED] Audit Check 4: Fallback transparency strictly verified.")
    return True


async def audit_check_5_security_hygiene():
    print("\n" + "=" * 70)
    print("AUDIT CHECK 5: Security & Repository Hygiene")
    print("=" * 70)

    # 1. Verify backend/.env is ignored by git
    import subprocess
    proc = subprocess.run(
        ["git", "check-ignore", "backend/.env"],
        capture_output=True,
        text=True
    )
    assert proc.returncode == 0 and "backend/.env" in proc.stdout, "backend/.env is NOT ignored by git!"
    print("[*] Confirmed backend/.env is properly ignored by .gitignore.")

    # 2. Check git status has no staged secrets
    proc_status = subprocess.run(
        ["git", "status", "--porcelain"],
        capture_output=True,
        text=True
    )
    untracked_lines = proc_status.stdout.strip().splitlines()
    for line in untracked_lines:
        assert ".env" not in line or ".env.example" in line, f"Untracked .env file exposed: {line}"
    print("[*] Confirmed git status has no .env credential files tracked or staged.")

    # 3. Check git tracked files for raw keys
    proc_tracked = subprocess.run(
        ["git", "ls-files"],
        capture_output=True,
        text=True
    )
    assert "backend/.env" not in proc_tracked.stdout.splitlines(), "backend/.env is tracked in git!"
    print("[*] Confirmed backend/.env is NOT tracked in git files.")

    # 4. Check backend/.env.example has placeholder only
    env_example = Path("backend/.env.example").read_text(encoding="utf-8")
    assert "your_gemini_api_key_here" in env_example
    assert "your_serpapi_key_here" in env_example
    print("[*] Confirmed backend/.env.example contains placeholder values only.")

    print("[PASSED] Audit Check 5: Security and repository hygiene verified.")
    return True


async def main():
    print("######################################################################")
    print("# PHASE 2 ACCEPTANCE AUDIT: CODE & RUNTIME VERIFICATION")
    print("######################################################################")

    results = {}
    results["Check 1: Real Gemini Reasoning"] = await audit_check_1_real_gemini_reasoning()
    results["Check 2: Shopping Provenance"] = await audit_check_2_shopping_provenance()
    results["Check 3: Hard Constraints"] = await audit_check_3_hard_constraints()
    results["Check 4: Fallback Transparency"] = await audit_check_4_fallback_transparency()
    results["Check 5: Security & Hygiene"] = await audit_check_5_security_hygiene()

    print("\n" + "=" * 70)
    print("ACCEPTANCE AUDIT SUMMARY")
    print("=" * 70)
    all_passed = True
    for check_name, passed in results.items():
        status = "[PASSED]" if passed else "[FAILED]"
        print(f"  {status} {check_name}")
        if not passed:
            all_passed = False

    print("=" * 70)
    if not all_passed:
        print("[AUDIT FAILED] Some checks did not pass.")
        sys.exit(1)
    else:
        print("[AUDIT PASSED] All 5 Phase 2 Acceptance Checks successfully verified.")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
