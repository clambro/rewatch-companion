"""CLI entrypoint for series thesis generation."""

import argparse
from pathlib import Path

import yaml
from pydantic import BaseModel

from agent import run_essay_agent
from generate_essay import write_article
from manifest import load_manifest
from schemas import EssayKind, EssaySource, EssayTarget, Show


class AboutCommand(BaseModel):
    """Parsed CLI command for series thesis generation."""

    show: Show


def generate_about() -> None:
    """Generate a series thesis essay."""
    parser = argparse.ArgumentParser(description="Generate a series thesis essay.")
    parser.add_argument("--show", choices=[show.value for show in Show], required=True)
    command = AboutCommand.model_validate(vars(parser.parse_args()))
    manifest = load_manifest(show=command.show)
    target = EssayTarget(
        show=command.show,
        kind=EssayKind.ABOUT,
        title=manifest.about.title,
        prompt=manifest.about.prompt,
    )

    write_article(
        target=target,
        draft=run_essay_agent(target=target, sources=about_sources(target=target)),
    )


def about_sources(*, target: EssayTarget) -> list[EssaySource]:
    """Load theme and character essays as context for the series thesis."""
    show_root = Path(__file__).resolve().parent.parent / "content" / "shows" / target.show.value
    sources = []
    for section_root in [
        show_root / EssayKind.THEMES.value,
        show_root / EssayKind.CHARACTERS.value,
    ]:
        sources.extend(
            render_source(path=path)
            for path in sorted(section_root.glob("*/index.mdx"))
            if path.is_file()
        )

    return sources


def render_source(*, path: Path) -> EssaySource:
    """Render one committed essay as source context."""
    metadata_path = path.with_name("article.yaml")
    metadata = yaml.safe_load(metadata_path.read_text(encoding="utf-8"))
    return EssaySource(
        title=metadata["title"],
        subtitle=metadata["seo"]["description"],
        body_mdx=path.read_text(encoding="utf-8").strip(),
    )


if __name__ == "__main__":
    generate_about()
