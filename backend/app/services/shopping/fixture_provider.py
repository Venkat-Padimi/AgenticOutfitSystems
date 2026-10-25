from typing import List, Optional
import uuid
from app.models.schemas import ProductItem, DataSourceEnum
from app.services.shopping.base import IProductSearchProvider

# Curated dataset of real Indian e-commerce clothing items across categories
FIXTURE_CATALOG = [
    # TOPS & BLAZERS (Men)
    {
        "id": "top_m_01",
        "title": "Blackberrys Men Navy Blue Slim-Fit Single-Breasted Formal Blazer",
        "brand": "Blackberrys",
        "category": "top",
        "gender": "men",
        "price_inr": 4899.0, # Premium price - triggers budget overrun when paired with accessories under ₹5k
        "merchant": "Myntra",
        "product_url": "https://www.myntra.com/blazers/blackberrys/navy-slim-fit-blazer",
        "image_url": "https://images.unsplash.com/photo-1594938298603-c8148c4dae35?w=500",
        "rating": 4.6,
        "reviews_count": 312,
        "available_sizes": ["38", "40", "42"],
        "delivery_estimate": "Express Delivery in 2 days",
        "tags": ["navy", "blazer", "formal", "smart casual", "farewell", "party"]
    },
    {
        "id": "top_m_02",
        "title": "Rare Rabbit Men Solid Cotton Linen Relaxed Fit Smart Casual Blazer",
        "brand": "Rare Rabbit",
        "category": "top",
        "gender": "men",
        "price_inr": 2199.0, # Budget-friendly replan replacement!
        "merchant": "Ajio",
        "product_url": "https://www.ajio.com/rare-rabbit-solid-blazer",
        "image_url": "https://images.unsplash.com/photo-1507679799987-c73779587ccf?w=500",
        "rating": 4.4,
        "reviews_count": 184,
        "available_sizes": ["S", "M", "L", "XL"],
        "delivery_estimate": "Delivery in 3 days",
        "tags": ["navy", "blue", "blazer", "budget", "linen", "smart casual", "farewell"]
    },
    {
        "id": "top_m_03",
        "title": "Marks & Spencer Tailored Fit Pure Cotton Oxford Shirt - Crisp White",
        "brand": "Marks & Spencer",
        "category": "top",
        "gender": "men",
        "price_inr": 1499.0,
        "merchant": "Myntra",
        "product_url": "https://www.myntra.com/shirts/marks--spencer/white-oxford-shirt",
        "image_url": "https://images.unsplash.com/photo-1602810318383-e386cc2a3ccf?w=500",
        "rating": 4.5,
        "reviews_count": 420,
        "available_sizes": ["M", "L", "XL"],
        "delivery_estimate": "Free Delivery by Wednesday",
        "tags": ["white", "shirt", "formal", "clean", "minimalist"]
    },

    # BOTTOMS (Men)
    {
        "id": "bot_m_01",
        "title": "Arrow Men Beige Super Slim Fit Flat-Front Stretch Chinos",
        "brand": "Arrow",
        "category": "bottom",
        "gender": "men",
        "price_inr": 1299.0,
        "merchant": "Amazon India",
        "product_url": "https://www.amazon.in/dp/B08X9QWXYZ",
        "image_url": "https://images.unsplash.com/photo-1624378439575-d8705ad7ae80?w=500",
        "rating": 4.3,
        "reviews_count": 250,
        "available_sizes": ["30", "32", "34", "36"],
        "delivery_estimate": "Delivery in 2 days (Prime)",
        "tags": ["beige", "chinos", "trousers", "smart casual", "khaki"]
    },
    {
        "id": "bot_m_02",
        "title": "Louis Philippe Charcoal Grey Tailored Fit Pleated Formal Trousers",
        "brand": "Louis Philippe",
        "category": "bottom",
        "gender": "men",
        "price_inr": 1599.0,
        "merchant": "Flipkart",
        "product_url": "https://www.flipkart.com/louis-philippe-grey-trousers",
        "image_url": "https://images.unsplash.com/photo-1506630448388-4e683c67ddb0?w=500",
        "rating": 4.4,
        "reviews_count": 180,
        "available_sizes": ["32", "34", "36"],
        "delivery_estimate": "Delivery in 4 days",
        "tags": ["grey", "charcoal", "formal", "retro", "trousers"]
    },

    # SHOES (Men)
    {
        "id": "shoe_m_01",
        "title": "Hush Puppies Men Brown Leather Handcrafted Tassel Loafers",
        "brand": "Hush Puppies",
        "category": "shoes",
        "gender": "men",
        "price_inr": 1899.0,
        "merchant": "Tata CLiQ",
        "product_url": "https://www.tatacliq.com/hush-puppies-loafers",
        "image_url": "https://images.unsplash.com/photo-1533867617858-e7b97e060509?w=500",
        "rating": 4.6,
        "reviews_count": 98,
        "available_sizes": ["UK 8", "UK 9", "UK 10"],
        "delivery_estimate": "Delivery in 3 days",
        "tags": ["brown", "tan", "loafers", "formal", "shoes"]
    },
    {
        "id": "shoe_m_02",
        "title": "Puma Men White Rebound Clean Court Low-Top Sneakers",
        "brand": "Puma",
        "category": "shoes",
        "gender": "men",
        "price_inr": 1699.0,
        "merchant": "Myntra",
        "product_url": "https://www.myntra.com/casual-shoes/puma/white-court-sneakers",
        "image_url": "https://images.unsplash.com/photo-1549298916-b41d501d3772?w=500",
        "rating": 4.5,
        "reviews_count": 512,
        "available_sizes": ["UK 7", "UK 8", "UK 9", "UK 10"],
        "delivery_estimate": "Delivery in 2 days",
        "tags": ["white", "sneakers", "casual", "smart casual", "shoes"]
    },

    # WOMEN ETHNIC & SMART CASUAL (For Blend & Women Outfits)
    {
        "id": "top_w_01",
        "title": "W for Woman Navy & Champagne Embroidered Anarkali Kurta Set",
        "brand": "W for Woman",
        "category": "ethnic",
        "gender": "women",
        "price_inr": 2499.0,
        "merchant": "Myntra",
        "product_url": "https://www.myntra.com/kurta-sets/w/navy-embroidered-set",
        "image_url": "https://images.unsplash.com/photo-1610030469983-98e550d6193c?w=500",
        "rating": 4.7,
        "reviews_count": 340,
        "available_sizes": ["XS", "S", "M", "L"],
        "delivery_estimate": "Delivery in 2 days",
        "tags": ["navy", "gold", "champagne", "ethnic", "kurta", "wedding", "sangeet", "farewell"]
    },
    {
        "id": "top_w_02",
        "title": "Mango Women Pastel Ivory Tailored Oversized Structured Blazer",
        "brand": "Mango",
        "category": "top",
        "gender": "women",
        "price_inr": 2990.0,
        "merchant": "Myntra",
        "product_url": "https://www.myntra.com/blazers/mango/ivory-oversized-blazer",
        "image_url": "https://images.unsplash.com/photo-1539571696357-5a69c17a67c6?w=500",
        "rating": 4.6,
        "reviews_count": 140,
        "available_sizes": ["S", "M", "L"],
        "delivery_estimate": "Delivery in 3 days",
        "tags": ["ivory", "cream", "blazer", "smart casual", "party"]
    },
    {
        "id": "bot_w_01",
        "title": "Zara Women High-Waist Wide-Leg Pleated Trousers - Champagne Sand",
        "brand": "Zara India",
        "category": "bottom",
        "gender": "women",
        "price_inr": 1890.0,
        "merchant": "Zara India",
        "product_url": "https://www.zara.com/in/wide-leg-trousers",
        "image_url": "https://images.unsplash.com/photo-1551803091-e20673f15770?w=500",
        "rating": 4.5,
        "reviews_count": 89,
        "available_sizes": ["XS", "S", "M", "L"],
        "delivery_estimate": "Standard delivery (3 days)",
        "tags": ["champagne", "beige", "wide leg", "trousers"]
    },
    {
        "id": "shoe_w_01",
        "title": "Aldo Women Metallic Champagne Block Heel Ankle Strap Sandals",
        "brand": "Aldo",
        "category": "shoes",
        "gender": "women",
        "price_inr": 1999.0,
        "merchant": "Ajio Luxe",
        "product_url": "https://www.ajio.com/aldo-champagne-heels",
        "image_url": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=500",
        "rating": 4.7,
        "reviews_count": 76,
        "available_sizes": ["UK 4", "UK 5", "UK 6", "UK 7"],
        "delivery_estimate": "Express Delivery in 2 days",
        "tags": ["champagne", "gold", "metallic", "heels", "sandals", "shoes"]
    },
    {
        "id": "shoe_w_02",
        "title": "Catwalk Women Metallic Champagne Embellished Ethnic Mojaris",
        "brand": "Catwalk",
        "category": "shoes",
        "gender": "women",
        "price_inr": 899.0,
        "merchant": "Myntra",
        "product_url": "https://www.myntra.com/flats/catwalk/champagne-mojaris",
        "image_url": "https://images.unsplash.com/photo-1543163521-1bf539c55dd2?w=500",
        "rating": 4.5,
        "reviews_count": 210,
        "available_sizes": ["UK 4", "UK 5", "UK 6", "UK 7"],
        "delivery_estimate": "Delivery in 2 days",
        "tags": ["champagne", "gold", "ethnic", "mojaris", "flats", "shoes", "wedding", "sangeet"]
    },

    # ACCESSORIES
    {
        "id": "acc_01",
        "title": "Fossil Minimalist Stainless Steel Watch with Brown Leather Strap",
        "brand": "Fossil",
        "category": "accessory",
        "gender": "unisex",
        "price_inr": 1295.0,
        "merchant": "Amazon India",
        "product_url": "https://www.amazon.in/dp/B07TESTFOS",
        "image_url": "https://images.unsplash.com/photo-1524805444758-089113d48a6d?w=500",
        "rating": 4.6,
        "reviews_count": 410,
        "available_sizes": ["Free Size"],
        "delivery_estimate": "Free 1-Day Prime Delivery",
        "tags": ["watch", "leather", "brown", "accessory"]
    },
    {
        "id": "acc_02",
        "title": "H&M Men Textured Silk Blend Pocket Square & Lapel Pin Set",
        "brand": "H&M",
        "category": "accessory",
        "gender": "men",
        "price_inr": 499.0,
        "merchant": "Myntra",
        "product_url": "https://www.myntra.com/hm/pocket-square-set",
        "image_url": "https://images.unsplash.com/photo-1589756823695-278bc923f962?w=500",
        "rating": 4.3,
        "reviews_count": 88,
        "available_sizes": ["Free Size"],
        "delivery_estimate": "Delivery in 3 days",
        "tags": ["pocket square", "gold", "navy", "accessory"]
    }
]

class ControlledFixtureProvider(IProductSearchProvider):
    """
    Deterministic test fixture provider ensuring repeatable evaluation scenarios
    (e.g., budget overshoot triggers, out-of-stock replanning, and color coordination).
    """

    def __init__(self):
        self.catalog = FIXTURE_CATALOG

    async def search_products(
        self,
        query: str,
        category: str,
        gender: str = "men",
        max_price: Optional[float] = None,
        color: Optional[str] = None,
        limit: int = 6
    ) -> List[ProductItem]:
        query_words = set(query.lower().split())
        matched = []

        for entry in self.catalog:
            # Gender match (or unisex)
            if entry["gender"] not in [gender, "unisex"]:
                continue
            
            # Category match if specified
            if category and entry["category"] != category:
                # Allow ethnic as top for women
                if not (category == "top" and entry["category"] == "ethnic"):
                    continue

            # Color filter if specified
            if color:
                color_words = color.lower().split()
                has_color = any(
                    any(word in tag.lower() for word in color_words) for tag in entry["tags"]
                ) or any(word in entry["title"].lower() for word in color_words)
                if not has_color:
                    continue

            # Price filter if max_price is provided
            if max_price is not None and entry["price_inr"] > max_price:
                continue

            # Reconstruct ProductItem
            item = ProductItem(
                id=entry["id"],
                title=entry["title"],
                brand=entry["brand"],
                category=entry["category"],
                price_inr=entry["price_inr"],
                original_price_inr=round(entry["price_inr"] * 1.35, 0),
                merchant=entry["merchant"],
                product_url=entry["product_url"],
                image_url=entry["image_url"],
                rating=entry["rating"],
                reviews_count=entry["reviews_count"],
                available_sizes=entry["available_sizes"],
                delivery_estimate=entry["delivery_estimate"],
                data_source=DataSourceEnum.CONTROLLED_FIXTURE
            )
            matched.append(item)

        # Fallback if strict filter yields nothing
        if not matched:
            for entry in self.catalog:
                cat_match = entry["category"] == category or (category == "top" and entry["category"] == "ethnic")
                if cat_match and entry["gender"] in [gender, "unisex"]:
                    matched.append(ProductItem(
                        id=entry["id"],
                        title=entry["title"],
                        brand=entry["brand"],
                        category=entry["category"],
                        price_inr=entry["price_inr"],
                        original_price_inr=round(entry["price_inr"] * 1.25, 0),
                        merchant=entry["merchant"],
                        product_url=entry["product_url"],
                        image_url=entry["image_url"],
                        rating=entry["rating"],
                        reviews_count=entry["reviews_count"],
                        available_sizes=entry["available_sizes"],
                        delivery_estimate=entry["delivery_estimate"],
                        data_source=DataSourceEnum.CONTROLLED_FIXTURE
                    ))

        return matched[:limit]

    async def get_product_details(self, product_id: str, product_url: str) -> Optional[ProductItem]:
        for entry in self.catalog:
            if entry["id"] == product_id:
                return ProductItem(
                    id=entry["id"],
                    title=entry["title"],
                    brand=entry["brand"],
                    category=entry["category"],
                    price_inr=entry["price_inr"],
                    merchant=entry["merchant"],
                    product_url=entry["product_url"],
                    image_url=entry["image_url"],
                    rating=entry["rating"],
                    reviews_count=entry["reviews_count"],
                    available_sizes=entry["available_sizes"],
                    delivery_estimate=entry["delivery_estimate"],
                    data_source=DataSourceEnum.CONTROLLED_FIXTURE
                )
        return None
