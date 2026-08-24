import pytest

from app.products.models import TrendDirection
from app.scoring.fallback import DeterministicScorer
from app.scoring.schemas import BoostMatch, ScoringInput

NO_BOOST = BoostMatch(points=0.0, matched_titles=(), category_hit=False)


def make_input(**overrides) -> ScoringInput:
    defaults = {
        "asin": "B00TEST0001",
        "title": "Expandable Garden Hose",
        "category": "lawn-garden",
        "price": 29.99,
        "rating": 4.6,
        "reviews_count": 8_400,
        "bestseller_rank": 3,
        "trend_direction": TrendDirection.RISING,
        "trend_latest_value": 88,
        "boost": NO_BOOST,
    }
    return ScoringInput(**(defaults | overrides))


@pytest.fixture
def scorer() -> DeterministicScorer:
    return DeterministicScorer()


def test_score_stays_within_bounds_for_an_empty_product(scorer):
    result = scorer.score(
        make_input(
            price=None,
            rating=None,
            reviews_count=None,
            bestseller_rank=None,
            trend_direction=TrendDirection.UNKNOWN,
            trend_latest_value=None,
        )
    )

    assert 0 <= result.score <= 100
    assert result.source == "fallback"


def test_rising_trend_outscores_falling_trend(scorer):
    rising = scorer.score(make_input(trend_direction=TrendDirection.RISING))
    falling = scorer.score(make_input(trend_direction=TrendDirection.FALLING))

    assert rising.score > falling.score


def test_boost_lifts_the_score_and_shows_up_in_the_reasoning(scorer):
    boost = BoostMatch(points=12.0, matched_titles=("Garden Hose Reel",), category_hit=True)

    boosted = scorer.score(make_input(boost=boost))
    plain = scorer.score(make_input())

    assert boosted.score == plain.score + 12
    assert "Garden Hose Reel" in boosted.reasoning


def test_price_outside_the_margin_band_scores_lower(scorer):
    in_band = scorer.score(make_input(price=29.99))
    too_cheap = scorer.score(make_input(price=3.0))

    assert in_band.score > too_cheap.score


def test_reasoning_names_the_concrete_signals(scorer):
    reasoning = scorer.score(make_input()).reasoning

    assert "8,400 reviews" in reasoning
    assert "#3 in lawn-garden" in reasoning
    assert reasoning.endswith(".")
