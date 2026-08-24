from collections.abc import Sequence

from app.products.enums import TrendDirection
from app.scoring.engine import ScoringEngine
from app.scoring.fallback import DeterministicScorer
from app.scoring.schemas import BoostMatch, LLMVerdict, ScoringInput


def make_input(asin: str) -> ScoringInput:
    return ScoringInput(
        asin=asin,
        title="Garden Hose",
        category="lawn-garden",
        price=29.99,
        rating=4.6,
        reviews_count=8400,
        bestseller_rank=3,
        trend_direction=TrendDirection.RISING,
        trend_latest_value=88,
        boost=BoostMatch(points=0, matched_titles=(), category_hit=False),
    )


class StubScorer:
    def __init__(self, verdicts: list[LLMVerdict]) -> None:
        self._verdicts = verdicts

    async def score_batch(self, items: Sequence[ScoringInput]) -> list[LLMVerdict]:
        return self._verdicts


async def test_engine_accepts_exact_structured_batch() -> None:
    items = [make_input("B00TEST001"), make_input("B00TEST002")]
    verdicts = [
        LLMVerdict(asin=item.asin, score=80, reasoning="Strong demand; manageable risk.")
        for item in items
    ]
    engine = ScoringEngine(DeterministicScorer(), StubScorer(verdicts), "test", 10)

    results = await engine.score(items)

    assert [result.source for result in results] == ["llm:test", "llm:test"]


async def test_engine_rejects_missing_or_reordered_verdicts() -> None:
    items = [make_input("B00TEST001"), make_input("B00TEST002")]
    verdicts = [
        LLMVerdict(asin=items[1].asin, score=80, reasoning="Strong demand; manageable risk."),
        LLMVerdict(asin=items[0].asin, score=80, reasoning="Strong demand; manageable risk."),
    ]
    engine = ScoringEngine(DeterministicScorer(), StubScorer(verdicts), "test", 10)

    results = await engine.score(items)

    assert [result.source for result in results] == ["fallback", "fallback"]
