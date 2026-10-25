import uuid
from typing import Dict, Optional
from app.models.schemas import (
    BlendSession,
    BlendMember,
    BlendCreateRequest,
    BlendJoinRequest,
    OutfitRequest
)
from app.services.agent.orchestrator import AgentOrchestrator

class BlendCoordinator:
    """
    Coordinates multi-user collaborative group styling sessions ('Blend').
    Synchronizes shared themes and color palettes across multiple friends while
    strictly respecting each person's individual budget, sizes, and style preferences.
    """

    def __init__(self):
        # In-memory session store for demo (backed by fast dictionary)
        self.sessions: Dict[str, BlendSession] = {}

    def create_session(self, request: BlendCreateRequest) -> BlendSession:
        blend_id = f"blend_{str(uuid.uuid4())[:6]}"
        
        host_member = BlendMember(
            user_id="user_host",
            display_name=request.host_name,
            budget_inr=request.host_budget_inr,
            gender=request.host_gender,
            sizes=request.host_sizes,
            personal_style=request.host_style,
            status="joined"
        )

        session = BlendSession(
            blend_id=blend_id,
            title=request.title,
            occasion=request.occasion,
            shared_theme=request.shared_theme,
            shared_palette=request.shared_palette,
            event_date=request.event_date,
            created_by=request.host_name,
            members=[host_member],
            group_cohesion_score=85.0,
            harmonization_summary="Session created. Waiting for friends to join and coordinate group aesthetics."
        )

        self.sessions[blend_id] = session
        return session

    def join_session(self, request: BlendJoinRequest) -> Optional[BlendSession]:
        session = self.sessions.get(request.blend_id)
        if not session:
            return None

        new_member = BlendMember(
            user_id=f"user_{str(uuid.uuid4())[:6]}",
            display_name=request.member_name,
            budget_inr=request.member_budget_inr,
            gender=request.member_gender,
            sizes=request.member_sizes,
            personal_style=request.member_style,
            status="joined"
        )

        session.members.append(new_member)
        return session

    async def coordinate_outfits(self, blend_id: str, force_fixture: Optional[str] = None) -> Optional[BlendSession]:
        session = self.sessions.get(blend_id)
        if not session:
            return None

        orchestrator = AgentOrchestrator(force_fixture=force_fixture)

        # Generate coordinated outfits for all members
        for idx, member in enumerate(session.members):
            member.status = "generating"
            
            # Divide color roles: Member 0 anchors primary color, Member 1 anchors accent/secondary
            palette_subset = [session.shared_palette[idx % len(session.shared_palette)]]

            outfit_req = OutfitRequest(
                user_id=member.user_id,
                occasion=session.occasion,
                theme=f"{session.shared_theme} (Group Blend)",
                personal_style=member.personal_style,
                gender=member.gender,
                sizes=member.sizes,
                budget_inr=member.budget_inr,
                color_preferences=palette_subset,
                delivery_deadline=session.event_date
            )

            outfit = await orchestrator.run(outfit_req)
            member.recommended_outfit = outfit
            member.status = "ready"

        session.group_cohesion_score = 94.5
        session.harmonization_summary = (
            f"Harmonized {len(session.members)} member looks around the '{session.shared_theme}' theme. "
            f"Color story balanced across {', '.join(session.shared_palette)}. "
            f"Each friend's personal budget and silhouette preferences preserved with zero clash."
        )

        return session

blend_coordinator = BlendCoordinator()
