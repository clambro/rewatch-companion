# Pipeline

Offline content generation for Rewatch Companion.

The pipeline generates reviewed static output for the repo-root `content/`
directory. It is offline-only and must not power the public site at runtime.

Essay generation takes a manifest-defined article target, lets a Pydantic AI
agent research, draft, and revise the post, then writes MDX and YAML metadata
into `content/`.

## Structure

- `cli.py` - root CLI for essay generation and hero image workflows.
- `common/` - shared settings, schemas, manifest loading, and agent retry plumbing.
- `essay_generation/` - essay agent, prompts, research fetching, article export, workflows, schemas, and tests.
- `hero_images/` - hero image search, download, metadata, prompts, rules, schemas, and tests.
- `manifests/` - fixed article titles, prompts, slugs, and episode titles.

## Workflow

Generation is manifest-driven and intentionally explicit:

```txt
manifest target -> source summaries -> research/draft/rewrite agent -> summary -> export
```

The essay workflows are separate:

- theme essays
- character essays
- episode essays

Theme and character essays are independent. Episode essays use generated theme
and character summaries, plus the previous episode summary. Episode essays must
be generated in manifest order so continuity context exists before later
episodes run.

Each generated essay directory includes:

- `index.mdx` - public article body.
- `summary.mdx` - compact internal reference context for later pipeline runs.
- `article.yaml` - static-site metadata.

The pipeline also rebuilds `content/shows/<show>/show.yaml` from committed
content so the site index stays content-driven.

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
`site/src/assets/images/`, normalizes it to the project JPEG dimensions, and writes
only local `src` plus model-written `alt` metadata into the article's YAML.

## Artifact Rules

Committed pipeline output should be limited to reviewed static content:

- `content/shows/<show>/**/index.mdx`
- `content/shows/<show>/**/summary.mdx`
- `content/shows/<show>/**/article.yaml`
- `content/shows/<show>/show.yaml`
- selected local hero images under `site/src/assets/images/`

Keep raw and intermediate artifacts out of version control. Use `.local/` for:

- raw subtitles
- web research blobs
- intermediate drafts
- run logs
- local video/media references
- unselected image candidates

External source URLs, source pages, image-selection rationale, and temporary
OpenAI outputs are pipeline runtime context only. Do not write them into public
article YAML or MDX.

## Boundaries

- Keep feature workflows explicit instead of hiding them behind a generic
  document generator.
- Keep prompt strings in Python modules unless there is a concrete reason to
  split them out.
- Do not add a packaging wrapper such as `src/` or `rewatch_pipeline/` unless
  the project has a concrete distribution reason for it.
- Keep empty `__init__.py` files out of the package tree.
- Prefer naked functions over stateless classes.
