# Pipeline

Offline content generation for Rewatch Companion.

The first pipeline feature is essay generation. It takes a manifest-defined article target, lets a single Pydantic AI agent research and draft the post, then writes the MDX and YAML metadata into `content/`.

## Structure

- `generate_essay.py` - CLI entrypoint and thin orchestration.
- `agent.py` - Pydantic AI agent definition.
- `manifest.py` - generation manifest loading and content-tree checks.
- `manifests/` - fixed article titles, prompts, slugs, and season episode counts.
- `prompt.py` - essay agent prompt string.
- `schemas.py` - target and generated essay schemas.

## Commands

Requires Python 3.14.

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` before running
generation.

```bash
uv run generate-essay --help
uv run generate-essay about --show succession
uv run python -m pytest tests/unit/test_manifest_content.py
uv run ruff check
uv run ty check
```
