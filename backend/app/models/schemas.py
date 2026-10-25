from enum import Enum
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from pydantic import BaseModel, Field, field_validator

class GenderEnum(str, Enum):
    MEN = "men"
    WOMEN = "women"
    UNISEX = "unisex"

class DataSourceEnum(str, Enum):
    LIVE_VERIFIED = "live_verified"
    CACHED = "cached"
    CONTROLLED_FIXTURE = "controlled_fixture"

class ClothingCategory(str, Enum):
    TOP = "top"
    BOTTOM = "bottom"
    SHOES = "shoes"
    ACCESSORY = "accessory"
    OUTERWEAR = "outerwear"
    ETHNIC = "ethnic"

class ProductItem(BaseModel):
    id: str
    title: str
    brand: Optional[str] = "Fashion Collection"
    category: str # "top", "bottom", "shoes", "accessory", "outerwear", "ethnic"
    price_inr: float
    original_price_inr: Optional[float] = None
    merchant: str = "Myntra" # "Myntra", "Amazon.in", "Ajio", "Flipkart", "Zara India"
    product_url: str
    image_url: str
    rating: Optional[float] = 4.2
    reviews_count: Optional[int] = 120
    available_sizes: List[str] = ["S", "M", "L", "XL"]
    delivery_estimate: Optional[str] = "Delivery in 3-5 days"
    data_source: DataSourceEnum = DataSourceEnum.LIVE_VERIFIED
    retrieved_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class ConstraintType(str, Enum):
    BUDGET = "budget"
    SIZE_AVAILABILITY = "size_availability"
    DELIVERY_DEADLINE = "delivery_deadline"
    COLOR_HARMONY = "color_harmony"
    THEME_COHESION = "theme_cohesion"

class ConstraintStatus(str, Enum):
    PASSED = "PASSED"
    VIOLATED = "VIOLATED"
    REPAIRED = "REPAIRED"

class ConstraintEvaluation(BaseModel):
    constraint_type: ConstraintType
    status: ConstraintStatus
    details: str
    replan_triggered: bool = False
    target_value: Optional[Any] = None
    actual_value: Optional[Any] = None

class AgentPhase(str, Enum):
    UNDERSTAND_GOAL = "UNDERSTAND_GOAL"
    DECOMPOSE_PLAN = "DECOMPOSE_PLAN"
    SELECT_TOOL = "SELECT_TOOL"
    EXECUTE_TOOL = "EXECUTE_TOOL"
    EVALUATE_CONSTRAINTS = "EVALUATE_CONSTRAINTS"
    REPLAN = "REPLAN"
    SYNTHESIZE_EXPLANATION = "SYNTHESIZE_EXPLANATION"
    COMPLETED = "COMPLETED"

class AgentTraceStep(BaseModel):
    step_number: int
    phase: AgentPhase
    thought: str
    tool_called: Optional[str] = None
    tool_input: Optional[Dict[str, Any]] = None
    tool_output: Optional[Dict[str, Any]] = None
    constraint_check: Optional[ConstraintEvaluation] = None
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class OutfitRequest(BaseModel):
    user_id: str = "user_guest"
    occasion: str # e.g. "College Farewell", "Tech Conference", "Diwali Sangeet", "Casual Weekend"
    theme: str # e.g. "Minimalist Smart Casual", "Royal Ethnic Elegance", "Streetwear Edge"
    personal_style: str = "Modern tailored, understated luxury"
    gender: GenderEnum = GenderEnum.MEN
    sizes: Dict[str, str] = Field(default_factory=lambda: {"top": "M", "bottom": "32", "shoes": "UK 9"})
    budget_inr: float = 5000.0
    delivery_deadline: Optional[str] = None # e.g. "2026-11-05" or "5 days"
    color_preferences: List[str] = Field(default_factory=lambda: ["Navy", "Beige", "White"])
    avoid_colors: List[str] = Field(default_factory=lambda: ["Neon Green"])
    force_test_fixture: Optional[str] = None # e.g. "budget_overrun_scenario", "out_of_stock_scenario"

class AgentActionType(str, Enum):
    SEARCH_PRODUCTS = "search_products"
    VALIDATE_OUTFIT = "validate_outfit"
    GET_BUDGET_SUMMARY = "get_budget_summary"
    REPLAN = "replan"
    FINISH_PLAN = "finish_plan"

class SearchProductsArgs(BaseModel):
    query: str
    category: str # "top", "bottom", "shoes", "accessory", "outerwear", "ethnic"
    gender: str = "men"
    max_price: Optional[float] = None
    color: Optional[str] = None
    limit: int = 3

class ReplanArgs(BaseModel):
    violating_category: str
    reason: str
    target_sub_budget: float
    revised_search_query: str

class AgentStepDecision(BaseModel):
    thought: str = Field(description="Step-by-step reasoning about constraints, user occasion, and next move")
    action: AgentActionType = Field(description="The tool action to execute next")
    search_args: Optional[SearchProductsArgs] = None
    replan_args: Optional[ReplanArgs] = None
    finish_summary: Optional[str] = None

class CategoryBudget(BaseModel):
    category: str
    amount_inr: float

class CategoryQuery(BaseModel):
    category: str
    query: str

class InitialPlan(BaseModel):
    goal_understanding: str
    style_direction: str
    preferred_palette: List[str]
    required_categories: List[str]
    budget_allocation: List[CategoryBudget] = Field(default_factory=list)
    initial_search_queries: List[CategoryQuery] = Field(default_factory=list)
    first_action: AgentActionType = AgentActionType.SEARCH_PRODUCTS
    first_search_args: Optional[SearchProductsArgs] = None

    @field_validator('budget_allocation', mode='before')
    @classmethod
    def convert_budget_dict(cls, v):
        if isinstance(v, dict):
            return [{"category": k, "amount_inr": float(val)} for k, val in v.items()]
        return v

    @field_validator('initial_search_queries', mode='before')
    @classmethod
    def convert_queries_dict(cls, v):
        if isinstance(v, dict):
            return [{"category": k, "query": str(val)} for k, val in v.items()]
        return v

class FinalStylistResponse(BaseModel):
    stylist_rationale: str
    harmony_score: float = 94.0
    tradeoffs_considered: List[str] = []
    styling_tips: List[str] = []

class OutfitRecommendation(BaseModel):
    outfit_id: str
    user_id: str
    occasion: str
    theme: str
    items: List[ProductItem]
    total_price_inr: float
    target_budget_inr: float
    is_within_budget: bool
    harmony_score: float = 92.0 # 0-100
    stylist_rationale: str
    tradeoffs_considered: List[str] = []
    trace_steps: List[AgentTraceStep] = []
    visualization_url: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    orchestration_engine: str = "deterministic_fallback" # "gemini" | "deterministic_fallback"
    status: str = "complete" # "complete" | "partial" | "failed" | "deadline_exceeded"
    data_source_mode: DataSourceEnum = DataSourceEnum.LIVE_VERIFIED
    error_message: Optional[str] = None

class UserFeedbackRequest(BaseModel):
    outfit_id: str
    accepted: bool
    rating: int = Field(default=4, ge=1, le=5)
    rejected_item_ids: List[str] = []
    feedback_text: str = "" # e.g., "Love the blazer, but the shoes are too formal. Can I have clean white sneakers?"

class HarmonyScoreBreakdown(BaseModel):
    overall_score: float = Field(..., ge=0.0, le=100.0)
    palette_harmony: float = Field(..., ge=0.0, le=100.0)
    formality_consistency: float = Field(..., ge=0.0, le=100.0)
    budget_compliance: float = Field(..., ge=0.0, le=100.0)
    category_completeness: float = Field(..., ge=0.0, le=100.0)
    preference_adherence: float = Field(..., ge=0.0, le=100.0)
    summary_notes: List[str] = Field(default_factory=list)
    is_provisional: bool = False

class BlendMember(BaseModel):
    user_id: str
    display_name: str
    budget_inr: float
    gender: GenderEnum
    sizes: Dict[str, str] = Field(default_factory=dict)
    personal_style: str = "Smart Casual"
    preferred_colors: List[str] = Field(default_factory=list)
    avoid_colors: List[str] = Field(default_factory=list)
    required_categories: List[str] = Field(default_factory=lambda: ["top", "bottom", "shoes"])
    recommended_outfit: Optional[OutfitRecommendation] = None
    status: str = "joined" # "joined", "generating", "ready", "partial", "failed"
    is_valid: bool = True
    unresolved_constraints: List[str] = Field(default_factory=list)

class BlendSession(BaseModel):
    blend_id: str
    title: str
    occasion: str
    shared_theme: str
    shared_palette: List[str]
    event_date: Optional[str] = None
    created_by: str
    members: List[BlendMember] = Field(default_factory=list)
    group_cohesion_score: float = 0.0
    score_breakdown: Optional[HarmonyScoreBreakdown] = None
    harmonization_summary: str = ""
    trace_steps: List[AgentTraceStep] = Field(default_factory=list)
    status: str = "draft" # "draft", "coordinating", "ready", "partial", "failed"
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

class BlendCreateRequest(BaseModel):
    title: str
    occasion: str
    shared_theme: str
    shared_palette: List[str] = ["Navy", "Champagne Gold", "Ivory"]
    event_date: Optional[str] = None
    host_name: str = "Arjun"
    host_budget_inr: float = 5000.0
    host_style: str = "Tailored smart casual"
    host_gender: GenderEnum = GenderEnum.MEN
    host_sizes: Dict[str, str] = Field(default_factory=lambda: {"top": "M", "bottom": "32", "shoes": "UK 9"})
    host_preferred_colors: List[str] = Field(default_factory=list)
    host_avoid_colors: List[str] = Field(default_factory=list)
    host_required_categories: List[str] = Field(default_factory=lambda: ["top", "bottom", "shoes"])

class BlendJoinRequest(BaseModel):
    blend_id: str
    member_name: str
    member_budget_inr: float = 3500.0
    member_style: str = "Indo-Western ethnic fusion"
    member_gender: GenderEnum = GenderEnum.WOMEN
    member_sizes: Dict[str, str] = Field(default_factory=lambda: {"top": "S", "bottom": "28", "shoes": "UK 5"})
    preferred_colors: List[str] = Field(default_factory=list)
    avoid_colors: List[str] = Field(default_factory=list)
    required_categories: List[str] = Field(default_factory=lambda: ["top", "bottom", "shoes"])

class BlendSwapRequest(BaseModel):
    blend_id: str
    member_id: str
    rejected_item_id: str
    feedback_text: str = "" # e.g., "Loafers too formal, swap for white casual court sneakers under 2000"
    target_category: Optional[str] = None
    preferred_color: Optional[str] = None
    max_price_inr: Optional[float] = None

