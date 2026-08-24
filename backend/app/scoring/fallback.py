import math

from app.products.enums import TrendDirection
from app.scoring.schemas import SCORE_MAX, SCORE_MIN, ScoreResult, ScoringInput

SOURCE = "fallback"

# Weights sum to 80; the remaining 20 come from the Internal Sales Boost.
RATING_WEIGHT = 25.0
REVIEWS_WEIGHT = 20.0
TREND_WEIGHT = 25.0
RANK_WEIGHT = 5.0
PRICE_WEIGHT = 5.0

MAX_RATING = 5.0
# 10k reviews is where the log curve saturates: beyond it, more reviews say
# "mature listing", not "more potential".
REVIEWS_SATURATION = 10_000
# Amazon shows 30 bestsellers per page, so rank 1 and rank 30 must stay distinguishable.
RANK_SATURATION = 30
# Dropshipping margin band — cheap items drown in shipping, expensive ones stall.
PRICE_SWEET_SPOT = (15.0, 60.0)

TREND_FRACTION = {
    TrendDirection.RISING: 1.0,
    TrendDirection.FLAT: 0.5,
    TrendDirection.FALLING: 0.15,
    TrendDirection.UNKNOWN: 0.4,
}
TREND_PHRASE = {
    TrendDirection.RISING: "search demand is rising",
    TrendDirection.FLAT: "search demand is stable",
    TrendDirection.FALLING: "search demand is falling",
    TrendDirection.UNKNOWN: "no trend data yet",
}


class DeterministicScorer:
    """Scoring without an LLM: the no-API-key path and the quota-exhausted path.

    Every component is worded in the reasoning so a buyer sees what moved the
    number, not just the number.
    """

    def score(self, item: ScoringInput) -> ScoreResult:
        rating = _rating_points(item.rating)
        reviews = _reviews_points(item.reviews_count)
        trend = TREND_WEIGHT * TREND_FRACTION[item.trend_direction]
        rank = _rank_points(item.bestseller_rank)
        price = _price_points(item.price)

        total = rating + reviews + trend + rank + price + item.boost.points
        return ScoreResult(
            asin=item.asin,
            score=round(min(max(total, SCORE_MIN), SCORE_MAX)),
            reasoning=_explain(item, rating, reviews, trend, price),
            source=SOURCE,
        )


def _rating_points(rating: float | None) -> float:
    return RATING_WEIGHT * (rating / MAX_RATING) if rating else 0.0


def _reviews_points(reviews_count: int | None) -> float:
    if not reviews_count:
        return 0.0
    saturated = min(reviews_count, REVIEWS_SATURATION)
    return REVIEWS_WEIGHT * math.log1p(saturated) / math.log1p(REVIEWS_SATURATION)


def _rank_points(bestseller_rank: int | None) -> float:
    if not bestseller_rank:
        return 0.0
    return RANK_WEIGHT * max(RANK_SATURATION - bestseller_rank + 1, 0) / RANK_SATURATION


def _price_points(price: float | None) -> float:
    if price is None:
        return 0.0
    low, high = PRICE_SWEET_SPOT
    if low <= price <= high:
        return PRICE_WEIGHT
    distance = low - price if price < low else price - high
    return max(PRICE_WEIGHT - distance / low * PRICE_WEIGHT, 0.0)


def _explain(item: ScoringInput, rating: float, reviews: float, trend: float, price: float) -> str:
    parts = [TREND_PHRASE[item.trend_direction]]

    if item.rating and item.reviews_count:
        parts.append(f"rated {item.rating} from {item.reviews_count:,} reviews")
    elif item.rating:
        parts.append(f"rated {item.rating} with little review history")
    else:
        parts.append("no ratings yet")

    if item.price is None:
        parts.append("price not listed on the bestseller page")
    elif price == PRICE_WEIGHT:
        parts.append(f"${item.price:.2f} sits in the resale margin band")
    else:
        parts.append(f"${item.price:.2f} is outside the usual margin band")

    if item.bestseller_rank:
        parts.append(f"ranked #{item.bestseller_rank} in {item.category}")

    parts.append(item.boost.explanation)

    weakest = min(
        (rating, "rating"), (reviews, "review volume"), (trend, "trend"), key=lambda pair: pair[0]
    )[1]
    sentence = "; ".join(parts)
    return f"{sentence[:1].upper()}{sentence[1:]}. Weakest signal: {weakest}."
