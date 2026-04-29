---
name: video-subtitle-md-sync
description: Turn pasted English transcript text into a study-ready Markdown review note and sync it to GitHub. Use when the user gives Codex a transcript, subtitle text, or rough English learning content and wants a clean review document rather than a raw dump.
---

# Transcript Review Sync

The job is not to preserve a raw transcript dump. The job is to turn the user's transcript text into a Markdown note that is useful for English review, then save it in the current repository and sync it to GitHub.

## Default Output Shape

Unless the user asks for a different structure, write the note with these sections:

```markdown
# Title

- Date: YYYY-MM-DD
- Source: pasted transcript

## Summary

Short Chinese summary of what the content is about.

## Useful Vocabulary

| Word / Phrase | Meaning | Note |
| --- | --- | --- |

## Useful Expressions

- Expression
- Expression

## Review Notes

- Natural phrasing
- Grammar or collocation notes
- Things worth imitating

## Clean Transcript

Cleaned transcript paragraphs.
```

## Workflow

### 1. Understand the text

- Read the pasted transcript or subtitle text.
- Clean broken line wraps.
- Keep simple markers such as `[music]` only if they help context.

### 2. Turn it into a review note

- Write a short Chinese summary.
- Extract useful words, phrases, and sentence patterns worth reviewing.
- Add concise learning notes instead of dumping everything mechanically.
- Keep the full cleaned transcript at the bottom for reference.

### 3. Save and sync

Use `scripts/save_review_markdown.py` to write the final Markdown into the repo.

Pipe the prepared Markdown through stdin:

```powershell
@'
# Example Title

- Date: 2026-04-29
- Source: pasted transcript

## Summary

...
'@ | py ".\.skills\video-subtitle-md-sync\scripts\save_review_markdown.py" `
  --stdin `
  --repo-root "." `
  --title "Example Title" `
  --sync
```

The script writes into `reviews/` by default and then optionally calls `scripts/sync_to_github.ps1`.

## Important Rule

Do not stop after producing a raw transcript-looking file. The final file should read like a review note someone can study from.
