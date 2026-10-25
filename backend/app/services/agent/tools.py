from typing import List, Dict, Any, Optional
from app.models.schemas import ProductItem, ConstraintEvaluation
from app.services.shopping.base import IProductSearchProvider
from app.services.agent.constraints import ConstraintEngine

class AgentTools:
    """
    Structured tool implementations available to the Agentic Orchestrator.
    """

    def __init__(self, provider: IProductSearchProvider):
        self.provider = provider
        self.constraints = ConstraintEngine()

    async def search_products(
        self,
        query: str,
        category: str,
        gender: str = "men",
        max_price: Optional[float] = None,
        color: Optional[str] = None,
        limit: int = 4
    ) -> List[ProductItem]:
        """
        Tool: Search real clothing products across supported stores.
        """
        return await self.provider.search_products(
            query=query,
            category=category,
            gender=gender,
            max_price=max_price,
            color=color,
            limit=limit
        )

    def calculate_outfit_budget(
        self,
        items: List[ProductItem],
        target_budget: float
    ) -> ConstraintEvaluation:
        """
        Tool: Calculate exact outfit price in INR and evaluate budget compliance.
        """
        return self.constraints.evaluate_budget(items, target_budget)

    def check_availability_and_sizes(
        self,
        items: List[ProductItem],
        sizes: Dict[str, str]
    ) -> ConstraintEvaluation:
        """
        Tool: Validate that all pieces are available in the user's specific sizing.
        """
        return self.constraints.evaluate_sizes(items, sizes)

    def evaluate_outfit_compatibility(
        self,
        items: List[ProductItem],
        occasion: str,
        theme: str,
        palette: List[str]
    ) -> Dict[str, Any]:
        """
        Tool: Evaluate color harmony and stylistic cohesion for the target occasion.
        """
        return self.constraints.evaluate_color_and_theme(items, occasion, theme, palette)
