from collections.abc import Sequence

from openai import AsyncOpenAI

from app.scoring.llm.base import LLMUnavailableError
from app.scoring.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.scoring.schemas import LLMVerdict, LLMVerdictBatch, ScoringInput


class OpenAIScorer:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key)
        self._model = model

    async def score_batch(self, items: Sequence[ScoringInput]) -> list[LLMVerdict]:
        response = await self._client.responses.parse(
            model=self._model,
            instructions=SYSTEM_PROMPT,
            input=build_user_prompt(items),
            text_format=LLMVerdictBatch,
        )
        if response.output_parsed is None:
            raise LLMUnavailableError("openai returned no parsable verdicts")
        return response.output_parsed.verdicts
