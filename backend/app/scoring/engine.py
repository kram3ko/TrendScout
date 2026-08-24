import logging
from collections.abc import Sequence

from app.scoring.fallback import DeterministicScorer
from app.scoring.llm.base import LLMScorer
from app.scoring.schemas import SCORE_MAX, SCORE_MIN, LLMVerdict, ScoreResult, ScoringInput

logger = logging.getLogger(__name__)

LLM_SOURCE_TEMPLATE = "llm:{provider}"


class ScoringEngine:
    """Turns product facts into a score, with the LLM as an upgrade, not a dependency.

    A provider failure — exhausted free-tier quota, a network blip, an answer that
    does not fit the schema — degrades that batch to the deterministic formula
    instead of failing the run, which is the same contract as running with no key.
    """

    def __init__(
        self,
        fallback: DeterministicScorer,
        scorer: LLMScorer | None,
        provider: str,
        batch_size: int,
    ) -> None:
        self._fallback = fallback
        self._scorer = scorer
        self._source = LLM_SOURCE_TEMPLATE.format(provider=provider)
        self._batch_size = batch_size

    async def score(self, items: Sequence[ScoringInput]) -> list[ScoreResult]:
        if self._scorer is None:
            return [self._fallback.score(item) for item in items]

        results: list[ScoreResult] = []
        batches = [
            items[start : start + self._batch_size]
            for start in range(0, len(items), self._batch_size)
        ]
        for batch in batches:
            results.extend(await self._score_batch(self._scorer, batch))
        return results

    async def _score_batch(
        self, scorer: LLMScorer, batch: Sequence[ScoringInput]
    ) -> list[ScoreResult]:
        try:
            verdicts = await scorer.score_batch(batch)
            expected = [item.asin for item in batch]
            received = [verdict.asin for verdict in verdicts]
            if received != expected:
                raise ValueError(
                    f"LLM verdict ASIN sequence mismatch: expected {expected}, received {received}"
                )
        except Exception as error:
            logger.warning("LLM batch failed, falling back to formula: %s", error)
            return [self._fallback.score(item) for item in batch]

        return [self._merge(item, verdict) for item, verdict in zip(batch, verdicts, strict=True)]

    def _merge(self, item: ScoringInput, verdict: LLMVerdict | None) -> ScoreResult:
        if verdict is None:
            return self._fallback.score(item)
        return ScoreResult(
            asin=item.asin,
            score=min(max(verdict.score, SCORE_MIN), SCORE_MAX),
            reasoning=verdict.reasoning,
            source=self._source,
        )
