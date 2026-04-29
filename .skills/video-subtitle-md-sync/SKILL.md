---
name: video-subtitle-md-sync
description: Export English subtitles from local `.srt`, `.vtt`, or `.txt` files, or from video URLs that already expose captions, into Markdown inside the current repository and optionally commit and push the result to GitHub. Use when Codex needs to turn study-video subtitles into reusable notes, transcript documents, or synced GitHub study records.
---

# Video Subtitle Md Sync

Extract subtitle text, format it into a clean Markdown transcript, and save it into the active Git repository. Use the bundled scripts to keep the workflow deterministic and to avoid rewriting subtitle parsing or Git commands each time.

## Quick Start

Decide the source type first:

- Local subtitle file: use `.srt`, `.vtt`, or `.txt` directly.
- Video URL with published captions: use the URL mode and let the script fetch captions through `yt-dlp`.
- Local video file without subtitles: do not fake it. Ask the user for an exported subtitle file or pause and propose adding a speech-to-text extension later.

Run the exporter from any repository that should receive the Markdown output:

```powershell
py "$env:USERPROFILE\.codex\skills\video-subtitle-md-sync\scripts\export_subtitle_markdown.py" `
  "D:\Videos\lesson-01.en.srt" `
  --repo-root "D:\2_Code\04_英语学习" `
  --title "Lesson 01" `
  --sync
```

URL example:

```powershell
py "$env:USERPROFILE\.codex\skills\video-subtitle-md-sync\scripts\export_subtitle_markdown.py" `
  "https://www.youtube.com/watch?v=VIDEO_ID" `
  --repo-root "D:\2_Code\04_英语学习" `
  --language en `
  --install-missing `
  --sync
```

Blocked YouTube example:

```powershell
py ".\.skills\video-subtitle-md-sync\scripts\export_subtitle_markdown.py" `
  "https://www.youtube.com/watch?v=VIDEO_ID" `
  --repo-root "." `
  --language en `
  --cookies-from-browser chrome
```

## Workflow

### 1. Choose safe inputs

- Prefer local subtitle files when the user already exported them.
- For URLs, use existing captions first. Do not claim full transcription support when captions are absent.
- If the user needs local-video speech-to-text, explain that this skill currently stops at subtitle extraction and Git sync.

### 2. Generate the Markdown file

Use `scripts/export_subtitle_markdown.py`.

Important flags:

- `--repo-root`: target Git repository. Defaults to the current working directory.
- `--output-dir`: defaults to `transcripts`.
- `--title`: override the generated title when the source name is messy.
- `--date`: override the filename date. Format: `YYYY-MM-DD`.
- `--language`: subtitle language for URL mode. Default: `en`.
- `--slug`: force a filename slug when needed.
- `--sync`: run Git add, commit, and push after writing the Markdown file.
- `--install-missing`: allow the exporter to install `yt-dlp` with `pip --user` if URL mode needs it.
- `--cookies-from-browser`: reuse local browser cookies for YouTube videos that block anonymous subtitle requests.

The exporter writes files like:

- `transcripts/2026-04-29-lesson-01.md`

Markdown output includes:

- Title
- Export metadata
- Timestamped transcript lines
- Plain text transcript block for copying into study notes or LLM prompts

### 3. Sync to GitHub

If `--sync` is set, the exporter calls `scripts/sync_to_github.ps1`.

That script:

- stages all changes in the target repo
- skips commit/push when there are no staged changes
- commits with a transcript-specific message unless overridden
- pushes to `origin` on the current branch by default

Run the sync script directly only when you already generated the Markdown file and just need Git sync.

## Dependency Notes

- Local subtitle-file mode uses only the Python standard library.
- URL mode requires `yt-dlp`.
- If `yt-dlp` is missing, either:
  - rerun with `--install-missing`, or
  - install manually with `py -m pip install --target .tools/pydeps yt-dlp`

YouTube-specific note:

- Some public videos block anonymous subtitle fetches even when captions exist.
- In that case, rerun with `--cookies-from-browser chrome` or another local browser profile that can open the video normally.

## References

- Read [references/source-modes.md](references/source-modes.md) when deciding which inputs this skill can handle cleanly.
