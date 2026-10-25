import re
from typing import List, Dict, Any, Optional, Set
from app.models.schemas import (
    BlendMember,
    BlendSession,
    ProductItem,
    HarmonyScoreBreakdown
)

NEUTRAL_COLORS = {
    "black", "white", "grey", "gray", "beige", "tan", "cream", "off-white", "ivory", "charcoal", "khaki"
}

FORMALITY_KEYWORDS = {
    "formal": {
        "positive": ["suit", "blazer", "tuxedo", "oxford", "trousers", "formal", "leather shoes", "brogue", "silk"],
        "negative": ["t-shirt", "tee", "hoodie", "shorts", "flip-flop", "sandal", "tracksuit", "joggers"]
    },
    "smart_casual": {
        "positive": ["blazer", "chinos", "oxford", "polo", "loafers", "chelsea", "derby", "tailored", "shirt"],
        "negative": ["flip-flop", "athletic", "gym", "tracksuit", "distressed"]
    },
    "festive": {
        "positive": ["kurta", "anarkali", "sherwani", "lehenga", "saree", "mojari", "jooti", "silk", "embellished", "ethnic", "bandhgala", "nehru jacket"],
        "negative": ["hoodie", "gym", "athletic", "distressed denim", "cargo shorts"]
    },
    "casual": {
        "positive": ["t-shirt", "tee", "jeans", "sneakers", "denim", "polo", "casual", "canvas", "hoodie"],
        "negative": ["tuxedo", "sherwani", "cufflinks", "cummerbund"]
    }
}

class HarmonyEngine:
    """
    Deterministic, observable group harmony and fairness scoring engine for Blend.
    Evaluates 5 verifiable dimensions:
    1. Palette Harmony (30%)
    2. Formality & Occasion Consistency (20%)
    3. Individual Budget Compliance & Fairness (25%)
    4. Category Completeness (15%)
    5. Preference & Constraint Adherence (10%)
    """

    @classmethod
    def evaluate(
        cls,
        members: List[BlendMember],
        shared_theme: str,
        shared_palette: List[str],
        occasion: str
    ) -> HarmonyScoreBreakdown:
        if not members:
            return HarmonyScoreBreakdown(
                overall_score=0.0,
                palette_harmony=0.0,
                formality_consistency=0.0,
                budget_compliance=0.0,
                category_completeness=0.0,
                preference_adherence=0.0,
                summary_notes=["No members present in Blend room."],
                is_provisional=True
            )

        members_with_outfits = [m for m in members if m.recommended_outfit and m.recommended_outfit.items]
        if not members_with_outfits:
            return HarmonyScoreBreakdown(
                overall_score=0.0,
                palette_harmony=0.0,
                formality_consistency=0.0,
                budget_compliance=0.0,
                category_completeness=0.0,
                preference_adherence=0.0,
                summary_notes=["No outfits generated yet. Waiting for coordination."],
                is_provisional=True
            )

        # 1. Palette Harmony (30%)
        palette_score, palette_notes = cls._evaluate_palette(
            members_with_outfits, shared_palette
        )

        # 2. Formality & Occasion Consistency (20%)
        formality_score, formality_notes = cls._evaluate_formality(
            members_with_outfits, occasion, shared_theme
        )

        # 3. Individual Budget Compliance & Fairness (25%)
        budget_score, budget_notes, any_over_budget = cls._evaluate_budgets(
            members_with_outfits
        )

        # 4. Category Completeness (15%)
        completeness_score, completeness_notes, all_complete = cls._evaluate_completeness(
            members_with_outfits
        )

        # 5. Preference & Constraint Adherence (10%)
        preference_score, preference_notes = cls._evaluate_preferences(
            members_with_outfits
        )

        # Calculate weighted overall score
        raw_overall = (
            (0.30 * palette_score) +
            (0.20 * formality_score) +
            (0.25 * budget_score) +
            (0.15 * completeness_score) +
            (0.10 * preference_score)
        )

        # Rule: A high group score must NEVER hide an invalid or over-budget outfit
        # Cap overall score at 75 if any member's budget is violated or required categories missing
        if any_over_budget or not all_complete:
            final_overall = min(74.5, raw_overall)
        else:
            final_overall = min(100.0, max(0.0, raw_overall))

        final_overall = round(final_overall, 1)

        notes = []
        notes.extend(palette_notes)
        notes.extend(formality_notes)
        notes.extend(budget_notes)
        notes.extend(completeness_notes)
        notes.extend(preference_notes)

        is_provisional = len(members_with_outfits) < len(members)

        return HarmonyScoreBreakdown(
            overall_score=final_overall,
            palette_harmony=round(palette_score, 1),
            formality_consistency=round(formality_score, 1),
            budget_compliance=round(budget_score, 1),
            category_completeness=round(completeness_score, 1),
            preference_adherence=round(preference_score, 1),
            summary_notes=notes,
            is_provisional=is_provisional
        )

    @classmethod
    def _evaluate_palette(
        cls,
        members: List[BlendMember],
        shared_palette: List[str]
    ) -> tuple[float, List[str]]:
        normalized_palette = [c.lower().strip() for c in shared_palette if c]
        notes = []
        member_scores = []

        for m in members:
            items = m.recommended_outfit.items if m.recommended_outfit else []
            if not items:
                continue

            item_scores = []
            avoid_colors_lower = [c.lower().strip() for c in m.avoid_colors if c]

            for item in items:
                title_lower = item.title.lower()

                # Check if item has an avoided color (hard clash penalty)
                clashed_avoid = any(c in title_lower for c in avoid_colors_lower)
                if clashed_avoid:
                    item_scores.append(15.0)
                    notes.append(f"Clash alert: {m.display_name}'s '{item.title}' matches avoided color.")
                    continue

                # Check if matches shared palette
                matches_palette = any(c in title_lower for c in normalized_palette)
                if matches_palette:
                    item_scores.append(100.0)
                    continue

                # Check neutral harmonic support
                matches_neutral = any(n in title_lower for n in NEUTRAL_COLORS)
                if matches_neutral:
                    item_scores.append(88.0)
                    continue

                # Complementary or unspecified color
                item_scores.append(65.0)

            avg_m = sum(item_scores) / len(item_scores) if item_scores else 50.0
            member_scores.append(avg_m)

        if not member_scores:
            return 50.0, ["Insufficient color data."]

        avg_score = sum(member_scores) / len(member_scores)
        if avg_score >= 85:
            notes.append(f"Palette anchored in {', '.join(shared_palette)} with strong harmonic coherence.")
        else:
            notes.append("Moderate palette alignment with some neutral or complementary transitions.")

        return avg_score, notes

    @classmethod
    def _evaluate_formality(
        cls,
        members: List[BlendMember],
        occasion: str,
        theme: str
    ) -> tuple[float, List[str]]:
        occ_lower = f"{occasion} {theme}".lower()
        if any(k in occ_lower for k in ["wedding", "sangeet", "diwali", "festive", "traditional"]):
            target_formality = "festive"
        elif any(k in occ_lower for k in ["gala", "black tie", "farewell", "formal", "conference"]):
            target_formality = "formal"
        elif any(k in occ_lower for k in ["casual", "brunch", "trip", "vacation", "weekend"]):
            target_formality = "casual"
        else:
            target_formality = "smart_casual"

        rules = FORMALITY_KEYWORDS.get(target_formality, FORMALITY_KEYWORDS["smart_casual"])
        member_scores = []
        notes = []

        for m in members:
            items = m.recommended_outfit.items if m.recommended_outfit else []
            if not items:
                continue

            score = 80.0
            for item in items:
                title_lower = item.title.lower()
                if any(p in title_lower for p in rules["positive"]):
                    score += 6.0
                if any(n in title_lower for n in rules["negative"]):
                    score -= 20.0
                    notes.append(f"Formality clash: {m.display_name}'s '{item.title}' is discordant with {target_formality} dress code.")

            member_scores.append(max(20.0, min(100.0, score)))

        avg_score = sum(member_scores) / len(member_scores) if member_scores else 70.0
        notes.append(f"Target formality '{target_formality.replace('_', ' ').title()}' consistency: {round(avg_score)}%.")
        return avg_score, notes

    @classmethod
    def _evaluate_budgets(
        cls,
        members: List[BlendMember]
    ) -> tuple[float, List[str], bool]:
        member_scores = []
        notes = []
        any_over = False

        for m in members:
            outfit = m.recommended_outfit
            if not outfit:
                continue

            total = outfit.total_price_inr
            budget = m.budget_inr

            if total <= budget:
                savings = budget - total
                member_scores.append(100.0)
            else:
                any_over = True
                overrun = total - budget
                pct_over = (overrun / budget) * 100
                score = max(0.0, 100.0 - (pct_over * 1.5))
                member_scores.append(score)
                notes.append(f"Budget exceeded for {m.display_name}: Total INR {total:,.2f} > Budget INR {budget:,.2f} (+INR {overrun:,.2f}).")

        if not any_over:
            notes.append("100% budget adherence across all individual members.")

        avg_score = sum(member_scores) / len(member_scores) if member_scores else 100.0
        return avg_score, notes, any_over

    @classmethod
    def _evaluate_completeness(
        cls,
        members: List[BlendMember]
    ) -> tuple[float, List[str], bool]:
        member_scores = []
        notes = []
        all_complete = True

        for m in members:
            items = m.recommended_outfit.items if m.recommended_outfit else []
            cats = {item.category.lower() for item in items}
            titles = " ".join(item.title.lower() for item in items)

            reqs = m.required_categories or ["top", "bottom", "shoes"]
            missing = []

            for r in reqs:
                r_lower = r.lower()
                has_cat = r_lower in cats
                # Full body ethnic garments (anarkali, saree, kurta set) cover both top and bottom
                if r_lower in ["top", "bottom"] and any(e in titles for e in ["anarkali", "kurta set", "suit set", "saree", "lehenga"]):
                    has_cat = True

                if not has_cat:
                    missing.append(r)

            if not missing:
                member_scores.append(100.0)
            else:
                all_complete = False
                penalty = (len(missing) / len(reqs)) * 100
                member_scores.append(max(0.0, 100.0 - penalty))
                notes.append(f"{m.display_name} missing required piece: {', '.join(missing)}.")

        avg_score = sum(member_scores) / len(member_scores) if member_scores else 100.0
        return avg_score, notes, all_complete

    @classmethod
    def _evaluate_preferences(
        cls,
        members: List[BlendMember]
    ) -> tuple[float, List[str]]:
        member_scores = []
        notes = []

        for m in members:
            items = m.recommended_outfit.items if m.recommended_outfit else []
            if not items:
                continue

            score = 85.0
            # Sizing satisfaction
            for item in items:
                req_size = m.sizes.get(item.category)
                if req_size and item.available_sizes:
                    has_size = any(req_size.lower() == s.lower() or req_size in s for s in item.available_sizes)
                    if has_size:
                        score += 3.0
                    else:
                        score -= 5.0

            # Style alignment
            style_lower = m.personal_style.lower()
            titles_lower = " ".join(item.title.lower() for item in items)
            if any(term in titles_lower for term in style_lower.split() if len(term) > 3):
                score += 5.0

            member_scores.append(min(100.0, max(40.0, score)))

        avg_score = sum(member_scores) / len(member_scores) if member_scores else 80.0
        return avg_score, notes
