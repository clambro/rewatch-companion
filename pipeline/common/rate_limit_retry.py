"""Pydantic AI capability for retrying model rate limits in-place."""

import asyncio
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, cast

import logfire
from pydantic_ai.capabilities import AbstractCapability
from pydantic_ai.exceptions import ModelHTTPError

if TYPE_CHECKING:
    from pydantic_ai.capabilities import WrapModelRequestHandler
    from pydantic_ai.messages import ModelResponse
    from pydantic_ai.models import ModelRequestContext
    from pydantic_ai.tools import RunContext

FALLBACK_RATE_LIMIT_SLEEP_SECONDS = 20.0
HTTP_TOO_MANY_REQUESTS = 429
MAX_RATE_LIMIT_RETRIES = 5
RATE_LIMIT_RETRY_BUFFER_SECONDS = 2.0


@dataclass
class RateLimitRetryCapability[AgentDepsT](AbstractCapability[AgentDepsT]):
    """Retry 429 model requests without restarting the agent run."""

    fallback_sleep_seconds: float = FALLBACK_RATE_LIMIT_SLEEP_SECONDS
    max_retries: int = MAX_RATE_LIMIT_RETRIES
    retry_buffer_seconds: float = RATE_LIMIT_RETRY_BUFFER_SECONDS

    async def wrap_model_request(
        self,
        ctx: RunContext[AgentDepsT],  # noqa: ARG002
        *,
        request_context: ModelRequestContext,
        handler: WrapModelRequestHandler,
    ) -> ModelResponse:
        """Sleep and retry when the provider asks us to wait for rate limits."""
        attempts_remaining = self.max_retries
        while True:
            try:
                return await handler(request_context)
            except ModelHTTPError as error:
                if error.status_code != HTTP_TOO_MANY_REQUESTS or attempts_remaining <= 0:
                    raise

                wait_seconds = rate_limit_wait_seconds(
                    error=error,
                    fallback_sleep_seconds=self.fallback_sleep_seconds,
                    retry_buffer_seconds=self.retry_buffer_seconds,
                )
                retry_number = self.max_retries - attempts_remaining + 1
                logfire.warning(
                    f"OpenAI rate limit hit; waiting {wait_seconds:.1f}s before retry "
                    f"{retry_number}/{self.max_retries}.",
                )
                await asyncio.sleep(wait_seconds)
                attempts_remaining -= 1


def rate_limit_wait_seconds(
    *,
    error: ModelHTTPError,
    fallback_sleep_seconds: float,
    retry_buffer_seconds: float,
) -> float:
    """Return the provider-suggested retry delay with a small buffer."""
    message = ""
    if isinstance(error.body, dict):
        body = cast("dict[str, Any]", error.body)
        message = str(body.get("message") or "")

    match = re.search(r"try again in ([0-9]+(?:\.[0-9]+)?)s", message, flags=re.IGNORECASE)
    if match is None:
        return fallback_sleep_seconds

    return float(match.group(1)) + retry_buffer_seconds
