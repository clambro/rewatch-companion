# Site Publication Plan

## Goal

Prepare Rewatch Companion for first public deployment as a static Astro site.

## Launch Checklist

### 1. Publication Workflow and Domain Decision

Publish from a public GitHub repository using GitHub Pages, with Cloudflare handling DNS for the custom domain. The deployment path is documented in the README.

Still open:

- Configure `rewatchcompanion.com` in GitHub Pages.
- Point Cloudflare DNS at GitHub Pages.

The GitHub Pages workflow should follow `../clambro.github.io`, adjusted for this repo's `site/` subdirectory:

- use Node 22
- install from `site/package-lock.json`
- run the Astro build from `site/`
- upload `site/dist`
- include `site/public/CNAME` with `rewatchcompanion.com`

### 2. Astro Production Config

Configured `site/astro.config.mjs` for production:

- set the final `site` URL to `https://rewatchcompanion.com`
- use `trailingSlash: "never"`
- add sitemap support

### 3. 404 Page

Add `site/src/pages/404.astro`.

Keep it simple:

- clear "Page not found" message
- short explanation
- link back to the homepage
- visual style consistent with the rest of the site

### 4. Baseline SEO Metadata

Expand `site/src/layouts/BaseLayout.astro` beyond title and description:

- canonical URL
- favicon links
- site name metadata
- basic Open Graph metadata without custom social-card work

Per-article social cards and richer sharing images are a separate ticket.

### 5. Public Root Assets

Add the basic public assets needed for launch:

- `site/public/robots.txt`
- favicon
- apple touch icon
- default Open Graph image, only enough to support baseline metadata

### 6. Sitemap

Install and configure `@astrojs/sitemap`.

This matters now because the site has a real page graph: homepage, show page, character essays, theme essays, and all Succession episode essays.

### 7. Build and Check Scripts

Add a production-oriented check path for the site:

- keep `npm run build`
- add `npm run check` with `astro check`
- add the required dependencies for Astro checking

Before publishing, run the static build from `site/` and fix route/content errors.

## Not In This Ticket

- RSS/feed support
- analytics
- per-article social cards
- ad slots or ad metadata
