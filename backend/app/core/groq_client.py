"""Groq API client with retry/backoff and structured JSON output."""
import asyncio
import json
from typing import Type, TypeVar
from pydantic import BaseModel, ValidationError
from groq import Groq, RateLimitError, APIError
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)
T = TypeVar("T", bound=BaseModel)

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=settings.GROQ_API_KEY)
    return _client


def _model_name(model: str) -> str:
    if model == "reasoning":
        return settings.GROQ_MODEL_REASONING
    if model == "classify":
        return settings.GROQ_MODEL_CLASSIFY
    return model


async def groq_json(
    prompt: str,
    response_model: Type[T],
    model: str = "reasoning",
    system: str = "You are a helpful legal information assistant. Always respond with valid JSON.",
    max_retries: int = 2,
) -> T:
    """Call Groq and parse structured JSON into a Pydantic model. Retries on rate limit or validation error."""
    client = _get_client()
    model_name = _model_name(model)

    for attempt in range(max_retries):
        try:
            # Exponential backoff on retry
            if attempt > 0:
                await asyncio.sleep(2 ** attempt)

            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.1,
                max_tokens=2048,
            )
            raw = completion.choices[0].message.content or "{}"

            try:
                return response_model.model_validate_json(raw)
            except ValidationError as ve:
                logger.warning("groq_validation_error", attempt=attempt, error=str(ve))
                if attempt == max_retries - 1:
                    raise

        except RateLimitError:
            logger.warning("groq_rate_limit", attempt=attempt, model=model_name)
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(4 * (attempt + 1))

        except APIError as exc:
            logger.error("groq_api_error", error=str(exc))
            raise

    raise RuntimeError("groq_json: all retries exhausted")


async def groq_text(
    prompt: str,
    model: str = "reasoning",
    system: str = "You are a helpful legal information assistant.",
) -> str:
    """Call Groq and return plain text."""
    client = _get_client()
    model_name = _model_name(model)
    for attempt in range(2):
        try:
            if attempt > 0:
                await asyncio.sleep(2 ** attempt)
            completion = client.chat.completions.create(
                model=model_name,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.2,
                max_tokens=1024,
            )
            return completion.choices[0].message.content or ""
        except RateLimitError:
            if attempt == 1:
                raise
            await asyncio.sleep(4)
    return ""
