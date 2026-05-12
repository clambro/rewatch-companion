# Pipeline

Offline content generation for Rewatch Companion.

The first pipeline feature is essay generation. It takes a kind plus a plain-language description, lets a single Pydantic AI agent research and draft the post, then prints a simple MDX draft.

## Structure

- `generate_essay.py` - CLI entrypoint and thin orchestration.
- `agent.py` - Pydantic AI agent definition.
- `prompt.py` - essay agent prompt string.
- `schemas.py` - target and generated essay schemas.

## Commands

Requires Python 3.14.

Copy `.env.example` to `.env` and set `OPENAI_API_KEY` before running
generation.

```bash
uv run generate-essay --help
uv run generate-essay --kind about --description "A full-series thesis essay about what Succession is fundamentally about."
uv run ruff check
uv run ty check
```
