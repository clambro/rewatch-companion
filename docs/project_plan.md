# Rewatch Companion Project Proposal

## 1. Project Summary

This project is a static website containing serious, full-series, episode-by-episode rewatch essays for television shows that reward close analysis.

The initial target show is **Succession**.

The site is not a recap site. It is not a first-watch guide. It is not a fandom wiki. It is a polished rewatch companion for viewers who have already finished the series and want to understand how each episode works: dramatically, thematically, visually, musically, structurally, and in relation to the full series.

Each episode page should feel like an intelligent critical essay written after the entire show is complete.

The core product promise:

> A full-series rewatch companion for serious viewers: episode-by-episode essays that explain what each episode is doing, why it matters, and how it connects to the whole show.

The public website should be simple, fast, static, and tasteful. The content generation pipeline should be offline, Python-based, and used only to generate static content. There should be no runtime backend serving article data.

---

## 2. Goals

### Primary Goals

1. Build a static front end that renders polished episode essays.
2. Build a minimal offline Python content pipeline that generates draft episode essays from:
   - subtitle files extracted from the episode,
   - web research collected by a web-enabled LLM,
   - house style instructions,
   - full-series rewatch framing.
3. Support up to two LLM review/rewrite loops to reduce obvious AI slop.
4. Extract fair-use screenshots from local episode files using PySceneDetect and/or `ffmpeg`.
5. Use an LLM to select and insert relevant screenshots into completed essays.
6. Keep raw research, intermediate drafts, and media processing artifacts outside version control.
7. Publish only reviewed static content into the repo’s `content/` directory.

### Non-Goals for MVP

Do **not** build:

- user accounts
- comments
- CMS
- dynamic personalization
- search beyond basic site search, if any
- paid membership
- glossary
- motif database
- character database
- source drawer
- public citation system
- runtime API
- database-backed public site
- automated publication without human review
- multi-show architecture beyond what is naturally supported by folders

The MVP is about producing a small number of excellent episode essays and validating the workflow.

---

## 3. Editorial Positioning

### What This Site Is

A **full-series rewatch guide**.

Every essay assumes the reader has already seen the entire series. Spoilers are allowed throughout. The point is to understand an episode with full knowledge of where the series goes.

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

> Could a smart viewer who has already watched the episode twice still learn something?

If the answer is no, the article should not be published.

---

## 4. Initial Content Scope

The first show should be **Succession**.

The first target episode path should be:

```txt
/shows/succession/episodes/s01/e01-celebration/
````

The first content milestone should be three polished essays:

```txt
content/shows/succession/episodes/s01/e01-celebration/
content/shows/succession/episodes/s01/e02-shit-show-at-the-fuck-factory/
content/shows/succession/episodes/s01/e03-lifeboats/
```

Only after the workflow proves itself should the project expand to the rest of the show.

---

## 5. Monorepo Structure

The repo contains two mostly unrelated codebases:

1. `frontend/` — the Astro static site.
2. `pipeline/` — the Python offline content generation pipeline.

They live in the same repo for convenience, but they should not be tightly coupled.

The only real contract between them is the static content in `content/`.

```txt
rewatch/
  frontend/
    package.json
    astro.config.mjs
    src/
      pages/
      layouts/
      components/
      styles/
      assets/
    public/

  pipeline/
    pyproject.toml
    README.md
    src/
      rewatch_pipeline/
        __init__.py
        cli.py
        config.py
        models.py
        subtitles.py
        research.py
        generate.py
        review.py
        screenshots.py
        export.py
        llm.py
        utils.py
    prompts/
      research.md
      write_episode.md
      review.md
      rewrite.md
      insert_screenshots.md
    style/
      house.md
      succession.md

  content/
    shows/
      succession/
        show.yaml
        episodes/
          s01/
            e01-celebration/
              index.mdx
              episode.yaml
              screenshots/
                001-logan-opening.webp
                002-kendall-car.webp
                003-baseball.webp
            e02-shit-show-at-the-fuck-factory/
              index.mdx
              episode.yaml
              screenshots/

  scripts/
    dev-frontend.sh
    run-episode.sh
    validate-content.sh

  .local/
    research/
    runs/
    media/

  .github/
    workflows/
      frontend.yml
      pipeline-smoke.yml

  README.md
```

The `.local/` directory must be gitignored. It is where raw research, intermediate drafts, video-derived artifacts, scene candidates, and run logs live.

---

## 6. Public Site Architecture

The public site should be static-first.

Use Astro for the front end.

The front end should do only the following:

1. Render show landing pages.
2. Render episode article pages.
3. Render previous/next navigation.
4. Render spoiler warnings.
5. Render screenshots.
6. Render basic SEO metadata.
7. Render restrained ad slots.
8. Generate a sitemap.

The front end should not:

* query a database
* call the generation pipeline
* fetch external sources at runtime
* expose research blobs
* expose review artifacts
* expose citations
* dynamically generate content

### Front-End Directory

```txt
frontend/src/
  pages/
    index.astro
    shows/[show]/index.astro
    shows/[show]/episodes/[season]/[episode]/index.astro

  layouts/
    BaseLayout.astro
    ShowLayout.astro
    EpisodeLayout.astro

  components/
    EpisodeNav.astro
    SpoilerNotice.astro
    Screenshot.astro
    ArticleToc.astro
    AdSlot.astro

  styles/
    global.css
```

### URL Structure

Episode URLs should be cleanly organized by show, season, and episode:

```txt
/shows/succession/
/shows/succession/episodes/s01/e01-celebration/
/shows/succession/episodes/s01/e02-shit-show-at-the-fuck-factory/
/shows/succession/episodes/s02/e01-the-summer-palace/
```

The file structure should mirror the URL structure:

```txt
content/shows/succession/episodes/s01/e01-celebration/
  index.mdx
  episode.yaml
  screenshots/
```

---

## 7. Static Content Contract

The `content/` directory is the publishing contract.

Everything in `content/` should be safe to commit.

Raw research, raw subtitles, local episode files, generated contact sheets, PySceneDetect scene images, and intermediate drafts should not be committed.

### Show Metadata

Example:

```yaml
# content/shows/succession/show.yaml

title: "Succession"
slug: "succession"
spoiler_policy: "Full-series spoilers throughout. These essays are written for rewatching."

seasons:
  - season: 1
    episodes:
      - code: "S01E01"
        title: "Celebration"
        path: "episodes/s01/e01-celebration"
      - code: "S01E02"
        title: "Shit Show at the Fuck Factory"
        path: "episodes/s01/e02-shit-show-at-the-fuck-factory"
      - code: "S01E03"
        title: "Lifeboats"
        path: "episodes/s01/e03-lifeboats"
```

This file should be enough for the front end to build the show landing page and compute previous/next episode links.

### Episode Metadata

Example:

```yaml
# content/shows/succession/episodes/s01/e01-celebration/episode.yaml

show: succession
season: 1
episode: 1
code: "S01E01"
title: "Celebration"
slug: "e01-celebration"
air_date: "2018-06-03"

writer:
  - Jesse Armstrong

director:
  - Adam McKay

status: published

seo:
  title: "Succession S01E01 Analysis: Celebration"
  description: "A full-series rewatch analysis of Succession's pilot: Logan's body, Kendall's false coronation, Roman's baseball cruelty, and the family business of humiliation."

spoiler_policy: "Full-series spoilers throughout."

screenshots:
  - id: "logan-opening"
    file: "screenshots/001-logan-opening.webp"
    alt: "Logan Roy stands disoriented in a dark hallway."
    caption: "The series begins by making Logan's authority inseparable from bodily decline."
    purpose: "Critical analysis of the opening image."

  - id: "baseball"
    file: "screenshots/003-baseball.webp"
    alt: "Roman Roy stands near the child at the family baseball game."
    caption: "The baseball sequence turns wealth into a private cruelty machine."
    purpose: "Critical analysis of the episode's class politics."

ads:
  enabled: true
  density: low
```

### Episode Article

Example:

```mdx
---
title: "Celebration"
dek: "The pilot introduces succession not as a corporate process, but as a family ritual corrupted by power."
---

## The episode’s move

The pilot is not primarily asking who will inherit Waystar. It is asking what the Roy children have already inherited.

<Screenshot id="logan-opening" />

...

## Roman and the baseball scene

...

<Screenshot id="baseball" />

...
```

The front end should resolve `<Screenshot id="...">` against `episode.yaml`.

---

## 8. Spoiler Policy

All episode essays are explicitly written for rewatching.

The site should display a spoiler notice on every episode page:

> Full-series spoilers throughout. This essay assumes you have watched the entire show.

There is no first-watch-safe mode.

However, avoid putting major finale spoilers in:

* page titles
* meta descriptions
* social sharing previews
* Open Graph descriptions

The article body can spoil freely.

---

## 9. Public Citations and External Links

The public site should not become a mess of references.

Readers are assumed to have watched the episode. They do not need academic-style citations.

Do not include public citations unless unavoidable.

External links should be rare and intentional. Examples of acceptable external links:

* an official source
* an essential interview
* a major source directly relevant to a claim
* a legally necessary attribution link

The research blob used internally may contain URLs and source references, but those should not normally be surfaced in the final article.

The final article should read as an essay, not as a literature review.

---

## 10. Article Structure

Each article should be specific to the episode, but a loose recurring structure is useful.

Suggested shape:

```md
# Succession S01E01 “Celebration” Analysis

Introductory thesis.

## The episode’s move

## Logan’s body and the limits of reality-making

## Kendall’s false coronation

## The birthday as corporate theater

## Roman and the baseball scene

## Tom, Greg, and downward humiliation

## Music and sound

## Full-series echoes

## Why it matters
```

Not every article needs exactly these headings. The structure should adapt to the episode.

Every article should answer:

1. What is this episode doing structurally?
2. What does it reveal about the characters?
3. What visual, musical, or formal choices matter?
4. What changes when the episode is viewed after the finale?
5. Why does this episode matter to the whole series?

---

## 11. House Style Guide

The house style should be clear, concrete, and allergic to generic recap language.

### Reader

The reader is smart, attentive, and has watched the full series.

The reader does not need basic plot summary.

### Mission

Write full-series rewatch essays that explain how the episode works.

### Default Move

Do not say what happened. Say what the episode is doing.

Bad:

> Kendall goes to the Vaulter meeting and tries to buy the company.

Good:

> The Vaulter meeting shows Kendall’s basic problem: he can identify the future of the business, but he cannot make others believe he has inherited Logan’s authority.

### Voice

The voice should be:

* specific
* declarative
* analytical
* occasionally sharp
* readable
* non-academic
* non-fannish
* non-clickbaity

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

### Music Rule

Discuss music and sound when there is something specific to say.

Do not invent cue-level claims.

Do not force a music section if the episode offers little and the research blob has nothing useful. But for a show like Succession, music and sound will often be relevant.

### Screenshot Rule

A screenshot must support an analytical claim.

Decorative screenshots are not allowed.

---

## 12. Content Pipeline Philosophy

The content pipeline should be simple.

It exists only to generate static content.

It should not power the website.

It should not expose sources publicly.

It should not maintain a complex source database for MVP.

It should not produce a public citation graph.

The basic idea:

```txt
episode video + subtitles
        ↓
web research blob
        ↓
generation prompt
        ↓
review pass
        ↓
rewrite pass
        ↓
optional second review/rewrite
        ↓
final MDX
        ↓
scene-detected screenshot candidates
        ↓
LLM selects/inserts screenshots
        ↓
human spot check
        ↓
static content export
```

Raw research and intermediate artifacts should live outside version control.

---

## 13. Pipeline Directory Structure

```txt
pipeline/
  pyproject.toml
  README.md

  src/
    rewatch_pipeline/
      __init__.py
      cli.py
      config.py
      models.py
      subtitles.py
      research.py
      generate.py
      review.py
      screenshots.py
      export.py
      llm.py
      utils.py

  prompts/
    research.md
    write_episode.md
    review.md
    rewrite.md
    insert_screenshots.md

  style/
    house.md
    succession.md
```

Runtime artifacts go in `.local/`:

```txt
.local/
  research/
    succession/
      s01e01/
        blob.md

  runs/
    succession/
      s01e01/
        2026-05-10-1430/
          subtitles_clean.txt
          research_blob.md
          draft_1.md
          review_1.md
          draft_2.md
          review_2.md
          final.md
          scene_candidates/
          screenshot_selection.json

  media/
    succession/
      s01/
        # optional symlinks or local references only
```

`.local/` must be gitignored.

---

## 14. Pipeline Inputs

For each episode, the pipeline should accept:

1. show slug
2. season number
3. episode number
4. episode title
5. local video path
6. local subtitle path, or video path from which subtitles can be extracted
7. output content path

Example command:

```bash
python -m rewatch_pipeline run succession s01e01 \
  --title "Celebration" \
  --video "/Volumes/TV/Succession/S01/Succession.S01E01.mkv" \
  --subtitles "/Volumes/TV/Succession/S01/Succession.S01E01.srt" \
  --out "content/shows/succession/episodes/s01/e01-celebration"
```

---

## 15. Subtitles as Script Replacement

The pipeline should use subtitle files as the canonical dialogue source.

This is preferable to scraping scripts from the internet, which may be unavailable, unreliable, or based on early drafts.

Subtitles provide:

* aired dialogue
* timestamps
* searchable text
* approximate scene structure
* anchors for line-level analysis
* anchors for screenshot timing

Subtitles do not provide:

* action lines
* blocking
* scene descriptions
* tone notes
* deleted lines
* alternate script versions

That is acceptable. The site analyzes the aired episode, not the screenplay.

### Extracting Subtitles

Inspect video streams:

```bash
ffprobe -hide_banner Succession.S01E01.mkv
```

Extract first subtitle stream:

```bash
ffmpeg -i Succession.S01E01.mkv -map 0:s:0 subtitles.srt
```

Extract another subtitle stream if needed:

```bash
ffmpeg -i Succession.S01E01.mkv -map 0:s:1 subtitles.srt
```

Text subtitle formats like `.srt` and `.vtt` are preferred.

Image-based subtitles such as PGS may require OCR and should be avoided for MVP if possible.

### Clean Subtitle Format

Convert SRT into a clean internal text format:

```txt
[00:01:44.230 → 00:01:46.100]
Where am I?

[00:07:12.050 → 00:07:15.900]
I’m gonna need to be on point today.
```

The writer prompt should treat this as the canonical dialogue record.

---

## 16. Web Research Blob

The research step should use a web-enabled LLM.

The goal is to collect useful context, not to write the essay.

The research blob may include:

* serious criticism
* creator interviews
* cast interviews
* composer interviews
* music/sound discussion
* production context
* notable interpretations
* consensus readings
* dissenting readings
* warnings about unreliable sources
* useful facts to verify manually

The blob should be stored outside version control:

```txt
.local/research/succession/s01e01/blob.md
```

The public article should not expose the blob or normally link to the sources.

### Research Prompt Skeleton

```txt
Research Succession S01E01 “Celebration” for a full-series rewatch essay.

Collect:
- serious criticism
- interviews with creators/cast/composer
- music/sound discussion
- production context
- notable interpretations
- consensus readings
- dissenting readings
- details useful for a retrospective essay

Do not write the essay.

Return a structured research blob with internal source names and URLs.

Prefer:
- primary sources
- high-quality criticism
- sources with real interpretive value

Avoid:
- generic plot recap
- SEO recap farms
- unsourced fan claims unless clearly labeled
```

---

## 17. Article Generation

The writer LLM receives:

1. episode metadata
2. cleaned subtitle transcript
3. web research blob
4. house style guide
5. show-specific style/context note
6. article requirements

The writer should output MDX-compatible article prose without public citations.

### Writer Prompt Skeleton

```txt
Write a full-series rewatch analysis of Succession S01E01 “Celebration.”

Audience:
- has watched the full series
- does not need a recap
- wants to understand why the episode matters

Use:
- the subtitle transcript as canonical dialogue evidence
- the research blob for production, music, and critical context
- the house style guide

Do not:
- write a plot recap
- include public citations
- mention the research blob
- overquote dialogue
- use generic LLM phrases
- invent dialogue
- invent visual details not supported by the episode, screenshots, subtitles, or research notes
- preserve first-watch surprise

Target:
- a polished critical essay
- full-series spoiler framing
- concrete claims
- minimal summary
- strong episode-specific thesis
```

---

## 18. Review and Rewrite Loop

The pipeline should support up to two review/rewrite loops.

Pseudo-flow:

```python
draft = write_article(inputs)

for _ in range(2):
    review = review_article(draft)

    if review.status == "PASS":
        break

    draft = rewrite_article(draft, review)

final = draft
```

Intermediate drafts may be saved in `.local/runs/...` for sanity checking, but they should not be committed.

The reviewer should be mechanical and style-focused. It is not there to produce a second essay.

### Reviewer Scope

The reviewer should catch:

* obvious LLM slop
* generic thesis
* too much recap
* banned phrases
* weak episode specificity
* invented dialogue
* unsupported factual claims
* excessive quotation
* public citations or source clutter leaking into the article
* first-watch framing
* lack of full-series retrospective value
* bad or missing discussion of craft/form/music when relevant
* repetitious sentence structures
* empty abstractions

### Review Output Format

```md
# Review result: FAIL

## Blocking issues

1. Generic thesis
The opening says the episode "explores power, family, and betrayal." Replace this with a concrete claim about the birthday ritual becoming a succession test.

2. Too much recap
The Vaulter section summarizes what happens without explaining what the negotiation reveals about Kendall's borrowed model of authority.

3. Banned phrases
Remove:
- "sets the stage"
- "serves as a reminder"
- "power dynamics"

## Non-blocking issues

1. Music section is thin.
Add one paragraph on how the score frames the Roys as mock-dynastic.

## Required revisions

- Replace the intro.
- Cut recap from the Vaulter section.
- Add one concrete music/sound paragraph.
- Remove all banned phrases.
```

The reviewer should return one of:

```txt
PASS
PASS_WITH_NOTES
FAIL
```

Only `FAIL` triggers a required rewrite.

---

## 19. Screenshot Workflow

Screenshots should mostly be fair-use screenshots extracted from the episode itself.

The workflow:

```txt
local episode file
  ↓
PySceneDetect scene detection
  ↓
candidate images
  ↓
completed article
  ↓
vision-capable LLM selects relevant screenshots
  ↓
selected screenshots copied/exported
  ↓
MDX screenshot tags inserted
  ↓
human spot check
```

Screenshots are selected after the article is written because they should support the essay’s claims. They are not decorative.

### PySceneDetect Command

Example:

```bash
scenedetect \
  -i Succession.S01E01.mkv \
  detect-content \
  list-scenes \
  save-images \
    --num-images 3 \
    --webp \
    --quality 80 \
    --width 960 \
    -o .local/runs/succession/s01e01/scenes
```

This produces representative frames from detected scenes.

### LLM Screenshot Selection Prompt

The screenshot-selection LLM receives:

1. final article
2. candidate image list
3. candidate images
4. screenshot rules

It should return:

```json
{
  "selected": [
    {
      "candidate_id": "scene-002-img-001",
      "output_filename": "001-logan-opening.webp",
      "insert_after_heading": "Logan’s body and the limits of reality-making",
      "alt": "Logan Roy stands disoriented in a dark hallway.",
      "caption": "The pilot begins by making Logan's authority inseparable from bodily decline.",
      "reason": "Supports the section's claim about sovereignty and bodily failure."
    }
  ]
}
```

### Screenshot Rules

* Use screenshots only when they support analysis.
* No decorative screenshots.
* No galleries.
* Avoid near-duplicates.
* Prefer visually clear frames.
* Prefer moments the article directly discusses.
* Use 3–6 screenshots for a long article.
* Compress images.
* Store only final selected screenshots in `content/`.

### Final Screenshot File Structure

```txt
content/shows/succession/episodes/s01/e01-celebration/
  screenshots/
    001-logan-opening.webp
    002-kendall-car.webp
    003-baseball.webp
```

### MDX Insertion

The pipeline can insert screenshot components like:

```mdx
<Screenshot id="logan-opening" />
```

The screenshot metadata lives in `episode.yaml`.

---

## 20. Ad Strategy

Ads should be out of the way.

The site should feel like a serious critical publication, not an ad farm.

Recommended ad placements:

### Desktop

* one right-rail ad after the table of contents
* one in-article ad after 35–45% scroll
* one footer ad

### Mobile

* one in-article ad after section 3 or 4
* one footer ad

### Never Use

* pop-ups
* interstitials
* sticky video
* autoplay video
* ads above the title
* ads between title and intro
* ads between spoiler warning and first paragraph

Build an `AdSlot.astro` component but allow ads to be disabled globally or per episode.

Example:

```yaml
ads:
  enabled: true
  density: low
```

For MVP, ads can remain disabled until there is enough content and traffic to justify them.

---

## 21. SEO

SEO should be basic and tasteful.

Do not let SEO drive the writing.

Each episode page should have:

* title
* meta description
* canonical URL
* Open Graph metadata
* sitemap inclusion
* previous/next links
* structured episode metadata where appropriate

Example title:

```txt
Succession S01E01 Analysis: Celebration
```

Example description:

```txt
A full-series rewatch analysis of Succession's pilot: Logan's body, Kendall's false coronation, Roman's baseball cruelty, and the family business of humiliation.
```

Avoid generic titles like:

```txt
Succession Season 1 Episode 1 Recap
```

This site is not competing as a recap site. It is targeting deeper searches:

```txt
Succession Celebration analysis
Succession pilot meaning
Succession baseball scene analysis
Succession music analysis
Succession rewatch guide
```

---

## 22. Deployment

Recommended MVP deployment:

```txt
Frontend: Astro
Hosting: Cloudflare Pages or Netlify
DNS: Cloudflare
Assets: committed static assets for MVP
Analytics: Plausible, Cloudflare Web Analytics, or similar
Ads: AdSense later
```

No runtime backend is needed.

The pipeline runs locally or in a manually triggered environment.

---

## 23. CI/CD

Minimum CI for the front end:

```txt
on pull request:
  - install frontend dependencies
  - validate content files
  - build Astro site
  - check for broken internal links
  - verify screenshots referenced in YAML exist
  - verify required metadata exists
```

Minimum content validation:

* every published episode has `index.mdx`
* every published episode has `episode.yaml`
* every screenshot referenced in `episode.yaml` exists
* every screenshot has alt text
* every screenshot has a caption
* every episode has SEO title and description
* every episode has spoiler policy
* no draft episodes are published accidentally

Pipeline smoke tests can be minimal:

* subtitle parser works on sample SRT
* review parser handles PASS/FAIL
* export function writes expected files
* screenshot metadata validation works

---

## 24. Human Review

The system should assist writing, not fully automate publication.

Human review remains necessary for:

* final editorial judgment
* verifying the article is not generic
* checking that claims sound right
* checking screenshot choices
* checking image captions
* checking that the article does not overquote
* checking that the piece is actually worth reading

The final publishing step should be deliberate.

---

## 25. Legal and Rights Posture

This project should avoid functioning as a substitute for watching the show.

### Dialogue

* Use short quotes only.
* Do not reproduce long stretches of dialogue.
* Do not publish transcript-like passages.
* Treat subtitles as internal source material, not public content.

### Screenshots

Screenshots should be used for criticism and commentary.

Rules:

* screenshots must support specific analysis
* no decorative galleries
* no excessive frame extraction
* captions should be analytical
* avoid using screenshots as mere visual filler

### Scripts

Online scripts are optional and unreliable.

If used, label them internally as draft/shooting/final when known.

The preferred canonical dialogue source is the subtitle file extracted from the aired episode.

### External Sources

Research blobs may include external source text and URLs internally.

Do not republish articles.

Do not expose large amounts of source text.

Do not turn the public site into a source archive.

---

## 26. Minimal Implementation Plan

### Phase 0: Static Front-End Skeleton

Build:

* Astro app
* show page
* episode page
* previous/next nav
* spoiler notice
* screenshot component
* basic styles
* content validation script

Create one hand-authored or manually pasted `index.mdx` to validate rendering.

### Phase 1: Subtitle-Based Article Generation

Build Python pipeline support for:

* loading SRT
* cleaning subtitles
* generating web research blob with web-enabled LLM
* generating draft article
* running review
* running rewrite
* exporting final MDX

Run on `Succession S01E01`.

### Phase 2: Screenshot Selection

Build support for:

* PySceneDetect candidate generation
* candidate manifest
* LLM screenshot selection
* copying selected screenshots into `content/`
* generating screenshot metadata
* inserting `<Screenshot id="...">` tags into MDX

### Phase 3: First Three Essays

Produce:

```txt
S01E01 Celebration
S01E02 Shit Show at the Fuck Factory
S01E03 Lifeboats
```

Manually review each.

Use these to assess:

* quality
* pipeline reliability
* article structure
* screenshot usefulness
* front-end readability
* production time per episode

### Phase 4: Complete Season 1

If the first three essays work, complete Season 1.

Only then consider expanding further.

---

## 27. Example End-to-End Command

Eventually, one command should run most of the pipeline:

```bash
python -m rewatch_pipeline run succession s01e01 \
  --title "Celebration" \
  --video "/Volumes/TV/Succession/S01/Succession.S01E01.mkv" \
  --subtitles "/Volumes/TV/Succession/S01/Succession.S01E01.srt" \
  --out "content/shows/succession/episodes/s01/e01-celebration"
```

Expected behavior:

1. Clean subtitle transcript.
2. Generate or load research blob.
3. Draft article.
4. Review article.
5. Rewrite if needed.
6. Optionally review/rewrite one more time.
7. Run PySceneDetect.
8. Select screenshots.
9. Export selected screenshots.
10. Insert screenshot components.
11. Write `index.mdx`.
12. Write `episode.yaml`.
13. Save run artifacts in `.local/runs/...`.

---

## 28. Final Architecture Summary

The project has three layers:

```txt
1. Public static site
   Astro renders committed static content.

2. Static content contract
   MDX, YAML, and selected screenshots live in content/.

3. Offline generation pipeline
   Python creates article drafts and screenshot selections from subtitles, research blobs, style guides, and local video files.
```

The public site is intentionally simple.

The pipeline is intentionally disposable and offline.

The editorial quality comes from:

* subtitle-grounded dialogue
* web research blob
* strong house style
* mechanical anti-slop review
* screenshot discipline
* human final review

The project succeeds if each episode essay feels like a serious retrospective companion: specific, rewatch-aware, visually attentive, and worth reading after the viewer has already seen the show.

```
```
