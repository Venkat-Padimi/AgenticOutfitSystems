from fastapi import APIRouter, HTTPException
from app.models.schemas import (
    BlendSession,
    BlendCreateRequest,
    BlendJoinRequest
)
from app.services.blend.coordinator import blend_coordinator

router = APIRouter(prefix="/api/v1/blend", tags=["Blend Collaborative Group Styling"])

@router.post("/create", response_model=BlendSession)
def create_blend_room(request: BlendCreateRequest):
    """
    Creates a new collaborative group styling room for an event, theme, and shared palette.
    """
    return blend_coordinator.create_session(request)

@router.post("/join", response_model=BlendSession)
def join_blend_room(request: BlendJoinRequest):
    """
    Allows a friend to join a group Blend room with their personal budget and style.
    """
    session = blend_coordinator.join_session(request)
    if not session:
        raise HTTPException(status_code=404, detail="Blend room ID not found")
    return session

@router.get("/{blend_id}", response_model=BlendSession)
def get_blend_room(blend_id: str):
    """
    Fetches the current status and member outfits of a Blend room.
    """
    session = blend_coordinator.sessions.get(blend_id)
    if not session:
        raise HTTPException(status_code=404, detail="Blend room not found")
    return session

@router.post("/{blend_id}/coordinate", response_model=BlendSession)
async def coordinate_blend_outfits(blend_id: str):
    """
    Triggers the autonomous agent to harmonize outfits for all members in the room.
    """
    session = await blend_coordinator.coordinate_outfits(blend_id)
    if not session:
        raise HTTPException(status_code=404, detail="Blend room not found")
    return session
