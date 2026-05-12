# AGENTS.md

## Scope

These instructions apply to the whole repository. More specific `AGENTS.md` files in child directories override or extend this file for work in those directories.

## Project Overview

Rewatch Companion is a static publishing project for full-series, episode-by-episode rewatch essays. The public site is static; any generation pipeline is offline-only.

## Repository Map

- `docs/project_plan.md` - product and architecture background. Use it as context, not as an immutable spec.
- `site/` - Astro static site. Read `site/AGENTS.md` before changing site code.
- `content/` - publishable show metadata, episode metadata, MDX articles, and final selected screenshots.
- `pipeline/` - future offline Python pipeline. Read `pipeline/AGENTS.md` before adding pipeline code.
- `.local/` - local-only artifacts such as research, media, generated drafts, run logs, and scene candidates. Never commit it.

## Content Boundary

`content/` is the stable contract between the offline pipeline and the static site.

Committed content should be safe to publish:

- `content/shows/<show>/show.yaml`
- `content/shows/<show>/episodes/<season>/<episode>/episode.yaml`
- `content/shows/<show>/episodes/<season>/<episode>/index.mdx`
- final selected screenshots only, when screenshots are added

Do not commit raw subtitles, research blobs, intermediate drafts, scene-detection output, video files, or local media references.

## Global Rules

- Keep the public site static. Do not add a runtime backend, database, CMS, or API unless explicitly requested.
- Do not add ad-related metadata or components yet.
- Keep changes scoped to the directory and task at hand.
- Respect `.pre-commit-config.yaml` and run it as part of your self-review.
- Prefer updating these instructions when workflow rules change instead of relying on chat history.
- Order code for top-to-bottom reading. Put public entrypoints before private helpers, and place helper functions below the functions they support.
