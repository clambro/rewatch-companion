# AGENTS.md

## Scope

These instructions apply to files under `pipeline/`. The root `AGENTS.md` also applies.

## Purpose

`pipeline/` is reserved for the offline Python content-generation pipeline. It should create reviewed static output for the repo-root `content/` directory. It must not power the public site at runtime.

Expected responsibilities once implemented:

- clean SRT/VTT subtitles into an internal transcript format
- generate theme, character, and episode essays
- generate compact `summary.mdx` files for source context
- enforce manifest-order episode generation with the previous episode summary as required context
- rebuild `show.yaml` from committed content files
- create screenshot candidates from local media
- select and export final screenshots
- write final `index.mdx`, `summary.mdx`, and metadata YAML files into `content/`

## Commands

This project uses `uv` for package management, ruff for linting, and ty for type checking:

```bash
uv run python -m path.to.module          # run code
uv run python -m pytest path/to/test     # run specific tests
uv run python -m pytest .                # run all tests
uv run ruff check --fix                  # linter (must pass)
uv run ty check                          # type checker (must pass)
```

Before handing work back, run the relevant checks for the files you changed. For
Python changes, run at least `uv run ruff check <changed files>` and
`uv run ty check` from `pipeline/`. For generated content, Markdown, MDX, YAML,
or other repo-level formatted files, run Prettier before committing. Do not rely
on pre-commit as the first place formatting, lint, or type errors are
discovered.

**Suppression rules**:

- Do NOT `# noqa` unless you have an excellent reason (e.g., complexity warnings in routing code)
- Do NOT ignore type errors except for unfixable external package issues
- When in doubt, fix the issue rather than suppress the warning

## Code Organization

Read Python modules from top to bottom:

- public entrypoints first
- private/helper functions after the functions they support
- no C-style forward-declaration ordering
- no one-line, one-use helper functions
- keep prompt strings in Python modules, not Markdown files, unless explicitly requested

## Artifact Rules

Keep raw and intermediate artifacts out of version control. Use `.local/` for:

- raw subtitles
- web research blobs
- draft essays
- review notes
- run logs
- local video/media references
- scene-detection outputs
- screenshot candidate images

Only write reviewed, publishable static output into `content/`.

## Runtime Boundary

The public site must not import pipeline code, call the pipeline, or expose pipeline artifacts.
