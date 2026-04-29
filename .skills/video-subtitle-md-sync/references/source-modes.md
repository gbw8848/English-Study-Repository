# Source Modes

Use this reference to decide which input path is appropriate.

## Supported Now

### 1. Local subtitle file

Best option when the user already exported subtitles manually.

Accepted formats:

- `.srt`
- `.vtt`
- `.txt`

### 2. Video URL with existing captions

Use this when the page exposes subtitles that `yt-dlp` can download.

Good fit for:

- YouTube videos with manual subtitles
- YouTube videos with auto captions
- Other providers supported by `yt-dlp`

## Not Supported Yet

### Local video file without subtitle track

This skill does not yet run speech-to-text on arbitrary local videos. Do not imply otherwise.

When the user still wants this:

- explain the current limitation plainly
- offer to extend the skill with a transcription backend later
- if they only need the Markdown/Git part today, ask them to export `.srt` or `.vtt` first
