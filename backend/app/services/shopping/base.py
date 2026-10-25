from abc import ABC, abstractmethod
from typing import List, Optional
from app.models.schemas import ProductItem

class ShoppingProviderError(Exception):
    """Raised when an external shopping provider encounters an API error, rate limit, or network failure."""
    pass

class IProductSearchProvider(ABC):
    """
    Provider-independent contract for discovering real clothing items.
    Allows transparent switching between SerpApi (Google Shopping India),
    future retailer APIs, or offline fixtures.
    """

    @abstractmethod
    async def search_products(
        self,
        query: str,
        category: str,
        gender: str = "men",
        max_price: Optional[float] = None,
        color: Optional[str] = None,
        limit: int = 6
    ) -> List[ProductItem]:
        """
        Execute product search and return standardized ProductItem list.
        """
        pass

    @abstractmethod
    async def get_product_details(self, product_id: str, product_url: str) -> Optional[ProductItem]:
        """
        Fetch enriched details for a specific product.
        """
        pass
