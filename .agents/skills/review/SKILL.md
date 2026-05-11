---
name: review
description: "Use when the user asks for a code review, PR review, or feedback on their branch changes. Diffs the current branch against main and reviews all changes against project standards."
---

# Code Review

## Workflow

1. Gather context by running:
   - `git branch --show-current` to identify the current branch
   - `git log main..HEAD --oneline` to see commits on this branch
   - `git diff main...HEAD` to get the full diff
2. Read project standards before reviewing:
   - `AGENTS.md` - Code standards and quality requirements
   - Check the `docs/` folder for other relevant documentation
3. Review all changes against those standards. Also check for:
   - Obvious bugs or logic errors
   - Dead code or commented-out code
   - Anything else you feel is important
4. Report findings using the output format below.

## Output Format

For each issue found:

1. Assign a number for easy reference
2. Link the file path and line number
3. Give severity: 🔴 Problem | 🟡 Suggestion | 💭 Nitpick
4. Describe the issue
5. Briefly suggest a fix (if applicable)

Group issues by file. End with a summary of overall assessment.
