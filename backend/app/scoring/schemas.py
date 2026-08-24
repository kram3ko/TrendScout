from dataclasses import dataclass

from pydantic import BaseModel, Field

from app.products.enums import TrendDirection

SCORE_MIN = 0
SCORE_MAX = 100


@dataclass(frozen=True, slots=True)
class BoostMatch:
    """Why a product earned internal boost — carried into the reasoning text."""

    points: float
    matched_titles: tuple[str, ...]
    category_hit: bool

    @property
    def explanation(self) -> str:
        if not self.points:
            return "no overlap with our past winners"
        reason = "same category as" if self.category_hit else "keyword overlap with"
        return f"{reason} {', '.join(self.matched_titles)}"


@dataclass(frozen=True, slots=True)
class ScoringInput:
    asin: str
    title: str
    category: str
    price: float | None
    rating: float | None
    reviews_count: int | None
    bestseller_rank: int | None
    trend_direction: TrendDirection
    trend_latest_value: int | None
    boost: BoostMatch


@dataclass(frozen=True, slots=True)
class ScoreResult:
    asin: str
    score: int
    reasoning: str
    source: str


class LLMVerdict(BaseModel):
    """Structured output contract shared by every provider."""

    asin: str
    score: int = Field(ge=SCORE_MIN, le=SCORE_MAX)
    reasoning: str = Field(min_length=1, max_length=600)


class LLMVerdictBatch(BaseModel):
    verdicts: list[LLMVerdict] = Field(min_length=1, max_length=25)
