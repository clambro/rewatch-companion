# Rewatch Companion

A static rewatch companion for serious, full-series episode analysis.

The initial target show is **Succession**. Essays assume the reader has already watched the full series.

## Structure

- `site/` - Astro static site.
- `content/` - publishable show metadata, episode metadata, MDX articles, and final selected screenshots.
- `pipeline/` - reserved for the future offline Python content-generation pipeline.
- `docs/project_plan.md` - project plan and editorial/product context.
- `.local/` - local-only research, media, drafts, and generated artifacts. This is ignored by Git.

## Requirements

- Node `>=22.12.0` for the Astro site.
- `pre-commit` for repository hooks.

## Site

```bash
cd site
npm install
npm run dev
```

Useful commands:

```bash
npm run build
npm run preview
```

## Hooks

Pre-commit is configured in `.pre-commit-config.yaml`.

```bash
pre-commit install
pre-commit run --all-files
```
