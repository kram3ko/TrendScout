from enum import StrEnum


class LLMProvider(StrEnum):
    GEMINI = "gemini"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    NONE = "none"
