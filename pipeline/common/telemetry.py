"""Telemetry setup for pipeline runs."""

import functools

import logfire

from common.settings import settings


@functools.cache
def configure_logfire() -> None:
    """Configure Logfire instrumentation once per process."""
    logfire.configure(
        service_name="rewatch-pipeline",
        token=settings.logfire_token,
        metrics=logfire.MetricsOptions(collect_in_spans=True),
        scrubbing=False,
    )
    logfire.instrument_pydantic_ai(use_aggregated_usage_attribute_names=True)
    logfire.instrument_openai(version="latest")
    logfire.instrument_httpx(capture_all=True)
