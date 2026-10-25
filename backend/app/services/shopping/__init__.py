from typing import Optional
from app.config import settings
from app.services.shopping.base import IProductSearchProvider
from app.services.shopping.serpapi_provider import SerpApiShoppingProvider
from app.services.shopping.fixture_provider import ControlledFixtureProvider

def get_shopping_provider(force_mode: Optional[str] = None) -> IProductSearchProvider:
    """
    Returns the appropriate shopping provider instance based on settings or explicit test flags.
    """
    mode = force_mode or settings.provider_mode

    if mode == "fixture" or not settings.serpapi_api_key:
        return ControlledFixtureProvider()
    
    if mode == "live" or mode == "hybrid":
        return SerpApiShoppingProvider(api_key=settings.serpapi_api_key)

    return ControlledFixtureProvider()
