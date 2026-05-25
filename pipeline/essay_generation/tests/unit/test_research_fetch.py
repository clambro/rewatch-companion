"""Tests for cleaned research fetching."""

from essay_generation.research_fetch import (
    cleaned_research_content,
    is_junk_line,
    is_usable_research_content,
)


def test_cleaned_research_content_removes_page_machinery() -> None:
    """Fetched markdown should discard obvious script, CSS, and consent junk."""
    content = """
Sarah Snook on 'Succession' Ending

window.dataLayer = window.dataLayer || [];
const consentConfig = {"cookie":"abc","advertisement":true,"privacy settings":true};
--site-header-color: rgb(255, 255, 255);
.article-page { color: var(--site-header-color); }

Sarah Snook had a lot to discuss after the finale, including the pregnancy and
the final scene between Shiv and Tom.

Newsletter
Subscribe for more coverage.

The actor said the ending worked because the relationship remained unresolved.
"""

    cleaned = cleaned_research_content(content=content)

    assert "Sarah Snook on 'Succession' Ending" in cleaned
    assert "final scene between Shiv and Tom" in cleaned
    assert "relationship remained unresolved" in cleaned
    assert "window.dataLayer" not in cleaned
    assert "consentConfig" not in cleaned
    assert "--site-header-color" not in cleaned
    assert ".article-page" not in cleaned
    assert "Newsletter" not in cleaned
    assert "Subscribe" not in cleaned


def test_json_like_machine_config_is_junk() -> None:
    """Long config-like lines should be removed before they hit the model."""
    assert is_junk_line(
        '{"css": ".foo{color:red}", "ads": true, "cookies": true, "slots": [1, 2, 3]}',
    )


def test_loading_shell_is_not_usable_research_content() -> None:
    """Blocked loading pages should not count as successful source fetches."""
    content = """
Loading...

margin: 0;
padding: 0;
box-sizing: border-box;
font-family: sans-serif;
background: #f5f5f5;
display: flex;
align-items: center;
justify-content: center;
animation: bounce 1.2s ease-in-out infinite;
font-size: 15px;
color: #999;
letter-spacing: 0.5px;

Loading...
"""

    assert not is_usable_research_content(content=content)
