export type Gender = 'men' | 'women' | 'unisex';

export type DataSource = 'live_verified' | 'cached' | 'controlled_fixture';

export interface ProductItem {
  id: string;
  title: string;
  brand?: string;
  category: string;
  price_inr: number;
  original_price_inr?: number;
  merchant: string;
  product_url: string;
  image_url: string;
  rating?: number;
  reviews_count?: number;
  available_sizes: string[];
  delivery_estimate?: string;
  data_source: DataSource;
  retrieved_at: string;
}

export type ConstraintStatus = 'PASSED' | 'VIOLATED' | 'REPAIRED';

export interface ConstraintEvaluation {
  constraint_type: string;
  status: ConstraintStatus;
  details: string;
  replan_triggered: boolean;
  target_value?: any;
  actual_value?: any;
}

export type AgentPhase =
  | 'UNDERSTAND_GOAL'
  | 'DECOMPOSE_PLAN'
  | 'SELECT_TOOL'
  | 'EXECUTE_TOOL'
  | 'EVALUATE_CONSTRAINTS'
  | 'REPLAN'
  | 'SYNTHESIZE_EXPLANATION'
  | 'COMPLETED';

export interface AgentTraceStep {
  step_number: number;
  phase: AgentPhase;
  thought: string;
  tool_called?: string;
  tool_input?: Record<string, any>;
  tool_output?: Record<string, any>;
  constraint_check?: ConstraintEvaluation;
  timestamp: string;
}

export interface OutfitRecommendation {
  outfit_id: string;
  user_id: string;
  occasion: string;
  theme: string;
  items: ProductItem[];
  total_price_inr: number;
  target_budget_inr: number;
  is_within_budget: boolean;
  harmony_score: number;
  stylist_rationale: string;
  tradeoffs_considered: string[];
  trace_steps: AgentTraceStep[];
  visualization_url?: string;
  created_at: string;
}

export interface BlendMember {
  user_id: string;
  display_name: string;
  budget_inr: number;
  gender: Gender;
  sizes: Record<string, string>;
  personal_style: string;
  recommended_outfit?: OutfitRecommendation;
  status: 'joined' | 'generating' | 'ready';
}

export interface BlendSession {
  blend_id: string;
  title: string;
  occasion: string;
  shared_theme: string;
  shared_palette: string[];
  event_date?: string;
  created_by: string;
  members: BlendMember[];
  group_cohesion_score: number;
  harmonization_summary: string;
  created_at: string;
}
