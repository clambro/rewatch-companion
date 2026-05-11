---
name: commit
description: "Use when the user asks to commit, save changes, or create a git commit. Stages all changes and commits with an auto-generated message."
---

# Commit Changes

## Workflow

1. Inspect current state by running:
   - `git status` to see what's changed
   - `git diff HEAD` to review the actual changes
2. Stage all changes: `git add -A` (unless a specific subset was requested)
3. Generate a commit message with:
   - a concise subject line
   - a short body explaining the key changes and why
4. Commit using the command tool, which will automatically prompt the user for confirmation. The sandbox environment will not work for this.

## Rules

- Always include both a subject and a brief body
- Keep the subject short and descriptive
- Keep the body concise and focused on the key changes
- No footers or signatures
- Never mention the AI agent or its provider
- Do not credit yourself
- Never use `--no-verify` unless the user explicitly instructs you to do so
