"""Tests for essay prompts."""

from prompt import AGENT_INSTRUCTIONS, render_workspace_state
from research_limits import MAX_RESEARCH_FETCHES, MAX_RESEARCH_SEARCHES
from schemas import EssayKind, EssayTarget, EssayWorkspace, Show


def test_agent_instructions_refer_to_live_research_budget() -> None:
    """The agent should rely on live state and tool responses for budget counts."""
    assert "current state and research tool responses" in AGENT_INSTRUCTIONS


def test_workspace_state_includes_remaining_research_budget() -> None:
    """The runtime state should show used and remaining research calls."""
    workspace = EssayWorkspace(
        target=EssayTarget(
            show=Show.SUCCESSION,
            kind=EssayKind.CHARACTERS,
            title="Kendall Roy",
            prompt="Write about Kendall.",
            slug="kendall-roy",
        ),
        research_searches=1,
        research_fetches=2,
    )

    state = render_workspace_state(workspace=workspace)

    assert f"Search budget: {MAX_RESEARCH_SEARCHES}" in state
    assert "Searches used: 1" in state
    assert f"Searches remaining: {MAX_RESEARCH_SEARCHES - 1}" in state
    assert f"Fetch budget: {MAX_RESEARCH_FETCHES}" in state
    assert "Fetches used: 2" in state
    assert f"Fetches remaining: {MAX_RESEARCH_FETCHES - 2}" in state
