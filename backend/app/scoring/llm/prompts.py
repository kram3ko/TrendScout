import json
from collections.abc import Sequence

from app.scoring.schemas import ScoringInput

SYSTEM_PROMPT = """You are a sourcing analyst at a dropshipping retailer.
Score each Amazon product on its potential as a product we should start reselling.

Weigh, in order of importance:
1. Google Trends direction for the product keyword — falling demand caps the score.
2. Internal boost: overlap with products we already sold successfully.
3. Rating combined with review volume — high rating on few reviews is unproven.
4. Price fit for resale margin: roughly $15-60 works, outside that shipping or
   customer hesitation eats the margin.
5. Bestseller rank within its category.

Reasoning rules: two or three sentences, plain business language, name the
concrete numbers that drove the score and the single biggest risk. Never
mention that you are an AI model or describe your scoring procedure.

Response contract: return exactly one verdict for every input product, in the
same order. Copy every ASIN exactly. Never omit, duplicate, invent, or alter an
ASIN."""

USER_PROMPT_TEMPLATE = "Score these {count} products:\n\n{payload}"


def build_user_prompt(items: Sequence[ScoringInput]) -> str:
    payload: list[dict[str, object]] = [
        {
            "asin": item.asin,
            "title": item.title,
            "category": item.category,
            "price_usd": item.price,
            "rating": item.rating,
            "reviews_count": item.reviews_count,
            "bestseller_rank": item.bestseller_rank,
            "google_trend": item.trend_direction.value,
            "trend_latest_value": item.trend_latest_value,
            "internal_boost_points": item.boost.points,
            "internal_boost_reason": item.boost.explanation,
        }
        for item in items
    ]
    return USER_PROMPT_TEMPLATE.format(
        count=len(items), payload=json.dumps(payload, ensure_ascii=False, indent=2)
    )
