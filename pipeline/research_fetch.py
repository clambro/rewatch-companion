"""Cleaned web research fetching for essay generation."""

import re

from openai import OpenAI
from pydantic import BaseModel
from pydantic_ai.common_tools.web_fetch import WebFetchLocalTool
from pydantic_ai.exceptions import ModelRetry
from pydantic_ai.messages import BinaryContent

from prompt import RESEARCH_SOURCE_SUMMARY_INSTRUCTIONS, build_research_source_summary_prompt
from settings import settings

SUMMARY_MODEL = "gpt-5.4-nano"
MAX_CLEAN_RESEARCH_CHARS = 20_000
MIN_MEANINGFUL_LINE_CHARS = 2
MIN_USABLE_RESEARCH_CHARS = 700
MIN_USABLE_RESEARCH_WORDS = 120
MAX_TABLE_SEPARATOR_COUNT = 6
MIN_CONFIG_PUNCTUATION_COUNT = 8
CONFIG_PUNCTUATION_RATIO = 0.12
MAX_CONFIG_QUOTE_COUNT = 10

JUNK_LINE_PATTERNS = [
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"\b(function|window|document|dataLayer|OneTrust|Optanon|googletag|"
        r"localStorage|sessionStorage)\b",
        r"\b(var|let|const)\s+[A-Za-z_$][\w$]*\s*=",
        r"\b(cookie|consent|privacy settings|newsletter|subscribe|advertisement)\b",
        r"\b(loading|please wait|enable javascript|access denied|blocked|forbidden)\b",
        r"^\s*[.#]?[A-Za-z][\w-]*\s*\{",
        r"^\s*--[\w-]+\s*:",
        r"[{};]{3,}",
        r"\b(rgb|rgba|hsl|calc)\(",
    )
]

REPEATED_SPACE_RE = re.compile(r"[ \t]{2,}")
EXCESSIVE_NEWLINES_RE = re.compile(r"\n{3,}")


class CleanedResearchSource(BaseModel):
    """Cleaned research source returned to the essay agent."""

    url: str
    title: str
    content: str
    summarized: bool


async def fetch_research_source(url: str) -> CleanedResearchSource:
    """Fetch a web source, clean boilerplate, and summarize it when still too long."""
    fetcher = WebFetchLocalTool(
        max_content_length=None,
        allow_local_urls=False,
        timeout=30,
    )
    result = await fetcher(url)
    if isinstance(result, BinaryContent):
        raise ModelRetry(f"Fetch a text article source instead of binary content: {url}")

    title = str(result.get("title") or "")
    content = cleaned_research_content(content=str(result["content"]))
    if not is_usable_research_content(content=content):
        raise ModelRetry(f"Fetched source did not contain usable article text: {url}")

    summarized = False
    if len(content) > MAX_CLEAN_RESEARCH_CHARS:
        content = summarize_research_source(url=url, title=title, content=content)
        summarized = True

    return CleanedResearchSource(
        url=str(result["url"]),
        title=title,
        content=content,
        summarized=summarized,
    )


def cleaned_research_content(*, content: str) -> str:
    """Remove obvious page chrome, script output, CSS, and boilerplate from fetched markdown."""
    cleaned_lines = []
    in_code_block = False

    for line in content.splitlines():
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if not stripped:
            cleaned_lines.append("")
            continue
        if is_junk_line(stripped):
            continue

        normalized = REPEATED_SPACE_RE.sub(" ", stripped)
        cleaned_lines.append(normalized)

    cleaned = "\n".join(cleaned_lines)
    cleaned = EXCESSIVE_NEWLINES_RE.sub("\n\n", cleaned)
    return cleaned.strip()


def is_usable_research_content(*, content: str) -> bool:
    """Return whether cleaned content has enough article text to be worth using."""
    if len(content) < MIN_USABLE_RESEARCH_CHARS:
        return False

    words = re.findall(r"[A-Za-z][A-Za-z'-]+", content)
    if len(words) < MIN_USABLE_RESEARCH_WORDS:
        return False

    return not looks_like_loading_shell(content=content)


def summarize_research_source(*, url: str, title: str, content: str) -> str:
    """Summarize a cleaned source that is still too large to return to the agent."""
    client = OpenAI(api_key=settings.openai_api_key)
    response = client.responses.create(
        model=SUMMARY_MODEL,
        instructions=RESEARCH_SOURCE_SUMMARY_INSTRUCTIONS,
        input=build_research_source_summary_prompt(
            url=url,
            title=title,
            content=content,
        ),
    )
    return response.output_text.strip()


def is_junk_line(line: str) -> bool:
    """Return whether a fetched markdown line is obvious page machinery."""
    if len(line) <= MIN_MEANINGFUL_LINE_CHARS:
        return True
    if line.count("|") >= MAX_TABLE_SEPARATOR_COUNT:
        return True
    if looks_like_json_or_javascript(line):
        return True

    return any(pattern.search(line) for pattern in JUNK_LINE_PATTERNS)


def looks_like_loading_shell(*, content: str) -> bool:
    """Return whether cleaned content is probably a blocked loading shell."""
    lines = [line.strip() for line in content.splitlines() if line.strip()]
    if not lines:
        return True

    loading_lines = sum(1 for line in lines if line.lower() == "loading...")
    css_like_lines = sum(
        1
        for line in lines
        if line.endswith(";") or line.startswith("@") or re.match(r"^[.#]?[A-Za-z][\w-]*\s*:", line)
    )
    return loading_lines > 0 and css_like_lines >= len(lines) // 2


def looks_like_json_or_javascript(line: str) -> bool:
    """Return whether a line is likely machine config rather than article prose."""
    punctuation_count = sum(1 for character in line if character in "{}[]:;,=")
    if punctuation_count < MIN_CONFIG_PUNCTUATION_COUNT:
        return False

    punctuation_ratio = punctuation_count / len(line)
    quote_count = line.count('"') + line.count("'")
    return punctuation_ratio > CONFIG_PUNCTUATION_RATIO or quote_count > MAX_CONFIG_QUOTE_COUNT
