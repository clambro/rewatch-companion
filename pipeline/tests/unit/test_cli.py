"""Tests for the root pipeline CLI."""

from typing import TYPE_CHECKING, Any

import cli
from common.schemas import EssayKind, Show

if TYPE_CHECKING:
    import pytest


def test_cli_dispatches_theme_essay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Root CLI should dispatch theme essay generation."""
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(cli, "assert_network_baseline", lambda: None)
    monkeypatch.setattr(
        cli,
        "generate_theme_essay",
        lambda **kwargs: calls.append(kwargs),
    )

    cli.main(["essay", "theme", "--show", "succession", "--slug", "love-as-leverage"])

    assert calls == [{"show": Show.SUCCESSION, "slug": "love-as-leverage"}]


def test_cli_dispatches_episode_essay(monkeypatch: pytest.MonkeyPatch) -> None:
    """Root CLI should dispatch episode essay generation."""
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(cli, "assert_network_baseline", lambda: None)
    monkeypatch.setattr(
        cli,
        "generate_episode_essay",
        lambda **kwargs: calls.append(kwargs),
    )

    cli.main(["essay", "episode", "--show", "succession", "--season", "2", "--episode", "2"])

    assert calls == [{"show": Show.SUCCESSION, "season": 2, "episode_number": 2}]


def test_cli_dispatches_missing_essay_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Root CLI should dispatch missing essay generation."""
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        cli,
        "generate_missing_essays",
        lambda **kwargs: calls.append(kwargs),
    )

    cli.main(["essay", "missing", "--show", "succession", "--dry-run"])

    assert calls == [{"show": Show.SUCCESSION, "dry_run": True}]


def test_cli_dispatches_character_image(monkeypatch: pytest.MonkeyPatch) -> None:
    """Root CLI should dispatch single-article hero image search."""
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(cli, "assert_network_baseline", lambda: None)
    monkeypatch.setattr(
        cli,
        "find_article_hero_image",
        lambda **kwargs: calls.append(kwargs),
    )

    cli.main(["image", "character", "--show", "succession", "--slug", "kendall-roy"])

    command = calls[0]["command"]
    assert command.show == Show.SUCCESSION
    assert command.kind == EssayKind.CHARACTERS
    assert command.slug == "kendall-roy"


def test_cli_dispatches_missing_image_dry_run(monkeypatch: pytest.MonkeyPatch) -> None:
    """Root CLI should dispatch missing hero image search."""
    calls: list[dict[str, Any]] = []
    monkeypatch.setattr(
        cli,
        "find_missing_hero_images",
        lambda **kwargs: calls.append(kwargs),
    )

    cli.main(["image", "missing", "--show", "succession", "--dry-run"])

    assert calls == [{"show": Show.SUCCESSION, "dry_run": True}]
