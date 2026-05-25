"""Research tool limits for essay generation."""

from pydantic_ai.usage import UsageLimits

AGENT_USAGE_LIMITS = UsageLimits(request_limit=18, tool_calls_limit=20)
MAX_RESEARCH_SEARCHES = 4
MAX_RESEARCH_FETCHES = 8
SEARCH_RESULTS_PER_QUERY = 5
