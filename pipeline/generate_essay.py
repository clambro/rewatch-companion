"""CLI entrypoint for essay generation."""

import argparse
import json
import re
import sys

from agent import run_essay_agent
from schemas import EssayDraft, EssayKind, EssayTarget


def main() -> None:
    """Run the essay generation CLI."""
    parser = argparse.ArgumentParser(description="Generate a rewatch companion essay draft.")
    parser.add_argument("--kind", choices=[kind.value for kind in EssayKind], required=True)
    parser.add_argument("--description", required=True)
    args = parser.parse_args()

    target = EssayTarget(kind=EssayKind(args.kind), description=args.description)
    draft = generate_essay(target=target)
    sys.stdout.write(render_draft(draft))


def generate_essay(*, target: EssayTarget) -> EssayDraft:
    """Generate an essay draft and orchestration-owned slug."""
    essay = run_essay_agent(target=target)
    return EssayDraft(
        slug=re.sub(r"[^a-z0-9]+", "-", essay.title.lower()).strip("-"),
        title=essay.title,
        subtitle=essay.subtitle,
        body_mdx=essay.body_mdx,
    )


def render_draft(draft: EssayDraft) -> str:
    """Render the generated draft as a simple MDX document."""
    return (
        "---\n"
        f"title: {json.dumps(draft.title)}\n"
        f"dek: {json.dumps(draft.subtitle)}\n"
        f"slug: {json.dumps(draft.slug)}\n"
        "---\n\n"
        f"{draft.body_mdx.rstrip()}\n"
    )


if __name__ == "__main__":
    main()
