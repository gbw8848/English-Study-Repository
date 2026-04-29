---
name: video-subtitle-md-sync
description: Turn pasted English transcript text into a study-ready Markdown review note and sync it to GitHub. Use when the user gives Codex a transcript, subtitle text, or rough English learning content and wants a clean review document rather than a raw dump.
---

# Transcript Review Sync

The job is to turn the user's transcript text into a Markdown note that is useful for English review, then save it in the current repository and sync it to GitHub.

Non-negotiable rules:

- Keep the full transcript content inside `Sentence Breakdown`. Do not delete paragraphs just because they feel repetitive.
- Use model judgment first when rewriting the transcript for study. Do not rely on the Python script as the primary source of pause placement.
- Put `Sentence Breakdown` at the top of the Markdown file as the only transcript section.
- Reformat hard-wrapped transcript lines into shadowing-friendly chunks while preserving all words.
- Make `Sentence Breakdown` shadowing-friendly: prefer spoken pauses and thought groups over full grammar analysis.
- If the user provides a video URL, include a clickable video link near the top of the file.
- Put review notes after the transcript, not before it.

## Default Output Shape

Unless the user asks for a different structure, write the note with these sections:

```markdown
# Title

- Date: YYYY-MM-DD
- Video: [Watch on YouTube](https://...)
- Source: pasted transcript

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
- Break the transcript into study-friendly chunks and keep only one transcript section.

### 2. Turn it into a review note

- Use AI-style semantic judgment to decide natural pause points, thought groups, and read-aloud rhythm before saving.
- Write a short Chinese summary.
- Extract useful words, phrases, and sentence patterns worth reviewing.
- Add concise learning notes after the transcript.
- Preserve the full transcript exactly, but present it only through `Sentence Breakdown`.
- If the user wants help with pausing and reading, make the `Sentence Breakdown` section more fine-grained rather than more compressed.
- Rebuild `Sentence Breakdown` from the transcript source when the note is regenerated.
- Prefer English thought groups rather than fixed-length cuts: split at connectors, new clauses, restarts like `I...`, and short parenthetical phrases such as `as you guys know`.
- Prefer chunks that someone can actually read aloud in one breath. Usually that means short spoken units, not long written-style sentences.
- Do not split in places that make shadowing awkward, such as `I like it`, `if you...`, or other tightly connected mini-phrases.
- Treat the script as a fallback saver and section normalizer. If the note already contains a natural AI-written `Sentence Breakdown`, keep it instead of regenerating it mechanically.

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

Do not omit parts of the transcript. The final file should start with `Sentence Breakdown`, include the video link when available, and then continue into review notes someone can study from.

Treat `Sentence Breakdown` as a speaking aid, not just a formatting step. The result should look like natural pause points for imitation and shadowing.
