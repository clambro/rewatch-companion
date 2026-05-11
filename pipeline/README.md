# Pipeline

Offline content generation for Rewatch Companion.

The first pipeline feature is per-episode essay generation. It reads episode inputs, calls a small set of generation tools, and eventually writes reviewed static output into the repo-root `content/` directory.

## Structure

- `episode_generation/` - per-episode essay generation feature.
- `episode_generation/orchestrator.py` - coordinates the end-to-end generation flow.
- `episode_generation/tools/` - self-contained tools used by the feature.
- `episode_generation/prompts/` - feature-level prompt inputs shared across tools.

## Commands

Requires Python 3.14.

```bash
uv run generate-episode --help
uv run ruff check
uv run ty check
```
