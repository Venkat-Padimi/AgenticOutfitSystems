from typing import Optional, List
from fastapi import APIRouter, Query
from app.models.schemas import ProductItem
from app.services.shopping import get_shopping_provider

router = APIRouter(prefix="/api/v1/products", tags=["Shopping Discovery"])

@router.get("/search", response_model=List[ProductItem])
async def search_products(
    q: str = Query(..., description="Search query string"),
    category: str = Query("top", description="top, bottom, shoes, ethnic, accessory"),
    gender: str = Query("men", description="men, women, unisex"),
    max_price: Optional[float] = Query(None, description="Max price filter in INR"),
    color: Optional[str] = Query(None, description="Color tag filter"),
    mode: Optional[str] = Query(None, description="Force 'live' or 'fixture' mode")
):
    """
    Search real clothing products across supported Indian fashion retailers.
    """
    provider = get_shopping_provider(force_mode=mode)
    results = await provider.search_products(
        query=q,
        category=category,
        gender=gender,
        max_price=max_price,
        color=color,
        limit=6
    )
    return results
