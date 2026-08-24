from collections.abc import Sequence

from google import genai
from google.genai import types

from app.scoring.llm.base import LLMUnavailableError
from app.scoring.llm.prompts import SYSTEM_PROMPT, build_user_prompt
from app.scoring.schemas import LLMVerdict, LLMVerdictBatch, ScoringInput

JSON_MIME_TYPE = "application/json"


class GeminiScorer:
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model
        self._config = types.GenerateContentConfig(
            system_instruction=SYSTEM_PROMPT,
            response_mime_type=JSON_MIME_TYPE,
            response_schema=LLMVerdictBatch,
        )

    async def score_batch(self, items: Sequence[ScoringInput]) -> list[LLMVerdict]:
        response = await self._client.aio.models.generate_content(
            model=self._model, contents=build_user_prompt(items), config=self._config
        )
        parsed = response.parsed
        if not isinstance(parsed, LLMVerdictBatch):
            raise LLMUnavailableError("gemini returned no parsable verdicts")
        return parsed.verdicts
