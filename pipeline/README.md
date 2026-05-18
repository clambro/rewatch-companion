# Pipeline

Offline content generation for Rewatch Companion.

The first pipeline feature is essay generation. It takes a manifest-defined article target, lets a single Pydantic AI agent research and draft the post, then writes the MDX and YAML metadata into `content/`.

## Structure

- `generate_theme.py` - CLI entrypoint for theme essays.
- `generate_character.py` - CLI entrypoint for character essays.
- `generate_episode.py` - CLI entrypoint for episode essays.
- `extract_show_frames.py` - CLI entrypoint for screenshot candidate extraction.
- `filter_screenshot_candidates.py` - CLI entrypoint for filtering blurry and duplicate screenshots.
- `generate_essay.py` - shared orchestration, source loading, export, and show index helpers.
- `agent.py` - Pydantic AI agent definition.
- `manifest.py` - generation manifest loading and content-tree checks.
- `manifests/` - fixed article titles, prompts, slugs, and episode titles.
- `prompt.py` - essay agent prompt string.
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
uv run python extract_show_frames.py --show succession --season 1 --episode 1
uv run python filter_screenshot_candidates.py --show succession --season 1 --episode 1
uv run python -m pytest tests/unit/test_manifest_content.py
uv run ruff check
uv run ty check
```

Episode essays must be generated in manifest order. Every episode after the
first one requires the previous episode's `summary.mdx` as continuity context.

Screenshot candidate extraction expects local episode media under
`.local/media/<show>/sXX/eYY.*`, such as
`.local/media/succession/s01/e01.mkv`. It writes scene-based candidates and
`candidate_manifest.json` files under `.local/screenshots/`. These artifacts are
local-only and should not be committed.

Screenshot filtering reads the raw `candidates/` folder, copies kept images into
a sibling `filtered/` folder, and writes `filtering_report.json`. It rejects
dark, bright, flat, blurry, unsafe, and near-duplicate frames. Blur uses a
tile-based Laplacian-variance score, unsafe content uses OpenAI image
moderation, and duplicates use average-hash distance. The report also records
whole-frame blur, luma metrics, and moderation scores for threshold tuning.
