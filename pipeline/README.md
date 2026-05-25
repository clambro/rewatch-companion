# Pipeline

Offline content generation for Rewatch Companion.

The first pipeline feature is essay generation. It takes a manifest-defined article target, lets a single Pydantic AI agent research and draft the post, then writes the MDX and YAML metadata into `content/`.

## Structure

- `generate_theme.py` - CLI entrypoint for theme essays.
- `generate_character.py` - CLI entrypoint for character essays.
- `generate_episode.py` - CLI entrypoint for episode essays.
- `generate_missing_essays.py` - manifest-driven backfill for missing essays.
- `find_hero_image.py` - CLI entrypoint for finding an online hero image candidate for a completed article.
- `find_missing_hero_images.py` - manifest-driven backfill for missing article hero images.
- `generate_essay.py` - shared orchestration, source loading, export, and show index helpers.
- `agent.py` - Pydantic AI agent definition.
- `hero_image_agent.py` - Pydantic AI hero image search agent definition.
- `manifest.py` - generation manifest loading and content-tree checks.
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
uv run python generate_theme.py --show succession --slug logan-fractured-inheritance
uv run python generate_character.py --show succession --slug kendall-roy
uv run python generate_episode.py --show succession --season 1 --episode 1
uv run python generate_missing_essays.py --show succession
uv run python find_hero_image.py --show succession episodes --season 2 --episode 2
uv run python find_missing_hero_images.py --show succession
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
