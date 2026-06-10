---
name: essay-metadata-tightening
description: "Use when asked to tighten deks, subtitles, SEO descriptions, or image alt text for a collection of essays. Especially useful for article.yaml metadata where deks must be short plain-text companion lines and alt text must describe the actual image after visual inspection."
---

# Essay Metadata Tightening

Use this skill when editing metadata for a collection of essays, especially `article.yaml` files with `seo.description` and `hero_image.alt`.

The goal is metadata that is sharp, publishable, and accurate:

- Deks should entice the reader and clarify the article’s angle.
- Alt text should describe the image, not interpret the essay.

## Workflow

1. Read the essay collection before editing metadata.
   - Understand each essay’s title, thesis, and distinguishing angle.
   - Compare the deks across the collection so they do not all use the same structure.
   - Avoid making every dek a miniature thesis statement with the same cadence.

2. Tighten deks first.
   - Keep each dek a single short plain-text sentence meant to be read alongside the title.
   - Do not use Markdown, italics, links, quotes as decoration, or other formatting.
   - Do not restate the title.
   - Do not summarize the entire essay.
   - Make the reader understand what they are getting into.
   - Prefer concrete stakes over abstract importance.
   - Cut padding such as “this essay explores,” “the show examines,” and “a look at.”

3. Inspect every image before editing alt text.
   - Use the local image viewer when the image exists in the repo.
   - Do not infer the image from the article title, slug, source URL, or previous alt text.
   - If the image is missing or cannot be inspected, say so and do not invent visual details.

4. Write alt text as image description.
   - Name visible people only when they are recognizable or already contextually obvious.
   - Describe the action, setting, and important visual relationship.
   - Keep it concise, usually one sentence.
   - Do not describe the essay’s argument.
   - Do not write promotional captions.
   - Do not include source credit, URLs, or licensing language.
   - Avoid empty alt fields unless the image is purely decorative and the site pattern supports that. In this repo, do not leave blanks.

5. Preserve metadata boundaries.
   - Do not change titles, slugs, image paths, or article body unless explicitly asked.
   - Do not add external image URLs to public YAML.
   - Do not add rationale or internal selection notes.

6. Validate.
   - Run the formatter on edited metadata files.
   - For YAML, run a YAML check when available.
   - Search for blank `alt:` and blank `description:` fields before finishing.
   - Summarize the changed metadata and checks run.

## Dek Heuristics

Prefer:

- “Walt’s claim to provide for his family becomes the clearest evidence against him.”
- “Every change in Breaking Bad leaves work, evidence, and damage behind.”

Avoid:

- “This essay explores how Walt uses family as an excuse.”
- “An analysis of Breaking Bad’s themes of change and consequence.”
- “Breaking Bad is not just about transformation; it is about consequence.”

## Alt Text Heuristics

Prefer:

- “Walt rolls a barrel through the desert while a body lies in the sand nearby.”
- “A charred pink teddy bear floats underwater while Walt looks down from above the pool.”

Avoid:

- “An image representing consequence in Breaking Bad.”
- “A powerful scene from Breaking Bad.”
- “Breaking Bad promotional image.”
