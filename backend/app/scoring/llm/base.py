from collections.abc import Sequence
from typing import Protocol

from app.scoring.schemas import LLMVerdict, ScoringInput


class LLMUnavailableError(RuntimeError):
    """Provider refused the batch — quota, network or an unusable answer."""


class LLMScorer(Protocol):
    """One batch of products in, one verdict per product out.

    Batching is not an optimisation detail: at ~120 products per run and a
    free-tier quota measured in hundreds of calls per day, per-product requests
    exhaust the key on the first day.
    """

    async def score_batch(self, items: Sequence[ScoringInput]) -> list[LLMVerdict]: ...
