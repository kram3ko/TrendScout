from collections.abc import Sequence

from anthropic import AsyncAnthropic

from app.scoring.llm.base import LLMUnavailableError
from app.scoring.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.scoring.schemas import LLMVerdict, LLMVerdictBatch, ScoringInput

MAX_TOKENS = 8_000


class AnthropicScorer:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncAnthropic(api_key=api_key)
        self._model = model

    async def score_batch(self, items: Sequence[ScoringInput]) -> list[LLMVerdict]:
        message = await self._client.messages.parse(
            model=self._model,
            max_tokens=MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": build_user_prompt(items)}],
            output_format=LLMVerdictBatch,
        )
        for block in message.content:
            if block.type == "text" and isinstance(block.parsed_output, LLMVerdictBatch):
                return block.parsed_output.verdicts
        raise LLMUnavailableError(f"anthropic stopped with {message.stop_reason}")
