# Pipeline

Offline content generation for Rewatch Companion.

The first pipeline feature is essay generation. It takes a manifest-defined article target, lets a single Pydantic AI agent research and draft the post, then writes the MDX and YAML metadata into `content/`.

## Structure

- `cli.py` - root CLI for essay generation and hero image workflows.
- `common/` - shared settings, schemas, manifest loading, and agent retry plumbing.
- `essay_generation/` - essay agent, prompts, research fetching, article export, workflows, schemas, and tests.
- `hero_images/` - hero image search, download, metadata, prompts, rules, schemas, and tests.
- `manifests/` - fixed article titles, prompts, slugs, and episode titles.

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
