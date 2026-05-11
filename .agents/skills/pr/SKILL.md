---
name: pr
description: "Use when the user wants to create a pull request description or summarize branch changes for a PR. Generates a PR description from the diff against main."
---

# Generate PR Description

## Workflow

1. Gather context by running:
   - `git branch --show-current` to identify the branch
   - `git diff main...HEAD --stat` to see files changed
   - `git log main..HEAD --oneline` to see commit history
   - `git diff main...HEAD` to get the full diff
2. Read relevant documentation for context:
   - `AGENTS.md` - Development standards
   - Any relevant files in the `docs/` folder
3. Look at the commit messages for intent
4. Generate a PR description in this format:

   ## Summary

   [A single paragraph describing what the PR does at a high level]

   [Short bullet points describing the changes]

   ## Changes

   [List of key changes, grouped by area/subject/folder if needed. Details go here, not in the summary section.]

## Rules

- Keep the description concise and focused on what changed and why
- Do not include test plans, footers, signatures, or AI attribution
