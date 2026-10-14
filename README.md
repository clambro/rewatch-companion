# Rewatch Companion

A static rewatch companion for serious, full-series episode analysis.

The initial target show is **Succession**. Essays assume the reader has already watched the full series.

The public site is static. The offline pipeline generates reviewed static
content, but it does not power the site at runtime.

## Structure

- `site/` - Astro static site.
- `content/` - publishable show metadata, episode metadata, MDX articles, and local image references.
- `pipeline/` - offline Python content and hero-image generation pipeline.
- `.local/` - local-only research, media, drafts, and generated artifacts. This is ignored by Git.

## Content Contract

`content/` is the stable boundary between the pipeline and the site.

Committed content should be safe to publish:

- `content/shows/<show>/show.yaml`
- `content/shows/<show>/**/article.yaml`
- `content/shows/<show>/**/index.mdx`
- `content/shows/<show>/**/summary.mdx`
- hero image metadata that references committed images under `site/src/assets/images/`

Do not commit raw subtitles, research blobs, intermediate drafts, image
candidates, video files, external image source URLs, or local media references.
Use `.local/` for those artifacts.

The site reads committed content only. It should not import pipeline code,
query a database, call generation tools, fetch external article sources at
runtime, or expose pipeline artifacts.

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

## Deployment

Cloudflare Workers configuration is in `site/wrangler.jsonc`.
Build from `site/` with `npm run build`, then deploy with `npx wrangler deploy`.
For Cloudflare Git integration, use branch `main` and root directory `site`.

The site URL is `https://rewatchcompanion.com`.

## Hooks

Pre-commit is configured in `.pre-commit-config.yaml`.

```bash
pre-commit install
pre-commit run --all-files
```
