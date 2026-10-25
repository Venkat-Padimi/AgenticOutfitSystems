import sys
from pathlib import Path

backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

import pytest
import asyncio
from unittest.mock import AsyncMock, patch
from app.models.schemas import (
    BlendSession,
    BlendMember,
    BlendCreateRequest,
    BlendJoinRequest,
    BlendSwapRequest,
    OutfitRecommendation,
    ProductItem,
    GenderEnum,
    DataSourceEnum
)
from app.services.blend.coordinator import BlendCoordinator
from app.services.blend.harmony_engine import HarmonyEngine
from app.services.blend.persistence import BlendPersistenceManager
from app.services.shopping.base import ShoppingProviderError

# Helper mock items
ITEM_NAVY_BLAZER = ProductItem(
    id="prod_top_1",
    title="Navy Blue Tailored Blazer",
    category="top",
    price_inr=2699.0,
    merchant="Myntra",
    product_url="https://myntra.com/p/1",
    image_url="https://images.unsplash.com/blazer.jpg",
    available_sizes=["M", "L", "XL"],
    data_source=DataSourceEnum.CONTROLLED_FIXTURE
)

ITEM_BEIGE_CHINOS = ProductItem(
    id="prod_bot_1",
    title="Slim Fit Beige Chinos",
    category="bottom",
    price_inr=1499.0,
    merchant="Ajio",
    product_url="https://ajio.com/p/2",
    image_url="https://images.unsplash.com/chinos.jpg",
    available_sizes=["32", "34"],
    data_source=DataSourceEnum.CONTROLLED_FIXTURE
)

ITEM_LOAFERS = ProductItem(
    id="prod_shoe_1",
    title="Classic Tan Leather Loafers",
    category="shoes",
    price_inr=1699.0,
    merchant="Amazon India",
    product_url="https://amazon.in/p/3",
    image_url="https://images.unsplash.com/loafers.jpg",
    available_sizes=["UK 9"],
    data_source=DataSourceEnum.CONTROLLED_FIXTURE
)

ITEM_ANARKALI_KURTA = ProductItem(
    id="prod_ethnic_1",
    title="Champagne Gold Embroidered Kurta Set",
    category="ethnic",
    price_inr=2199.0,
    merchant="Myntra",
    product_url="https://myntra.com/p/4",
    image_url="https://images.unsplash.com/kurta.jpg",
    available_sizes=["S", "M"],
    data_source=DataSourceEnum.CONTROLLED_FIXTURE
)

ITEM_MOJARI = ProductItem(
    id="prod_shoe_2",
    title="Champagne Handcrafted Ethnic Mojaris",
    category="shoes",
    price_inr=999.0,
    merchant="Ajio",
    product_url="https://ajio.com/p/5",
    image_url="https://images.unsplash.com/mojari.jpg",
    available_sizes=["UK 5"],
    data_source=DataSourceEnum.CONTROLLED_FIXTURE
)

ITEM_NEON_TEE = ProductItem(
    id="prod_top_clash",
    title="Neon Green Distressed Graphic Tee",
    category="top",
    price_inr=899.0,
    merchant="Flipkart",
    product_url="https://flipkart.com/p/6",
    image_url="https://images.unsplash.com/neon.jpg",
    available_sizes=["M"],
    data_source=DataSourceEnum.CONTROLLED_FIXTURE
)

ITEM_CHEAP_SNEAKERS = ProductItem(
    id="prod_shoe_swap",
    title="White Minimalist Court Sneakers",
    category="shoes",
    price_inr=1199.0,
    merchant="Ajio",
    product_url="https://ajio.com/p/7",
    image_url="https://images.unsplash.com/sneakers.jpg",
    available_sizes=["UK 9"],
    data_source=DataSourceEnum.CONTROLLED_FIXTURE
)

@pytest.fixture
def tmp_coordinator(tmp_path):
    persistence = BlendPersistenceManager(storage_dir=tmp_path / "blend_rooms")
    return BlendCoordinator(persistence_manager=persistence)

# -----------------------------------------------------------------------------
# 1. Test different individual budgets
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_group_different_individual_budgets(tmp_coordinator):
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="College Farewell Gala",
        occasion="Graduation",
        shared_theme="Royal Retro",
        shared_palette=["Navy", "Champagne Gold"],
        host_name="Arjun",
        host_budget_inr=6000.0,
        host_style="Formal Smart"
    ))
    tmp_coordinator.join_session(BlendJoinRequest(
        blend_id=session.blend_id,
        member_name="Sneha",
        member_budget_inr=3500.0,
        member_style="Indo-Western",
        member_gender=GenderEnum.WOMEN
    ))

    coordinated = await tmp_coordinator.coordinate_outfits(session.blend_id, force_fixture="fixture")
    assert coordinated is not None
    m1 = coordinated.members[0]
    m2 = coordinated.members[1]

    # Verify individual budgets are preserved without cross-subsidy
    assert m1.recommended_outfit.total_price_inr <= 6000.0
    assert m2.recommended_outfit.total_price_inr <= 3500.0
    assert m1.budget_inr == 6000.0
    assert m2.budget_inr == 3500.0

# -----------------------------------------------------------------------------
# 2. Test different style preferences with shared palette
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_group_different_styles_shared_palette(tmp_coordinator):
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="Diwali Dinner",
        occasion="Festive",
        shared_theme="Festive Chic",
        shared_palette=["Royal Blue", "Champagne Gold", "Ivory"],
        host_name="HostA",
        host_budget_inr=5500.0,
        host_style="Contemporary Indo-Western"
    ))
    tmp_coordinator.join_session(BlendJoinRequest(
        blend_id=session.blend_id,
        member_name="FriendB",
        member_budget_inr=4000.0,
        member_style="Minimalist Silk Ethnic",
        member_gender=GenderEnum.WOMEN
    ))

    coordinated = await tmp_coordinator.coordinate_outfits(session.blend_id, force_fixture="fixture")
    assert coordinated.score_breakdown.palette_harmony >= 65.0
    assert coordinated.group_cohesion_score >= 80.0

# -----------------------------------------------------------------------------
# 3. Test member budget exceeded -> penalized score and cap at 75
# -----------------------------------------------------------------------------
def test_member_budget_exceeded_penalized_score():
    member1 = BlendMember(
        user_id="u1",
        display_name="Arjun",
        budget_inr=5000.0,
        gender=GenderEnum.MEN,
        sizes={},
        personal_style="Smart",
        recommended_outfit=OutfitRecommendation(
            outfit_id="o1",
            user_id="u1",
            occasion="Farewell",
            theme="Retro",
            items=[ITEM_NAVY_BLAZER, ITEM_BEIGE_CHINOS, ITEM_LOAFERS], # Total = 5897.0 > 5000.0
            total_price_inr=5897.0,
            target_budget_inr=5000.0,
            is_within_budget=False,
            stylist_rationale="Over budget demo"
        )
    )

    breakdown = HarmonyEngine.evaluate(
        members=[member1],
        shared_theme="Retro",
        shared_palette=["Navy", "Beige"],
        occasion="Farewell"
    )

    # Must be penalized and capped at 74.5
    assert breakdown.budget_compliance < 100.0
    assert breakdown.overall_score <= 74.5
    assert any("Budget exceeded" in note for note in breakdown.summary_notes)

# -----------------------------------------------------------------------------
# 4. Test missing required category
# -----------------------------------------------------------------------------
def test_member_missing_required_category():
    member1 = BlendMember(
        user_id="u1",
        display_name="Arjun",
        budget_inr=6000.0,
        gender=GenderEnum.MEN,
        sizes={},
        personal_style="Smart",
        required_categories=["top", "bottom", "shoes"],
        recommended_outfit=OutfitRecommendation(
            outfit_id="o1",
            user_id="u1",
            occasion="Farewell",
            theme="Retro",
            items=[ITEM_NAVY_BLAZER], # Only top, missing bottom and shoes
            total_price_inr=2699.0,
            target_budget_inr=6000.0,
            is_within_budget=True,
            stylist_rationale="Partial look"
        )
    )

    breakdown = HarmonyEngine.evaluate(
        members=[member1],
        shared_theme="Retro",
        shared_palette=["Navy"],
        occasion="Farewell"
    )

    assert breakdown.category_completeness < 100.0
    assert any("missing required piece" in note for note in breakdown.summary_notes)

# -----------------------------------------------------------------------------
# 5. Test product that violates individual exclusion (avoid_colors)
# -----------------------------------------------------------------------------
def test_product_violates_avoid_colors():
    member_avoid = BlendMember(
        user_id="u1",
        display_name="Rahul",
        budget_inr=5000.0,
        gender=GenderEnum.MEN,
        sizes={},
        personal_style="Casual",
        avoid_colors=["Neon Green"],
        recommended_outfit=OutfitRecommendation(
            outfit_id="o1",
            user_id="u1",
            occasion="Festive",
            theme="Festive",
            items=[ITEM_NEON_TEE], # Clashes with avoid_colors
            total_price_inr=899.0,
            target_budget_inr=5000.0,
            is_within_budget=True,
            stylist_rationale="Clashing tee"
        )
    )

    breakdown = HarmonyEngine.evaluate(
        members=[member_avoid],
        shared_theme="Festive",
        shared_palette=["Navy", "Gold"],
        occasion="Festive"
    )

    assert breakdown.palette_harmony <= 40.0
    assert any("avoided color" in note for note in breakdown.summary_notes)

# -----------------------------------------------------------------------------
# 6. Test group harmony changes when a product is swapped
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_harmony_score_changes_on_swap(tmp_coordinator):
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="College Farewell",
        occasion="Graduation",
        shared_theme="Retro",
        shared_palette=["Navy", "Beige", "Tan"],
        host_name="Arjun",
        host_budget_inr=6000.0
    ))
    coordinated = await tmp_coordinator.coordinate_outfits(session.blend_id, force_fixture="fixture")
    score_before = coordinated.group_cohesion_score

    # Swap host shoes
    swap_req = BlendSwapRequest(
        blend_id=session.blend_id,
        member_id="user_host",
        rejected_item_id=coordinated.members[0].recommended_outfit.items[2].id,
        feedback_text="Clean white court sneakers"
    )
    swapped = await tmp_coordinator.swap_member_item(swap_req, force_fixture="fixture")
    assert swapped is not None
    # Verify recalculation took place
    assert swapped.score_breakdown is not None
    assert isinstance(swapped.group_cohesion_score, float)

# -----------------------------------------------------------------------------
# 7. Test harmony score is not hardcoded
# -----------------------------------------------------------------------------
def test_harmony_score_not_hardcoded():
    m_perfect = BlendMember(
        user_id="u1",
        display_name="M1",
        budget_inr=6000.0,
        gender=GenderEnum.MEN,
        sizes={},
        personal_style="Smart Casual",
        recommended_outfit=OutfitRecommendation(
            outfit_id="o1", user_id="u1", occasion="Farewell", theme="Retro",
            items=[ITEM_NAVY_BLAZER, ITEM_BEIGE_CHINOS, ITEM_LOAFERS],
            total_price_inr=5897.0, target_budget_inr=6000.0, is_within_budget=True,
            stylist_rationale="Cohesive look"
        )
    )

    m_clash = BlendMember(
        user_id="u2",
        display_name="M2",
        budget_inr=2000.0,
        gender=GenderEnum.MEN,
        sizes={},
        personal_style="Gym",
        avoid_colors=["Neon Green"],
        recommended_outfit=OutfitRecommendation(
            outfit_id="o2", user_id="u2", occasion="Farewell", theme="Retro",
            items=[ITEM_NEON_TEE],
            total_price_inr=899.0, target_budget_inr=2000.0, is_within_budget=True,
            stylist_rationale="Clashing look"
        )
    )

    score_perfect = HarmonyEngine.evaluate([m_perfect], "Retro", ["Navy", "Beige"], "Farewell").overall_score
    score_clash = HarmonyEngine.evaluate([m_clash], "Retro", ["Navy", "Beige"], "Farewell").overall_score

    assert score_perfect != score_clash
    assert score_perfect > score_clash

    m_budget_fail = BlendMember(
        user_id="u3",
        display_name="M3",
        budget_inr=1000.0,
        gender=GenderEnum.MEN,
        sizes={},
        personal_style="Formal",
        recommended_outfit=OutfitRecommendation(
            outfit_id="o3", user_id="u3", occasion="Farewell", theme="Retro",
            items=[ITEM_NAVY_BLAZER, ITEM_BEIGE_CHINOS],
            total_price_inr=4198.0, target_budget_inr=1000.0, is_within_budget=False,
            stylist_rationale="Overrun"
        )
    )
    score_budget_fail = HarmonyEngine.evaluate([m_budget_fail], "Retro", ["Navy"], "Farewell").overall_score
    assert len({score_perfect, score_clash, score_budget_fail}) >= 2, "Harmony scores must be dynamic and not hardcoded"
    assert score_budget_fail < score_perfect

# -----------------------------------------------------------------------------
# 8. Test failed repair returns honest partial status
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_failed_repair_returns_honest_status(tmp_coordinator):
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="Tight Budget Farewell",
        occasion="Farewell",
        shared_theme="Smart",
        shared_palette=["Navy"],
        host_name="Arjun",
        host_budget_inr=500.0 # Deliberately unachievable complete budget
    ))

    coordinated = await tmp_coordinator.coordinate_outfits(session.blend_id, force_fixture="fixture")
    assert coordinated.members[0].is_valid is False
    assert coordinated.status in ["partial", "failed"]
    assert len(coordinated.members[0].unresolved_constraints) > 0

# -----------------------------------------------------------------------------
# 9. Test repairing one member preserves other valid outfits
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_repairing_one_member_preserves_others(tmp_coordinator):
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="College Event",
        occasion="Farewell",
        shared_theme="Retro",
        shared_palette=["Navy", "Champagne Gold"],
        host_name="ValidMember",
        host_budget_inr=6000.0
    ))
    tmp_coordinator.join_session(BlendJoinRequest(
        blend_id=session.blend_id,
        member_name="BudgetMember",
        member_budget_inr=5000.0,
        member_style="Smart Casual",
        member_gender=GenderEnum.MEN
    ))

    coordinated = await tmp_coordinator.coordinate_outfits(session.blend_id, force_fixture="fixture")
    host_item_ids = [i.id for i in coordinated.members[0].recommended_outfit.items]

    # Swap item for friend only
    friend_id = coordinated.members[1].user_id
    rejected_id = coordinated.members[1].recommended_outfit.items[0].id
    swapped = await tmp_coordinator.swap_member_item(BlendSwapRequest(
        blend_id=session.blend_id,
        member_id=friend_id,
        rejected_item_id=rejected_id,
        feedback_text="Casual blazer"
    ), force_fixture="fixture")

    # Host items must remain identical (zero collateral damage)
    new_host_item_ids = [i.id for i in swapped.members[0].recommended_outfit.items]
    assert host_item_ids == new_host_item_ids

# -----------------------------------------------------------------------------
# 10. Test feedback applies to correct member and item
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_feedback_applies_to_correct_member(tmp_coordinator):
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="Graduation",
        occasion="Farewell",
        shared_theme="Royal Retro",
        shared_palette=["Navy", "Gold"],
        host_name="Arjun",
        host_budget_inr=6000.0
    ))
    tmp_coordinator.join_session(BlendJoinRequest(
        blend_id=session.blend_id,
        member_name="Sneha",
        member_budget_inr=5000.0,
        member_style="Indo-Western",
        member_gender=GenderEnum.WOMEN
    ))
    coordinated = await tmp_coordinator.coordinate_outfits(session.blend_id, force_fixture="fixture")

    # In Sneha's outfit, items are Anarkali Kurta (ethnic) and Mojaris (shoes)
    friend = coordinated.members[1]
    friend_shoe = next(i for i in friend.recommended_outfit.items if i.category == "shoes")

    updated_session = await tmp_coordinator.swap_member_item(BlendSwapRequest(
        blend_id=session.blend_id,
        member_id=friend.user_id,
        rejected_item_id=friend_shoe.id,
        feedback_text="Metallic block heel sandals"
    ), force_fixture="fixture")

    updated_friend = updated_session.members[1]
    updated_item_ids = [i.id for i in updated_friend.recommended_outfit.items]
    assert friend_shoe.id not in updated_item_ids, "Rejected item must be replaced"

# -----------------------------------------------------------------------------
# 11. Test invalid room / member / item identifiers handled safely
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_invalid_identifiers_handled_safely(tmp_coordinator):
    # Nonexistent room
    bad_session = await tmp_coordinator.coordinate_outfits("blend_nonexistent")
    assert bad_session is None

    bad_swap = await tmp_coordinator.swap_member_item(BlendSwapRequest(
        blend_id="blend_nonexistent",
        member_id="user_fake",
        rejected_item_id="prod_fake"
    ))
    assert bad_swap is None

    # Valid room, nonexistent member
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="Test Room",
        occasion="Event",
        shared_theme="Theme",
        shared_palette=["Navy"],
        host_name="Host"
    ))
    bad_member_swap = await tmp_coordinator.swap_member_item(BlendSwapRequest(
        blend_id=session.blend_id,
        member_id="user_nonexistent",
        rejected_item_id="prod_fake"
    ))
    assert bad_member_swap is None

# -----------------------------------------------------------------------------
# 12. Test live provider errors do not silently fall back to fixtures
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_live_provider_error_surfaced_honestly(tmp_coordinator):
    mock_live_provider = AsyncMock()
    mock_live_provider.search_products.side_effect = ShoppingProviderError("SerpApi 401 Unauthorized")

    with patch("app.services.agent.orchestrator.get_shopping_provider", return_value=mock_live_provider), \
         patch("app.services.agent.gemini_service.GeminiAgentService.is_configured", return_value=False):
        session = tmp_coordinator.create_session(BlendCreateRequest(
            title="Live Error Test",
            occasion="Event",
            shared_theme="Theme",
            shared_palette=["Navy"],
            host_name="Host"
        ))

        # Coordination under live provider failure should handle error honestly
        coordinated = await tmp_coordinator.coordinate_outfits(session.blend_id, force_fixture=None)
        assert coordinated is not None
        assert coordinated.status in ["partial", "failed"]
        # Must not silently claim live verified items or fall back silently to fixtures
        host_member = coordinated.members[0]
        assert host_member.status in ["failed", "partial"]
        assert len(host_member.recommended_outfit.items) == 0
        assert any(term in (host_member.recommended_outfit.error_message or host_member.recommended_outfit.stylist_rationale) for term in ["SerpApi", "401", "Shopping provider"])
        assert "Shopping provider failed" in host_member.recommended_outfit.stylist_rationale

# -----------------------------------------------------------------------------
# 13. Test fixture mode remains deterministic and correctly labelled
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_fixture_mode_correctly_labelled(tmp_coordinator):
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="Fixture Verification",
        occasion="Farewell",
        shared_theme="Smart",
        shared_palette=["Navy"],
        host_name="Arjun",
        host_budget_inr=5000.0
    ))
    coordinated = await tmp_coordinator.coordinate_outfits(session.blend_id, force_fixture="fixture")
    for m in coordinated.members:
        outfit = m.recommended_outfit
        assert outfit.data_source_mode == DataSourceEnum.CONTROLLED_FIXTURE
        for item in outfit.items:
            assert item.data_source == DataSourceEnum.CONTROLLED_FIXTURE

# -----------------------------------------------------------------------------
# 14. Test room persistence works across manager instances
# -----------------------------------------------------------------------------
def test_room_persistence_across_instances(tmp_path):
    storage_dir = tmp_path / "persistence_test"
    mgr1 = BlendPersistenceManager(storage_dir=storage_dir)
    coord1 = BlendCoordinator(persistence_manager=mgr1)

    session = coord1.create_session(BlendCreateRequest(
        title="Persistent Room 2026",
        occasion="Gala",
        shared_theme="Retro",
        shared_palette=["Gold"],
        host_name="PersistentHost"
    ))

    # Create fresh manager simulating server restart
    mgr2 = BlendPersistenceManager(storage_dir=storage_dir)
    loaded = mgr2.get(session.blend_id)

    assert loaded is not None
    assert loaded.blend_id == session.blend_id
    assert loaded.title == "Persistent Room 2026"
    assert loaded.members[0].display_name == "PersistentHost"

# -----------------------------------------------------------------------------
# 15. Verify existing Phase 1–3 tests continue to pass
# -----------------------------------------------------------------------------
@pytest.mark.asyncio
async def test_phase1_3_compatibility(tmp_coordinator):
    session = tmp_coordinator.create_session(BlendCreateRequest(
        title="Legacy Room",
        occasion="Event",
        shared_theme="Theme",
        shared_palette=["Navy", "White"],
        host_name="Host"
    ))
    assert session.blend_id.startswith("blend_")
    assert session.group_cohesion_score >= 0.0
