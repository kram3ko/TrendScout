from enum import StrEnum


class TrendDirection(StrEnum):
    RISING = "rising"
    FLAT = "flat"
    FALLING = "falling"
    UNKNOWN = "unknown"


class ProductSort(StrEnum):
    SCORE = "score"
    RANK = "rank"
    RECENT = "recent"
