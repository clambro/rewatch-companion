# Rewatch Companion Project Plan

## 1. Project Summary

Rewatch Companion is a static website for serious, full-series television criticism.

The initial target show is **Succession**.

The site is not a recap site, first-watch guide, wiki, quote database, or SEO content farm. It is a polished rewatch companion for viewers who have already finished a series and want to understand how the show works as a completed object.

The core product promise:

> A full-series rewatch companion for serious viewers: essays that explain what the show is doing, why it matters, and how individual episodes connect to the whole.

The public website should be simple, fast, static, and tasteful. The content generation pipeline should be offline, Python-based, and used only to generate static content. There should be no runtime backend serving article data.

## 2. Core Editorial Strategy

The project should not generate isolated episode essays.

The goal is a coherent rewatch companion for a completed TV series. If the pipeline starts directly with per-episode essays, each episode run has to rediscover the show’s meaning from scratch. That creates drift:

- S01E01 may describe the show one way.
- S01E02 may use different language for the same theme.
- Character arcs may be interpreted inconsistently.
- Major concepts may be reintroduced over and over.
- Episode essays may collapse into recap because they lack stable interpretive context.

The problem is not generation speed. Generating more essays is cheap. The problem is **coherence**.

The correct generation order is:

```txt
1. Series thesis essay: “What [Show] Is About”
2. Major theme essays
3. Major character essays
4. Episode-by-episode essays
```

The earlier essays become grounding context for later essays.

The final episode essays should feel like they were written by a critic who already has a mature theory of the show, its themes, its characters, and its ending.

## 3. Content Layers

### Layer 1: Series Thesis

First produce a foundational essay:

```txt
What Succession Is About
```

This essay establishes the project’s master interpretation of the series.

It should answer:

- What is the show fundamentally about?
- What is commonly misunderstood about it?
- What is the show’s governing dramatic engine?
- What does the ending reveal about the whole series?
- What recurring tensions organize the show?
- What should all later essays assume as the baseline interpretation?

This is the root context document for the whole project.

### Layer 2: Major Theme Essays

Next produce essays on the show’s major themes.

For **Succession**, possible theme essays include:

```txt
Family as Corporation, Corporation as Family
Love as Leverage
Logan's Fractured Inheritance
Reality-Making and Media Power
Inheritance as Damage
Language, Evasion, and Corporate Nonsense
Music and Mock Monarchy
Bodies, Illness, and the Limits of Power
Money as Insulation
Documents, Signatures, and Legal Violence
```

Theme essays define the show’s conceptual vocabulary.

They should answer:

- What does this theme mean in this show specifically?
- How is the show’s treatment of this theme distinct?
- Which characters express the theme differently?
- Which episodes are key evidence?
- How does the theme evolve across the series?
- How does the finale clarify or revise the theme?
- What should later character and episode essays remember about this theme?

The point is to prevent every episode essay from saying vague things like “this episode explores power and family.” The theme essays define exactly how power, family, money, language, media, inheritance, and the Roy children's relationship to Logan work in this specific show.

### Layer 3: Major Character Essays

After the theme essays, produce essays on major characters.

For **Succession**, likely character essays include:

```txt
Logan Roy
Kendall Roy
Shiv Roy
Roman Roy
Tom Wambsgans
Greg Hirsch
Connor Roy
Gerri Kellman
Marcia Roy
```

Character essays consume the series thesis and relevant theme essays as context.

They should not be biographies or plot summaries. They should explain the character as an expression of the show’s larger machinery.

Each character essay should answer:

- What is this character’s core wound or operating principle?
- What does this character want?
- What does this character misunderstand about themselves?
- How do they relate to the show’s major themes?
- How does their relationship to power change across the series?
- How does their relationship to language, money, family, and humiliation work?
- What does the ending reveal about them?
- Which episodes are crucial to understanding them?

Weak character claim:

```txt
Kendall Roy wants his father’s approval and struggles to become CEO.
```

Better character claim:

```txt
Kendall Roy is the show’s central case study in failed self-authorship: he can diagnose the future of the business, perform the language of liberation, and repeatedly declare independence, but he remains dependent on Logan’s recognition for his own reality to become real.
```

The character essays should inherit vocabulary from the theme essays.

### Layer 4: Episode Essays

Only after the series thesis, major theme essays, and major character essays exist should the pipeline generate per-episode essays.

Each episode essay should consume:

- episode subtitles or transcript
- web research blob for that episode
- the series thesis essay
- relevant theme essays
- relevant character essays
- house style guide

For visual analysis, the episode workflow should also use screenshot candidates extracted from the local episode file.

Episode essays are the primary rewatch product, but they should not be generated in isolation. They should apply the already-established series, theme, and character framework to a concrete episode.

Each episode essay should answer:

- What is this episode doing structurally?
- How does it move the series?
- Which character arcs does it clarify or distort?
- Which themes does it activate?
- What does it reveal when viewed after the finale?
- What formal, visual, musical, or tonal choices matter?
- Why does this episode matter to the whole show?

Weak episode analysis:

```txt
The vote fails because the siblings cannot work together.
```

Better episode analysis:

```txt
The failed alliance shows the central inheritance problem in miniature: Kendall, Shiv, and Roman each carry a usable fragment of Logan's force, but each fragment is damaged in a way that makes durable coalition impossible.
```

The second version is possible because “Logan's Fractured Inheritance” has already been defined upstream.

## 4. Why This Order Matters

The order is not about saving generation time. It is about building a stable interpretive stack.

```txt
Series thesis → defines the show’s master argument
Themes       → define the conceptual vocabulary
Characters   → embody and complicate the themes
Episodes     → apply the framework to concrete dramatic units
```

This reduces:

- interpretive drift
- repetitive claims
- generic theme language
- recap padding
- inconsistent character readings
- shallow episode analysis

It improves:

- coherence
- specificity
- cross-episode memory
- full-series retrospective value
- stylistic consistency
- downstream prompt quality

The episode essays should feel like the output of a single critical intelligence with a stable theory of the show.

## 5. Goals

### Primary Goals

1. Build a static Astro site that renders the public content in `content/`.
2. Build an offline Python pipeline that generates static content in this order:
   - series thesis essay
   - theme essays
   - character essays
   - episode essays
3. Keep artifact workflows explicit. Do not hide distinct content types behind a vague universal “generate document” abstraction.
4. Support research, drafting, review, and rewrite loops for each artifact type.
5. Support screenshot extraction and screenshot insertion for episode essays only.
6. Keep raw research, intermediate drafts, local media, screenshot candidates, and run logs outside version control.
7. Publish only reviewed static content into the repo’s `content/` directory.

### Non-Goals for MVP

Do not build:

- user accounts
- comments
- CMS
- dynamic personalization
- paid membership
- glossary database
- motif database
- character database
- source drawer
- public citation system
- runtime API
- database-backed public site
- automated publication without human review
- ad slots or ad metadata

The MVP is about proving that the layered workflow can produce a small set of coherent, high-quality essays.

## 6. Editorial Positioning

### What This Site Is

A **full-series rewatch guide**.

Every essay assumes the reader has already seen the entire series. Spoilers are allowed throughout. The point is to understand the work with full knowledge of where it goes.

### What This Site Is Not

It is not:

- a recap
- a summary
- a first-watch guide
- a news site
- a wiki
- a fan theory archive
- a quote database
- a transcript replacement
- a screenshot gallery
- an SEO content farm

### Editorial Test

Every article must pass this test:

> Could a smart viewer who has already watched the show still learn something?

If the answer is no, the article should not be published.

## 7. Initial Content Scope

The first show should be **Succession**.

The first content milestone should be the interpretive foundation:

```txt
content/shows/succession/about/what-succession-is-about/
content/shows/succession/themes/family-as-corporation/
content/shows/succession/themes/logan-fractured-inheritance/
content/shows/succession/characters/logan-roy/
content/shows/succession/characters/kendall-roy/
```

Only after those are working should the pipeline generate the first episode essays:

```txt
content/shows/succession/episodes/s01/e01-celebration/
content/shows/succession/episodes/s01/e02-shit-show-at-the-fuck-factory/
content/shows/succession/episodes/s01/e03-lifeboats/
```

## 8. Repository Structure

The repo contains three main areas:

1. `site/` — the Astro static site.
2. `pipeline/` — the Python offline content generation pipeline.
3. `content/` — the committed static content contract.

They live in the same repo for convenience, but the site and pipeline should not be tightly coupled.

The only stable contract between them is `content/`.

```txt
rewatch-companion/
  site/
    package.json
    astro.config.mjs
    src/
      pages/
      layouts/
      components/
      styles/

  pipeline/
    pyproject.toml
    README.md
    workflows/
    tools/
    prompts/

  content/
    shows/
      succession/
        show.yaml
        about/
        themes/
        characters/
        episodes/

  docs/
    project_plan.md

  .local/
    research/
    runs/
    media/

  README.md
```

The `.local/` directory must be gitignored. It is where raw research, intermediate drafts, video-derived artifacts, screenshot candidates, and run logs live.

## 9. Public Site Architecture

The public site should be static-first.

Use Astro for the site.

The site should render:

- show landing pages
- series thesis essays
- theme essays
- character essays
- episode article pages
- previous/next episode navigation
- spoiler notices
- screenshots in episode essays
- basic SEO metadata
- sitemap output

The site should not:

- query a database
- call the generation pipeline
- fetch external sources at runtime
- expose research blobs
- expose review artifacts
- expose raw citations
- dynamically generate content from non-committed artifacts

### URL Structure

Public URLs should be organized by show and artifact type:

```txt
/shows/succession/
/shows/succession/about/what-succession-is-about/
/shows/succession/themes/logan-fractured-inheritance/
/shows/succession/characters/kendall-roy/
/shows/succession/episodes/s01/e01-celebration/
```

## 10. Static Content Contract

The `content/` directory is the publishing contract.

Everything in `content/` should be safe to commit.

Raw research, raw subtitles, local episode files, generated contact sheets, scene images, screenshot candidates, and intermediate drafts should not be committed.

Example public content structure:

```txt
content/
  shows/
    succession/
      show.yaml

      about/
        what-succession-is-about/
          index.mdx
          article.yaml

      themes/
        family-as-corporation/
          index.mdx
          article.yaml
        logan-fractured-inheritance/
          index.mdx
          article.yaml

      characters/
        logan-roy/
          index.mdx
          article.yaml
        kendall-roy/
          index.mdx
          article.yaml

      episodes/
        s01/
          e01-celebration/
            index.mdx
            episode.yaml
          e02-shit-show-at-the-fuck-factory/
            index.mdx
            episode.yaml
```

### Show Metadata

Example:

```yaml
title: "Succession"
slug: "succession"

about:
  - title: "What Succession Is About"
    path: "about/what-succession-is-about"

themes:
  - title: "Logan's Fractured Inheritance"
    path: "themes/logan-fractured-inheritance"

characters:
  - name: "Kendall Roy"
    path: "characters/kendall-roy"

seasons:
  - season: 1
    episodes:
      - code: "S01E01"
        title: "Celebration"
        path: "episodes/s01/e01-celebration"
```

### General Article Metadata

Use `article.yaml` for series thesis, theme, and character essays.

Example:

```yaml
show: succession
type: theme
title: "Logan's Fractured Inheritance"
slug: "logan-fractured-inheritance"
status: published

seo:
  title: "Succession Theme Analysis: Logan's Fractured Inheritance"
  description: "A full-series analysis of the Roy children as partial, flawed expressions of Logan's power."

context:
  depends_on:
    - "about/what-succession-is-about"
```

### Episode Metadata

Use `episode.yaml` for episode essays.

Example:

```yaml
show: succession
season: 1
episode: 1
code: "S01E01"
title: "Celebration"
slug: "e01-celebration"

seo:
  title: "Succession S01E01 Analysis: Celebration"
  description: "A full-series rewatch analysis of Succession's pilot: Logan's body, Kendall's false coronation, and the family business of humiliation."
```

## 11. Spoiler Policy

All essays are explicitly written for rewatching.

The site should display a spoiler notice on analytical content pages:

> Full-series spoilers throughout. This essay assumes you have watched the entire show.

There is no first-watch-safe mode.

Avoid putting major finale spoilers in:

- page titles
- meta descriptions
- social sharing previews
- Open Graph descriptions

The article body can spoil freely.

## 12. Public Citations and External Links

The public site should not become a mess of references.

Readers are assumed to have watched the show. They do not need academic-style citations.

Do not include public citations unless unavoidable.

External links should be rare and intentional. Examples of acceptable external links:

- an official source
- an essential interview
- a major source directly relevant to a claim
- a legally necessary attribution link

The research blob used internally may contain URLs and source references, but those should not normally be surfaced in the final article.

The final article should read as an essay, not as a literature review.

## 13. House Style Guide

The house style should be clear, concrete, and allergic to generic recap language.

### Reader

The reader is smart, attentive, and has watched the full series.

The reader does not need basic plot summary.

### Mission

Write full-series rewatch essays that explain how the show, theme, character, or episode works.

### Default Move

Do not say what happened. Say what the work is doing.

Bad:

```txt
Kendall goes to the Vaulter meeting and tries to buy the company.
```

Good:

```txt
The Vaulter meeting shows Kendall’s basic problem: he can identify the future of the business, but he cannot make others believe he has inherited Logan’s authority.
```

### Voice

The voice should be:

- specific
- declarative
- analytical
- occasionally sharp
- readable
- non-academic
- non-fannish
- non-clickbaity

### Avoid

Avoid vague LLM-style phrasing.

Banned or strongly discouraged phrases:

```txt
explores themes of
sets the stage
serves as a reminder
power dynamics
complex character
morally gray
nuanced portrayal
rich tapestry
web of relationships
compelling
masterclass
iconic
foreshadows future events
leaves viewers wondering
delves into
at its core
in many ways
this moment encapsulates
```

### Prefer

Prefer concrete verbs and mechanisms:

```txt
converts
exposes
literalizes
rehearses
disguises
weaponizes
withholds
collapses
translates
turns X into Y
makes X legible as Y
```

### Recap Rule

A plot fact may appear only when it supports an interpretive claim.

### Quote Rule

Use short quotes sparingly.

Do not reproduce scenes.

Do not use dialogue as decoration.

Do not publish transcript-like passages.

## 14. Pipeline Philosophy

The content pipeline should be simple and offline.

It exists only to generate static content.

It should not power the website.

It should not expose sources publicly.

It should not maintain a complex public source database for MVP.

The pipeline should build a layered critical system:

```txt
What the show is about
  → what its major themes mean
    → how its characters embody those themes
      → how each episode activates, complicates, or revises that framework
```

## 15. Pipeline Architecture

Build first-class workflow types:

```txt
series_thesis
theme_essay
character_essay
episode_essay
```

Each workflow can share the same basic mechanics:

```txt
research → draft → review → rewrite → export
```

But each artifact type needs its own schemas, prompts, and review checklist.

Do not build a vague universal “generate document” prompt. The artifact types are different enough to deserve separate workflows.

The architecture should stay explicit and direct:

```txt
pipeline/
  pyproject.toml
  README.md

  workflows/
    series_thesis/
      schemas.py
      workflow.py
      research_prompt.md
      write_prompt.md
      review_prompt.md

    theme_essay/
      schemas.py
      workflow.py
      research_prompt.md
      write_prompt.md
      review_prompt.md

    character_essay/
      schemas.py
      workflow.py
      research_prompt.md
      write_prompt.md
      review_prompt.md

    episode_essay/
      schemas.py
      workflow.py
      research_prompt.md
      write_prompt.md
      review_prompt.md
      insert_screenshots_prompt.md

  tools/
    research/
      schemas.py
      service.py

    write/
      schemas.py
      service.py

    review/
      schemas.py
      service.py

    rewrite/
      schemas.py
      service.py

    subtitles/
      schemas.py
      service.py

    screenshots/
      schemas.py
      service.py

  prompts/
    house_style.md
    anti_slop_rules.md
    rewrite.md
```

Rules:

- No `src/` wrapper unless the project later has a concrete packaging reason for it.
- No `rewatch_pipeline/` package layer.
- Keep workflow folders as the first-class artifact types.
- Keep tools small and self-contained.
- Prompt files should be files, not prompt directories.
- Empty `__init__.py` files should not exist.
- Parent modules should import child modules through explicit package APIs when a child package exposes one.
- Prefer naked functions over stateless classes.
- Tests should be colocated at the level of the code they test, under `tests/unit` and `tests/integration`.

## 16. Workflow Details

### Series Thesis Workflow

Inputs:

- show metadata
- full-series research blob
- house style guide

Outputs:

- `content/shows/<show>/about/what-<show>-is-about/index.mdx`
- `content/shows/<show>/about/what-<show>-is-about/article.yaml`
- `.local/runs/<show>/series-thesis/...`

The series thesis workflow establishes the master interpretation used by all later workflows.

### Theme Essay Workflow

Inputs:

- show metadata
- series thesis essay
- theme-specific research blob
- house style guide

Outputs:

- `content/shows/<show>/themes/<theme>/index.mdx`
- `content/shows/<show>/themes/<theme>/article.yaml`
- `.local/runs/<show>/theme-<theme>/...`

Theme essays define the conceptual vocabulary used by character and episode essays.

### Character Essay Workflow

Inputs:

- show metadata
- series thesis essay
- relevant theme essays
- character-specific research blob
- house style guide

Outputs:

- `content/shows/<show>/characters/<character>/index.mdx`
- `content/shows/<show>/characters/<character>/article.yaml`
- `.local/runs/<show>/character-<character>/...`

Character essays explain a character as an expression of the show’s larger machinery.

### Episode Essay Workflow

Inputs:

- show metadata
- episode metadata
- subtitle file extracted from the aired episode
- episode-specific web research blob
- series thesis essay
- relevant theme essays
- relevant character essays
- house style guide
- optional screenshot candidates

Outputs:

- `content/shows/<show>/episodes/<season>/<episode>/index.mdx`
- `content/shows/<show>/episodes/<season>/<episode>/episode.yaml`
- selected screenshots under `content/.../screenshots/`
- `.local/runs/<show>/episode-<code>/...`

Episode essays apply the established interpretive framework to a concrete dramatic unit.

## 17. Internal and Temporary Artifacts

Raw research, intermediate drafts, review outputs, and screenshot candidates should live outside version control.

Example:

```txt
.local/
  research/
    succession/
      series-thesis/
      themes/
      characters/
      episodes/

  runs/
    succession/
      series-thesis/
      theme-family-as-corporation/
      character-kendall-roy/
      episode-s01e01/

  media/
    succession/
      s01/
```

The final reviewed `index.mdx`, metadata YAML, and selected screenshots are committed. Raw research blobs and intermediate LLM outputs are not.

## 18. Episode Inputs and Subtitles

The episode workflow should use subtitles as the canonical dialogue source.

Do not rely on internet scripts as the primary text. They are often unavailable, inaccurate, or based on earlier drafts.

Use:

- local subtitle file extracted from the episode
- web research blob
- series thesis essay
- relevant theme essays
- relevant character essays
- house style guide

Subtitles provide:

- aired dialogue
- timestamps
- searchable text
- quote verification
- anchors for screenshots

They do not provide screen direction, but that is acceptable because the show itself and extracted screenshots provide visual evidence.

## 19. Screenshot Workflow

Screenshots are part of the episode workflow only.

Use PySceneDetect or similar tooling to extract candidate frames from the local episode file. Then feed the completed article plus candidate images into a vision-capable LLM to select screenshots that support specific analytical claims.

Screenshots should be:

- fair-use critical images
- analytically necessary
- non-decorative
- limited in number
- captioned with interpretation
- stored only after final selection

The article should be written first. Screenshots should be inserted afterward to support the already-written analysis.

## 20. Review Philosophy

The reviewer is not a second critic. It is a guardrail.

The reviewer should catch:

- obvious LLM slop
- generic claims
- recap padding
- banned phrases
- inconsistent framing
- unsupported factual claims
- invented dialogue
- overquoting
- public citation clutter
- weak connection to the series thesis
- weak connection to relevant themes and characters
- lack of full-series rewatch value

The review output should be concrete:

```txt
PASS
PASS_WITH_NOTES
FAIL
```

A failed review triggers rewrite. Allow up to two review/rewrite loops.

## 21. SEO

SEO should be basic and tasteful.

Do not let SEO drive the writing.

Each public page should have:

- title
- meta description
- canonical URL
- Open Graph metadata
- sitemap inclusion
- internal navigation where appropriate

Episode page title example:

```txt
Succession S01E01 Analysis: Celebration
```

Avoid generic titles like:

```txt
Succession Season 1 Episode 1 Recap
```

This site is not competing as a recap site.

## 22. Deployment

Recommended MVP deployment:

```txt
Site: Astro
Hosting: Cloudflare Pages or Netlify
DNS: Cloudflare
Assets: committed static assets for MVP
Analytics: Plausible, Cloudflare Web Analytics, or similar
```

No runtime backend is needed.

The pipeline runs locally or in a manually triggered environment.

## 23. CI/CD

Minimum CI for the site:

```txt
on pull request:
  - install site dependencies
  - validate content files
  - build Astro site
  - check for broken internal links
  - verify screenshots referenced in YAML exist
  - verify required metadata exists
```

Minimum content validation:

- every published article has `index.mdx`
- every published article has metadata YAML
- every episode screenshot referenced in `episode.yaml` exists
- every screenshot has alt text
- every screenshot has a caption
- every page has SEO title and description
- no draft articles are published accidentally

Pipeline smoke tests can be minimal:

- workflow schemas validate expected inputs
- review parser handles PASS/PASS_WITH_NOTES/FAIL
- export writes expected files
- subtitle parser works on sample SRT
- screenshot metadata validation works

## 24. Human Review

The system should assist writing, not fully automate publication.

Human review remains necessary for:

- final editorial judgment
- verifying the article is not generic
- checking that claims sound right
- checking screenshot choices
- checking image captions
- checking that the article does not overquote
- checking that the piece is actually worth reading

The final publishing step should be deliberate.

## 25. Legal and Rights Posture

This project should avoid functioning as a substitute for watching the show.

### Dialogue

- Use short quotes only.
- Do not reproduce long stretches of dialogue.
- Do not publish transcript-like passages.
- Treat subtitles as internal source material, not public content.

### Screenshots

Screenshots should be used for criticism and commentary.

Rules:

- screenshots must support specific analysis
- no decorative galleries
- no excessive frame extraction
- captions should be analytical
- avoid using screenshots as mere visual filler

### Scripts

Online scripts are optional and unreliable.

If used, label them internally as draft/shooting/final when known.

The preferred canonical dialogue source is the subtitle file extracted from the aired episode.

### External Sources

Research blobs may include external source text and URLs internally.

Do not republish articles.

Do not expose large amounts of source text.

Do not turn the public site into a source archive.

## 26. Minimal Implementation Plan

### Phase 0: Static Site and Content Contract

Build:

- Astro site shell
- content collections for shows, about essays, themes, characters, and episodes
- show page
- general article page
- episode page
- previous/next episode nav
- spoiler notice
- screenshot component
- basic styles
- content validation script

### Phase 1: Series Thesis Workflow

Build:

- series thesis workflow schema
- research/draft/review/rewrite/export flow
- prompts for series thesis
- export to `content/shows/<show>/about/...`

Run for:

```txt
What Succession Is About
```

### Phase 2: Theme and Character Workflows

Build:

- theme essay workflow
- character essay workflow
- prompt files and review checklists for each
- exports to `themes/` and `characters/`

Generate a small foundation set before episodes.

### Phase 3: Episode Essay Workflow

Build:

- subtitle ingestion
- episode research blob
- context selection from series/theme/character essays
- episode draft/review/rewrite/export

Run on:

```txt
S01E01 Celebration
S01E02 Shit Show at the Fuck Factory
S01E03 Lifeboats
```

### Phase 4: Screenshot Selection

Build:

- PySceneDetect candidate generation
- candidate manifest
- LLM screenshot selection
- copying selected screenshots into `content/`
- generating screenshot metadata
- inserting screenshot tags into MDX

## 27. Final Architecture Summary

The project has three layers:

```txt
1. Public static site
   Astro renders committed static content.

2. Static content contract
   MDX, YAML, and selected screenshots live in content/.

3. Offline generation pipeline
   Python creates layered critical essays and episode analyses from research, style guidance, subtitles, upstream context, and local media.
```

The public site is intentionally simple.

The pipeline is intentionally offline and explicit.

The editorial quality comes from:

- series-first interpretation
- theme vocabulary
- character frameworks
- subtitle-grounded episode analysis
- web research blobs
- strong house style
- mechanical anti-slop review
- screenshot discipline
- human final review

The project succeeds if each episode essay feels like part of a coherent rewatch companion: specific, rewatch-aware, visually attentive, and grounded in a stable theory of the whole show.
