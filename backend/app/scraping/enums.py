from enum import StrEnum


class RunKind(StrEnum):
    AMAZON = "amazon"
    CATEGORIES = "categories"
    TRENDS = "trends"


class RunStatus(StrEnum):
    RUNNING = "running"
    SUCCESS = "success"
    BLOCKED = "blocked"
    FAILED = "failed"
