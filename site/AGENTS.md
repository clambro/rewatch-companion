# AGENTS.md

## Scope

These instructions apply to files under `site/`. The root `AGENTS.md` also applies.

## Stack

- Astro 6.
- Official `@astrojs/mdx` integration.
- Node `>=22.12.0`; see `.nvmrc` and `package.json`.
- Root-level content is loaded through `src/content.config.ts`.

## Commands

Available commands from `site/`:

- Install dependencies: `npm install`
- Start dev server: `npm run dev`
- Build static site: `npm run build`
- Preview built site: `npm run preview`

Do not run dev, build, preview, browser inspection, or site-fetching commands unless the user explicitly asks. If asked to run them, use Node 22 or newer.

## Site Structure

- `src/content.config.ts` defines content collections for shows, episode metadata, and episode MDX articles.
- `src/pages/index.astro` renders the home page.
- `src/pages/shows/[show]/index.astro` renders show pages.
- `src/pages/shows/[show]/episodes/[season]/[episode]/index.astro` renders episode articles.
- `src/components/SpoilerNotice.astro` owns the fixed spoiler notice copy.
- `src/components/EpisodeNav.astro` owns previous/next navigation.

## Conventions

- Keep the site static. Do not add runtime APIs, database calls, server-side content fetching, or dynamic publication behavior.
- Do not hand-roll Markdown, MDX, YAML, or frontmatter parsing. Use Astro content collections and Astro rendering APIs.
- Keep publishable content in the repo-root `content/` directory, not under `site/`.
- If YAML content shape changes, update `src/content.config.ts` in the same change.
- Do not add ad slots, ad metadata, or ad configuration yet.

## Generated Files

Do not edit or commit generated output:

- `node_modules/`
- `.astro/`
- `dist/`
- `.vite/`
