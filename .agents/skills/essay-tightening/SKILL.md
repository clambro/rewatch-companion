---
name: essay-tightening
description: "Use when asked to tighten, de-AI, line edit, or improve a collection of essays while preserving their arguments. Especially useful for MDX/Markdown essay sets where the work should include paragraph-level structure, repetition, pacing, and voice rather than only sentence-level copyediting."
---

# Essay Tightening

Use this skill when editing a collection of essays that already exist and should be improved without changing their core arguments.

The goal is not a rewrite. The goal is to make the essays read like considered criticism rather than generated prose: less padding, fewer mechanical paragraph shapes, better flow, more varied emphasis, and cleaner language.

For AI-voice, de-AI, or collection-tightening requests, read [references/ai-writing-tells.md](references/ai-writing-tells.md) before editing. Do not treat it as optional background when the user is explicitly complaining about generated prose.

## Workflow

1. Read the full collection before editing.
   - Identify each essay’s thesis, section structure, recurring examples, and repeated language.
   - Look across the set for duplicated moves, repeated paragraph rhythms, recurring transitions, and essays that solve the same problem the same way.
   - Take brief notes before editing.
   - For AI-tell work, explicitly diagnose the collection before editing: repeated paragraph shapes, stock transitions, tidy landing sentences, generic critical nouns, repeated section logic, and recurring sentence templates.
   - Use search to support the diagnosis. Look for repeated phrases and abstract vocabulary such as `not merely`, `not only`, `becomes`, `reveals`, `clarifies`, `legible`, `available`, `structure`, `role`, `surface`, `system`, `function`, `logic`, `performance`, `claim`, and similar terms that are doing generic interpretive work.

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
   - Do not count small sentence-level substitutions as a real tightening pass when the problem is paragraph rhythm. If the essays share the same setup / explanation / polished-takeaway motion, restructure or combine the paragraphs creating that rhythm.

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
   - Watch for “critical autopilot”: paragraphs that correctly describe an example and then end with a neat abstract verdict.
   - Watch for collection-level repetition, such as every essay opening with the same kind of character entrance, ending with the same clarified thesis, or using the same abstract nouns to describe different characters.

6. Preserve editorial boundaries.
   - Do not change titles, slugs, metadata, image paths, or deks unless asked.
   - Do not introduce citations, footnotes, or source notes into publishable essays unless the local content pattern already uses them.
   - Do not turn literary criticism into plot summary.

7. Validate the edit.
   - Run the relevant formatter for the touched files.
   - For MDX/Markdown in this repo, run Prettier on the edited files.
   - Re-run the tell-oriented search from step 1 and inspect the remaining hits. Some terms may be justified, but repeated hits should be consciously accepted, rewritten, or removed.
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
