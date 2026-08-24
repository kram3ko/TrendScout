from app.core.config import LLMProvider, Settings
from app.scoring.llm.anthropic_scorer import AnthropicScorer
from app.scoring.llm.base import LLMScorer
from app.scoring.llm.gemini_scorer import GeminiScorer
from app.scoring.llm.openai_scorer import OpenAIScorer

_SCORERS: dict[LLMProvider, type[AnthropicScorer | GeminiScorer | OpenAIScorer]] = {
    LLMProvider.GEMINI: GeminiScorer,
    LLMProvider.ANTHROPIC: AnthropicScorer,
    LLMProvider.OPENAI: OpenAIScorer,
}


def build_scorer(settings: Settings) -> LLMScorer | None:
    """None means the deterministic path: no provider selected or no key supplied."""
    if not settings.llm_enabled:
        return None
    return _SCORERS[settings.llm_provider](settings.llm_api_key, settings.llm_model)
