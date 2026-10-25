import uuid
import time
import logging
from typing import Dict, Optional, List
from datetime import datetime, timezone

from app.models.schemas import (
    BlendSession,
    BlendMember,
    BlendCreateRequest,
    BlendJoinRequest,
    BlendSwapRequest,
    OutfitRequest,
    OutfitRecommendation,
    ProductItem,
    AgentTraceStep,
    AgentPhase,
    ConstraintEvaluation,
    ConstraintType,
    ConstraintStatus,
    DataSourceEnum
)
from app.services.agent.orchestrator import AgentOrchestrator
from app.services.agent.constraints import ConstraintEngine
from app.services.agent.gemini_service import GeminiAgentService, sanitize_error_message
from app.services.shopping import get_shopping_provider
from app.services.shopping.base import ShoppingProviderError
from app.services.blend.harmony_engine import HarmonyEngine
from app.services.blend.persistence import BlendPersistenceManager

logger = logging.getLogger("blend.coordinator")

class BlendCoordinator:
    """
    Intelligent Group Outfit Coordinator for Blend.
    Coordinates multi-user collaborative group styling sessions while:
    1. Strictly honoring individual member budgets and hard constraints (zero cross-member subsidy).
    2. Synthesizing a shared aesthetic, formality level, and color story.
    3. Calculating deterministic, multi-dimensional harmony scores.
    4. Providing member-specific autonomous replanning and item swap controls.
    5. Persisting room state across server restarts.
    """

    def __init__(self, persistence_manager: Optional[BlendPersistenceManager] = None):
        self.persistence = persistence_manager or BlendPersistenceManager()
        self.gemini_service = GeminiAgentService()
        self.constraints = ConstraintEngine()

    def get_session(self, blend_id: str) -> Optional[BlendSession]:
        return self.persistence.get(blend_id)

    def list_sessions(self) -> List[BlendSession]:
        return self.persistence.list_all()

    def create_session(self, request: BlendCreateRequest) -> BlendSession:
        if request.host_budget_inr < 500:
            raise ValueError("Host budget must be at least INR 500.")

        blend_id = f"blend_{str(uuid.uuid4())[:6]}"

        host_member = BlendMember(
            user_id="user_host",
            display_name=request.host_name.strip() or "Host",
            budget_inr=request.host_budget_inr,
            gender=request.host_gender,
            sizes=request.host_sizes,
            personal_style=request.host_style.strip() or "Tailored smart casual",
            preferred_colors=request.host_preferred_colors,
            avoid_colors=request.host_avoid_colors,
            required_categories=request.host_required_categories or ["top", "bottom", "shoes"],
            status="joined",
            is_valid=True
        )

        initial_breakdown = HarmonyEngine.evaluate(
            members=[host_member],
            shared_theme=request.shared_theme,
            shared_palette=request.shared_palette,
            occasion=request.occasion
        )

        session = BlendSession(
            blend_id=blend_id,
            title=request.title.strip() or "Group Blend",
            occasion=request.occasion.strip() or "Special Event",
            shared_theme=request.shared_theme.strip() or "Coordinated Style",
            shared_palette=request.shared_palette or ["Navy", "Champagne Gold"],
            event_date=request.event_date,
            created_by=request.host_name,
            members=[host_member],
            group_cohesion_score=initial_breakdown.overall_score,
            score_breakdown=initial_breakdown,
            harmonization_summary="Blend room initialized. Invite friends to coordinate individual styles and budgets.",
            status="draft",
            trace_steps=[
                AgentTraceStep(
                    step_number=1,
                    phase=AgentPhase.UNDERSTAND_GOAL,
                    thought=f"Initialized Blend room '{request.title}' for occasion '{request.occasion}' with shared palette: {', '.join(request.shared_palette)}.",
                    tool_called="InitializeBlendRoom",
                    tool_output={"blend_id": blend_id, "host": request.host_name, "host_budget": request.host_budget_inr}
                )
            ]
        )

        self.persistence.save(session)
        return session

    def join_session(self, request: BlendJoinRequest) -> Optional[BlendSession]:
        session = self.persistence.get(request.blend_id)
        if not session:
            return None

        if request.member_budget_inr < 500:
            raise ValueError("Member budget must be at least INR 500.")

        # Prevent duplicate member names
        existing_names = [m.display_name.lower() for m in session.members]
        clean_name = request.member_name.strip() or f"Member {len(session.members) + 1}"
        if clean_name.lower() in existing_names:
            clean_name = f"{clean_name} ({len(session.members) + 1})"

        member_id = f"user_{str(uuid.uuid4())[:6]}"

        new_member = BlendMember(
            user_id=member_id,
            display_name=clean_name,
            budget_inr=request.member_budget_inr,
            gender=request.member_gender,
            sizes=request.member_sizes,
            personal_style=request.member_style.strip() or "Smart Casual",
            preferred_colors=request.preferred_colors,
            avoid_colors=request.avoid_colors,
            required_categories=request.required_categories or ["top", "bottom", "shoes"],
            status="joined",
            is_valid=True
        )

        session.members.append(new_member)
        session.status = "draft"
        session.updated_at = datetime.now(timezone.utc).isoformat()

        session.trace_steps.append(
            AgentTraceStep(
                step_number=len(session.trace_steps) + 1,
                phase=AgentPhase.UNDERSTAND_GOAL,
                thought=f"Friend '{clean_name}' joined Blend room. Added individual budget INR {request.member_budget_inr:,.2f} and personal style '{request.member_style}'.",
                tool_called="JoinBlendRoom",
                tool_output={"member_id": member_id, "display_name": clean_name, "budget": request.member_budget_inr}
            )
        )

        # Update provisional harmony score
        session.score_breakdown = HarmonyEngine.evaluate(
            members=session.members,
            shared_theme=session.shared_theme,
            shared_palette=session.shared_palette,
            occasion=session.occasion
        )
        session.group_cohesion_score = session.score_breakdown.overall_score

        self.persistence.save(session)
        return session

    async def coordinate_outfits(
        self,
        blend_id: str,
        force_fixture: Optional[str] = None
    ) -> Optional[BlendSession]:
        session = self.persistence.get(blend_id)
        if not session:
            return None

        session.status = "coordinating"
        session.updated_at = datetime.now(timezone.utc).isoformat()
        orchestrator = AgentOrchestrator(force_fixture=force_fixture)

        # 1. Group-level aesthetic planning
        color_assignments = self._plan_color_distribution(session)

        session.trace_steps.append(
            AgentTraceStep(
                step_number=len(session.trace_steps) + 1,
                phase=AgentPhase.DECOMPOSE_PLAN,
                thought=f"Group Planning: Formulated color distribution across {len(session.members)} members to ensure complementary balance without identical styling.",
                tool_called="PlanGroupPaletteDistribution",
                tool_output={"color_roles": color_assignments, "palette": session.shared_palette}
            )
        )

        # 2. Per-member bounded assembly & validation
        for idx, member in enumerate(session.members):
            member.status = "generating"
            assigned_colors = color_assignments.get(member.user_id, session.shared_palette)

            outfit_req = OutfitRequest(
                user_id=member.user_id,
                occasion=session.occasion,
                theme=f"{session.shared_theme} ({member.personal_style})",
                personal_style=member.personal_style,
                gender=member.gender,
                sizes=member.sizes,
                budget_inr=member.budget_inr,
                color_preferences=assigned_colors,
                avoid_colors=member.avoid_colors,
                delivery_deadline=session.event_date,
                force_test_fixture=force_fixture
            )

            # Assemble individual outfit
            try:
                outfit = await orchestrator.run(outfit_req)
            except ShoppingProviderError as e:
                logger.warning(f"Shopping provider error for {member.display_name}: {e}")
                outfit = OutfitRecommendation(
                    outfit_id=f"err_{member.user_id}",
                    user_id=member.user_id,
                    occasion=session.occasion,
                    theme=session.shared_theme,
                    items=[],
                    total_price_inr=0.0,
                    target_budget_inr=member.budget_inr,
                    is_within_budget=True,
                    harmony_score=0.0,
                    stylist_rationale=f"Shopping provider failed: {str(e)}",
                    status="failed",
                    data_source_mode=DataSourceEnum.LIVE_VERIFIED,
                    error_message=str(e)
                )

            # Deterministic individual validation in Python
            validation_errors = []
            if outfit.total_price_inr > member.budget_inr:
                overrun = outfit.total_price_inr - member.budget_inr
                validation_errors.append(f"Exceeds budget by INR {overrun:,.2f}")

            # Check required categories
            cats_present = {item.category.lower() for item in outfit.items}
            titles_lower = " ".join(item.title.lower() for item in outfit.items)
            is_full_ethnic = any(e in titles_lower for e in ["anarkali", "kurta set", "suit set", "saree", "lehenga"])

            for req_cat in member.required_categories:
                req_lower = req_cat.lower()
                if is_full_ethnic and req_lower in ["top", "bottom"]:
                    continue
                if req_lower not in cats_present:
                    validation_errors.append(f"Missing required piece: {req_cat}")

            # Check avoided colors
            for item in outfit.items:
                for avoided in member.avoid_colors:
                    if avoided.lower() in item.title.lower():
                        validation_errors.append(f"Item '{item.title}' matches avoided color '{avoided}'")

            # 3. Autonomous repair if constraints violated
            if validation_errors and len(outfit.items) > 1:
                session.trace_steps.append(
                    AgentTraceStep(
                        step_number=len(session.trace_steps) + 1,
                        phase=AgentPhase.REPLAN,
                        thought=f"Detected constraint issue for {member.display_name}: {'; '.join(validation_errors)}. Initiating member-specific repair loop.",
                        tool_called="ReplanMemberOutfit",
                        tool_output={"member": member.display_name, "issues": validation_errors}
                    )
                )

                # Attempt targeted repair for over-budget or clashing item
                outfit, repaired_errors = await self._attempt_member_repair(
                    member=member,
                    outfit=outfit,
                    orchestrator=orchestrator,
                    session=session,
                    force_fixture=force_fixture
                )
                validation_errors = repaired_errors

            member.recommended_outfit = outfit
            member.unresolved_constraints = validation_errors
            member.is_valid = len(validation_errors) == 0
            member.status = "ready" if member.is_valid else "partial"

            session.trace_steps.append(
                AgentTraceStep(
                    step_number=len(session.trace_steps) + 1,
                    phase=AgentPhase.EVALUATE_CONSTRAINTS,
                    thought=f"Verified {member.display_name}'s ensemble: Total INR {outfit.total_price_inr:,.2f} / Budget INR {member.budget_inr:,.2f} ({'PASSED' if member.is_valid else 'UNRESOLVED CONSTRAINTS'}).",
                    tool_called="ValidateMemberConstraints",
                    tool_output={
                        "member": member.display_name,
                        "valid": member.is_valid,
                        "total_inr": outfit.total_price_inr,
                        "budget_inr": member.budget_inr,
                        "unresolved": validation_errors
                    }
                )
            )

        # 4. Compute deterministic group harmony score and breakdown
        breakdown = HarmonyEngine.evaluate(
            members=session.members,
            shared_theme=session.shared_theme,
            shared_palette=session.shared_palette,
            occasion=session.occasion
        )

        session.group_cohesion_score = breakdown.overall_score
        session.score_breakdown = breakdown

        all_valid = all(m.is_valid for m in session.members)
        session.status = "ready" if all_valid else "partial"

        session.harmonization_summary = (
            f"Harmonized {len(session.members)} looks around '{session.shared_theme}' (Cohesion: {breakdown.overall_score}%). "
            f"Color palette balance: {breakdown.palette_harmony}%, Formality: {breakdown.formality_consistency}%, "
            f"Budget compliance: {breakdown.budget_compliance}%. "
            f"{'All individual budgets strictly preserved.' if all_valid else 'Note: Some member constraints require review.'}"
        )

        session.trace_steps.append(
            AgentTraceStep(
                step_number=len(session.trace_steps) + 1,
                phase=AgentPhase.COMPLETED,
                thought=f"Coordination complete. Computed group cohesion {breakdown.overall_score}% across {len(session.members)} members.",
                tool_called="FinalizeGroupCoordination",
                tool_output={"cohesion_score": breakdown.overall_score, "breakdown": breakdown.model_dump()}
            )
        )

        self.persistence.save(session)
        return session

    def _plan_color_distribution(self, session: BlendSession) -> Dict[str, List[str]]:
        """
        Assigns distinct color subsets from the shared palette so members harmonize
        without wearing matching uniforms.
        """
        palette = session.shared_palette or ["Navy", "Champagne Gold"]
        assignments: Dict[str, List[str]] = {}

        for idx, m in enumerate(session.members):
            # Member 0 anchors primary; member 1 anchors secondary/accent
            primary = palette[idx % len(palette)]
            secondary = palette[(idx + 1) % len(palette)]
            assignments[m.user_id] = [primary, secondary]

        return assignments

    async def _attempt_member_repair(
        self,
        member: BlendMember,
        outfit: OutfitRecommendation,
        orchestrator: AgentOrchestrator,
        session: BlendSession,
        force_fixture: Optional[str]
    ) -> tuple[OutfitRecommendation, List[str]]:
        """
        Attempts targeted item replacement for a member whose constraints were violated.
        Preserves other valid items in their ensemble.
        """
        items = list(outfit.items)
        if not items:
            return outfit, ["No items to repair."]

        # Identify most expensive or clashing item
        overrun = outfit.total_price_inr - member.budget_inr
        priciest_item = max(items, key=lambda i: i.price_inr)

        # Target sub-budget for replacement
        target_sub_budget = max(500.0, priciest_item.price_inr - overrun - 100.0)

        replacements = await orchestrator.tools.search_products(
            query=f"affordable {priciest_item.category} {member.personal_style}",
            category=priciest_item.category,
            gender=member.gender.value if hasattr(member.gender, "value") else str(member.gender),
            max_price=target_sub_budget,
            limit=2
        )

        if replacements:
            # Swap priciest item with lower-priced alternative
            repaired_items = [i for i in items if i.id != priciest_item.id] + [replacements[0]]
            new_total = sum(i.price_inr for i in repaired_items)

            updated_outfit = OutfitRecommendation(
                outfit_id=outfit.outfit_id,
                user_id=member.user_id,
                occasion=outfit.occasion,
                theme=outfit.theme,
                items=repaired_items,
                total_price_inr=new_total,
                target_budget_inr=member.budget_inr,
                is_within_budget=new_total <= member.budget_inr,
                harmony_score=outfit.harmony_score,
                stylist_rationale=f"Repaired ensemble: Swapped {priciest_item.title} (INR {priciest_item.price_inr:,.0f}) for {replacements[0].title} (INR {replacements[0].price_inr:,.0f}) to meet budget.",
                tradeoffs_considered=outfit.tradeoffs_considered + ["Repaired item to satisfy budget ceiling."],
                trace_steps=outfit.trace_steps,
                orchestration_engine=outfit.orchestration_engine,
                data_source_mode=outfit.data_source_mode,
                status="complete" if new_total <= member.budget_inr else "partial"
            )

            remaining_errors = []
            if new_total > member.budget_inr:
                remaining_errors.append(f"Exceeds budget by INR {new_total - member.budget_inr:,.2f}")

            return updated_outfit, remaining_errors

        # If repair search yielded no items, return original with honest error
        return outfit, [f"Could not find lower-cost replacement for {priciest_item.title}"]

    async def swap_member_item(
        self,
        request: BlendSwapRequest,
        force_fixture: Optional[str] = None
    ) -> Optional[BlendSession]:
        """
        Human-in-the-loop item critique and swap for a specific member.
        Replaces rejected item, re-evaluates member budget, and recalculates group harmony.
        """
        session = self.persistence.get(request.blend_id)
        if not session:
            return None

        member = next((m for m in session.members if m.user_id == request.member_id), None)
        if not member or not member.recommended_outfit:
            return None

        outfit = member.recommended_outfit
        item_to_replace = next((i for i in outfit.items if i.id == request.rejected_item_id), None)
        if not item_to_replace:
            # If item id not found, return existing session safely
            return session

        orchestrator = AgentOrchestrator(force_fixture=force_fixture)
        target_cat = request.target_category or item_to_replace.category
        search_query = request.feedback_text or f"{item_to_replace.category} alternative"

        # Search replacements respecting member's budget headroom
        other_items = [i for i in outfit.items if i.id != item_to_replace.id]
        other_total = sum(i.price_inr for i in other_items)
        max_price = request.max_price_inr or max(500.0, member.budget_inr - other_total)

        replacements = await orchestrator.tools.search_products(
            query=search_query,
            category=target_cat,
            gender=member.gender.value if hasattr(member.gender, "value") else str(member.gender),
            max_price=max_price,
            limit=4
        )

        # Filter out the explicitly rejected item so a genuinely different item is selected
        valid_candidates = [r for r in replacements if r.id != item_to_replace.id]
        new_item = valid_candidates[0] if valid_candidates else (replacements[0] if replacements else None)

        if new_item and new_item.id != item_to_replace.id:
            updated_items = other_items + [new_item]
            new_total = sum(i.price_inr for i in updated_items)

            member.recommended_outfit = OutfitRecommendation(
                outfit_id=outfit.outfit_id,
                user_id=member.user_id,
                occasion=outfit.occasion,
                theme=outfit.theme,
                items=updated_items,
                total_price_inr=new_total,
                target_budget_inr=member.budget_inr,
                is_within_budget=new_total <= member.budget_inr,
                harmony_score=outfit.harmony_score,
                stylist_rationale=f"Updated ensemble based on critique: Swapped '{item_to_replace.title}' for '{new_item.title}'.",
                tradeoffs_considered=outfit.tradeoffs_considered + [f"Human critique applied: {request.feedback_text}"],
                trace_steps=outfit.trace_steps,
                orchestration_engine=outfit.orchestration_engine,
                data_source_mode=new_item.data_source,
                status="complete" if new_total <= member.budget_inr else "partial"
            )

            member.is_valid = new_total <= member.budget_inr
            member.unresolved_constraints = [] if member.is_valid else [f"Exceeds budget by INR {new_total - member.budget_inr:,.2f}"]

            # Recalculate group harmony score and breakdown
            breakdown = HarmonyEngine.evaluate(
                members=session.members,
                shared_theme=session.shared_theme,
                shared_palette=session.shared_palette,
                occasion=session.occasion
            )
            session.group_cohesion_score = breakdown.overall_score
            session.score_breakdown = breakdown
            session.updated_at = datetime.now(timezone.utc).isoformat()

            session.trace_steps.append(
                AgentTraceStep(
                    step_number=len(session.trace_steps) + 1,
                    phase=AgentPhase.REPLAN,
                    thought=f"Swap executed for {member.display_name}: Replaced '{item_to_replace.title}' with '{new_item.title}' (INR {new_item.price_inr:,.0f}). Recalculated group cohesion to {breakdown.overall_score}%.",
                    tool_called="SwapMemberItem",
                    tool_output={
                        "member": member.display_name,
                        "old_item": item_to_replace.title,
                        "new_item": new_item.title,
                        "new_total_inr": new_total,
                        "new_cohesion_score": breakdown.overall_score
                    }
                )
            )

            self.persistence.save(session)

        return session

blend_coordinator = BlendCoordinator()
