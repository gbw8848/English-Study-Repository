---
name: video-subtitle-md-sync
description: Format pasted transcript text or local `.txt`, `.srt`, or `.vtt` content into a clean Markdown study document inside the current repository and sync it to GitHub. Use when the user gives Codex a transcript, subtitle text, or rough English study notes and wants them cleaned up, saved, and pushed.
---

# Transcript Markdown Sync

Take raw transcript text, normalize the formatting, save the original text when needed, generate a readable Markdown document, and sync the result to GitHub.

## Quick Start

Use `scripts/format_transcript_markdown.py`.

For pasted transcript text, pipe the content through stdin:

```powershell
@'
Your transcript text here.
'@ | py ".\.skills\video-subtitle-md-sync\scripts\format_transcript_markdown.py" `
  --stdin `
  --repo-root "." `
  --title "Lesson Title" `
  --sync
```

For an existing local text file:

```powershell
py ".\.skills\video-subtitle-md-sync\scripts\format_transcript_markdown.py" `
  ".\notes\lesson-01.txt" `
  --repo-root "." `
  --title "Lesson Title" `
  --sync
```

## Workflow

### 1. Choose the input

- If the user pasted text directly into chat, use `--stdin`.
- If the user already has a local transcript file, pass the file path.
- Accept `.txt`, `.srt`, and `.vtt`.

### 2. Generate the Markdown file

The formatter writes Markdown into `transcripts/` by default.

Important flags:

- `--stdin`: read transcript text from standard input.
- `--repo-root`: target Git repository. Defaults to the current directory.
- `--output-dir`: Markdown output directory. Defaults to `transcripts`.
- `--source-dir`: raw text archive directory for stdin input. Defaults to `sources`.
- `--title`: override the generated document title.
- `--date`: override the filename date. Format: `YYYY-MM-DD`.
- `--slug`: override the filename slug.
- `--sync`: run Git add, commit, and push after writing files.

Markdown output includes:

- Title
- Export metadata
- Cleaned transcript paragraphs
- Plain text block for reuse

### 3. Sync to GitHub

If `--sync` is set, the formatter calls `scripts/sync_to_github.ps1`.

That script:

- stages all repository changes
- skips commit and push if nothing changed
- commits with a transcript-specific message unless overridden
- pushes to `origin` on the current branch by default

## Formatting Rules

- Join hard-wrapped transcript lines into readable paragraphs.
- Preserve simple stage markers such as `[music]`.
- Keep the raw input text when stdin is used so the repository retains the original source.
- Prefer readable paragraphs over one-line-per-wrap transcript output.
