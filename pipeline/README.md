# Pipeline

Offline content generation for Rewatch Companion.

The first pipeline feature is essay generation. It takes a manifest-defined article target, lets a single Pydantic AI agent research and draft the post, then writes the MDX and YAML metadata into `content/`.

## Structure

- `cli.py` - root CLI for essay generation and hero image workflows.
- `generate_theme.py` - theme essay workflow.
- `generate_character.py` - character essay workflow.
- `generate_episode.py` - episode essay workflow.
- `generate_missing_essays.py` - manifest-driven backfill for missing essays.
- `find_hero_image.py` - workflow for finding an online hero image for a completed article.
- `find_missing_hero_images.py` - manifest-driven backfill for missing article hero images.
- `generate_essay.py` - shared orchestration, source loading, export, and show index helpers.
- `agent.py` - Pydantic AI agent definition.
- `hero_image_agent.py` - Pydantic AI hero image search agent definition.
- `common/` - shared settings, manifest loading, and agent retry plumbing.
- `manifests/` - fixed article titles, prompts, slugs, and episode titles.
- `prompt.py` - essay agent prompt strings.
- `hero_image_prompt.py` - hero image agent prompt strings.
- `schemas.py` - target and generated essay schemas.

## Commands

Requires Python 3.14.

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` before running
generation.

Agent runs are instrumented with Logfire. To send traces to Logfire, authenticate
and select a project from `pipeline/`:

```bash
uv run logfire auth
uv run logfire projects use
```

```bash
uv run poe rw -- essay theme --show succession --slug logan-fractured-inheritance
uv run poe rw -- essay character --show succession --slug kendall-roy
uv run poe rw -- essay episode --show succession --season 1 --episode 1
uv run poe rw -- essay missing --show succession
uv run poe rw -- image episode --show succession --season 2 --episode 2
uv run poe rw -- image missing --show succession
uv run python -m pytest tests/unit/test_manifest_content.py
uv run ruff check
uv run ty check
```

Episode essays must be generated in manifest order. Every episode after the
first one requires the previous episode's `summary.mdx` as continuity context.

Hero image search is separate from essay generation. It reads a completed
article, searches online for one reasonable show image, downloads it into
`site/public/images/`, normalizes it to the project JPEG dimensions, and writes
only local `src` plus model-written `alt` metadata into the article's YAML.
