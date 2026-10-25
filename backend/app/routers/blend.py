from fastapi import APIRouter, HTTPException, Query
from typing import Optional
from app.models.schemas import (
    BlendSession,
    BlendCreateRequest,
    BlendJoinRequest,
    BlendSwapRequest
)
from app.services.blend.coordinator import blend_coordinator

router = APIRouter(prefix="/api/v1/blend", tags=["Blend Collaborative Group Styling"])

@router.post("/create", response_model=BlendSession)
def create_blend_room(request: BlendCreateRequest):
    """
    Creates a new collaborative group styling room for an event, theme, and shared palette.
    """
    try:
        return blend_coordinator.create_session(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/join", response_model=BlendSession)
def join_blend_room(request: BlendJoinRequest):
    """
    Allows a friend to join a group Blend room with their personal budget, style, and constraints.
    """
    try:
        session = blend_coordinator.join_session(request)
        if not session:
            raise HTTPException(status_code=404, detail="Blend room ID not found")
        return session
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.get("/{blend_id}", response_model=BlendSession)
def get_blend_room(blend_id: str):
    """
    Fetches the current status, member profiles, outfits, and harmony score of a Blend room.
    """
    session = blend_coordinator.get_session(blend_id)
    if not session:
        raise HTTPException(status_code=404, detail="Blend room not found")
    return session

@router.post("/{blend_id}/coordinate", response_model=BlendSession)
async def coordinate_blend_outfits(
    blend_id: str,
    force_fixture: Optional[str] = Query(None, description="Force fixture mode for testing")
):
    """
    Triggers the autonomous agent to harmonize outfits for all members in the room,
    strictly enforcing individual budgets while optimizing shared palette & formality.
    """
    session = await blend_coordinator.coordinate_outfits(blend_id, force_fixture=force_fixture)
    if not session:
        raise HTTPException(status_code=404, detail="Blend room not found")
    return session

@router.post("/swap", response_model=BlendSession)
async def swap_blend_item(
    request: BlendSwapRequest,
    force_fixture: Optional[str] = Query(None, description="Force fixture mode for testing")
):
    """
    Human-in-the-loop item critique and swap for a specific member in a Blend room.
    Replaces the rejected item, validates the member's budget, and recalculates group harmony.
    """
    session = await blend_coordinator.swap_member_item(request, force_fixture=force_fixture)
    if not session:
        raise HTTPException(status_code=404, detail="Blend room or member not found")
    return session

@router.post("/{blend_id}/members/{member_id}/swap", response_model=BlendSession)
async def swap_member_item_by_path(
    blend_id: str,
    member_id: str,
    request: BlendSwapRequest,
    force_fixture: Optional[str] = Query(None, description="Force fixture mode for testing")
):
    """Path-based alias for swapping an item for a specific member."""
    request.blend_id = blend_id
    request.member_id = member_id
    session = await blend_coordinator.swap_member_item(request, force_fixture=force_fixture)
    if not session:
        raise HTTPException(status_code=404, detail="Blend room or member not found")
    return session
