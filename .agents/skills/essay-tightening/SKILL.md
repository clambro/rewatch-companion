---
name: essay-tightening
description: "Use when asked to tighten, de-AI, line edit, or improve a collection of essays while preserving their arguments. Especially useful for MDX/Markdown essay sets where the work should include paragraph-level structure, repetition, pacing, and voice rather than only sentence-level copyediting."
---

# Essay Tightening

Use this skill when editing a collection of essays that already exist and should be improved without changing their core arguments.

The goal is not a rewrite. The goal is to make the essays read like considered criticism rather than generated prose: less padding, fewer mechanical paragraph shapes, better flow, more varied emphasis, and cleaner language.

For background on common AI-writing tells, see [references/ai-writing-tells.md](references/ai-writing-tells.md) when useful.

## Workflow

1. Read the full collection before editing.
   - Identify each essay’s thesis, section structure, recurring examples, and repeated language.
   - Look across the set for duplicated moves, repeated paragraph rhythms, recurring transitions, and essays that solve the same problem the same way.
   - Take brief notes before editing.

2. Edit one essay at a time, but keep the collection in mind.
   - Preserve the thesis, argument, and evidence unless the user explicitly asks for a rewrite.
   - Do not add new factual claims unless you verify them.
   - Do not flatten distinctive phrasing just because it is unusual.

3. Start at paragraph level.
   - Cut paragraphs that only announce, summarize, or re-explain a point the surrounding example already proves.
   - Combine adjacent paragraphs when they perform one argumentative job.
   - Split only when a paragraph has two real jobs that need separate weight.
   - Remove end-of-section recaps when the section already lands.
   - Vary paragraph function naturally: some paragraphs should advance evidence, some should turn the argument, some should linger on an image, and some should close a section.
   - Avoid fake variation. Do not replace developed paragraphs with punchy one-line blog/reddit-style takeaways.

4. Then tighten sentences.
   - Remove scaffolding phrases such as “the point is,” “this matters because,” “that is why,” and “the show’s irony is” when the sentence can simply make the claim.
   - Replace over-explained contrasts with direct argument.
   - Cut repeated nouns, recycled adjectives, and duplicated clause shapes.
   - Prefer specific verbs over abstract explanatory phrasing.
   - Keep the prose serious and readable. Do not make it chatty.

5. Check for AI voice.
   - Watch for smooth but mechanical paragraphs: setup, explanation, polished takeaway, repeated across the essay.
   - Watch for strings of similarly sized paragraphs with the same internal movement.
   - Watch for generic critical vocabulary that could apply to any show.
   - Watch for over-balanced constructions that keep saying a thing is “not just X but Y.”
   - Watch for conclusions that restate the essay instead of earning a final turn.

6. Preserve editorial boundaries.
   - Do not change titles, slugs, metadata, image paths, or deks unless asked.
   - Do not introduce citations, footnotes, or source notes into publishable essays unless the local content pattern already uses them.
   - Do not turn literary criticism into plot summary.

7. Validate the edit.
   - Run the relevant formatter for the touched files.
   - For MDX/Markdown in this repo, run Prettier on the edited files.
   - Check `git diff --stat` and `git diff --check`.
   - In the final response, summarize the nature of the edits and the checks run.

## Editing Heuristics

Prefer these moves:

- Cut a paragraph that exists only to say what the previous paragraph already demonstrated.
- Fold a “why this matters” paragraph into the example that made it matter.
- Replace repeated final-summary sentences with a sharper transition into the next section.
- Turn a mechanical three-paragraph sequence into one tighter paragraph plus one real development paragraph.
- Keep a strong image or example on the page and remove the explanation orbiting it.

Avoid these moves:

- Rewriting every paragraph in the same shorter style.
- Creating abrupt one-sentence paragraphs just to vary rhythm.
- Removing texture, strangeness, or judgment because it is less efficient.
- Over-polishing until the essay sounds neutral, corporate, or academic by default.
- Making arguments more generic in the name of clarity.
