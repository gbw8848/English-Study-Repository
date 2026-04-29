---
name: video-subtitle-md-sync
description: Turn pasted English transcript text into a study-ready Markdown review note and sync it to GitHub. Use when the user gives Codex a transcript, subtitle text, or rough English learning content and wants a clean review document rather than a raw dump.
---

# Transcript Review Sync

The job is to turn the user's transcript text into a Markdown note that is useful for English review, then save it in the current repository and sync it to GitHub.

Non-negotiable rules:

- Keep the full transcript content. Do not delete paragraphs just because they feel repetitive.
- Put the full transcript at the top of the Markdown file.
- Reformat hard-wrapped transcript lines into readable paragraphs while preserving all words.
- Add a `Sentence Breakdown` section after `Full Transcript` so the user can study shorter chunks more easily.
- If the user provides a video URL, include a clickable video link near the top of the file.
- Put review notes after the transcript, not before it.

## Default Output Shape

Unless the user asks for a different structure, write the note with these sections:

```markdown
# Title

- Date: YYYY-MM-DD
- Video: [Watch on YouTube](https://...)
- Source: pasted transcript

## Full Transcript

```text
Full original transcript here.
```

## Sentence Breakdown

- Short chunk
- Short chunk

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

```

## Workflow

### 1. Understand the text

- Read the pasted transcript or subtitle text.
- Clean broken line wraps.
- Keep simple markers such as `[music]` only if they help context.
- Break the transcript into study-friendly chunks after the full transcript.

### 2. Turn it into a review note

- Write a short Chinese summary.
- Extract useful words, phrases, and sentence patterns worth reviewing.
- Add concise learning notes after the transcript.
- Preserve the full transcript exactly when the user clearly wants the full wording kept.
- If the user wants help with pausing and reading, make the `Sentence Breakdown` section more fine-grained rather than more compressed.
- Rebuild `Sentence Breakdown` from the latest `Full Transcript` when the note is regenerated.
- Prefer English thought groups rather than fixed-length cuts: split at connectors, new clauses, restarts like `I...`, and short parenthetical phrases such as `as you guys know`.

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

The script writes into a month folder such as `2026-04/` by default and then optionally calls `scripts/sync_to_github.ps1`.

## Important Rule

Do not omit parts of the transcript. The final file should start with the full transcript, include the video link when available, add a `Sentence Breakdown` section for learning, and then continue into review notes someone can study from.
