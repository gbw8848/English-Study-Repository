---
name: tiktok-downsub-batch-sync
description: Batch-process TikTok short links into synced English study notes through DownSub and the local video-subtitle-md-sync workflow. Use when the user provides many TikTok links, a BitBrowser/current-browser screenshot, DownSub context, or asks to handle TikTok subtitles one by one without mixing video URLs and transcripts.
---

# TikTok DownSub Batch Sync

## Overview

Use this skill to coordinate the fragile upstream workflow before `video-subtitle-md-sync`: TikTok short links -> TikTok long links -> DownSub TXT subtitles -> one review note per video -> GitHub sync.

The prime directive is correspondence. Never let a transcript, TikTok URL, DownSub page, draft note, or synced file drift away from its source link.

## Required Order

Process videos strictly one at a time:

1. Resolve one short link to one TikTok long link.
2. Download that video's TXT subtitle from DownSub.
3. Create and sync that video's study note with `video-subtitle-md-sync`.
4. Record the saved file path/status.
5. Move to the next link only after the previous sync succeeds or is explicitly marked failed.

Do not batch-generate notes from multiple transcripts in one prompt. Do not download several TXT files and sort them out later.

Keep a running ledger in the user-visible updates or scratch notes:

```text
1. Short: https://www.tiktok.com/t/...
   Long: https://www.tiktok.com/@user/video/...
   DownSub: TXT downloaded / retry used / failed
   Sync: 2026-06/001-...
```

## Link Resolution

Use `scripts/resolve_tiktok_links.py` when convenient:

```powershell
py ".\.skills\02_tiktok-downsub-batch-sync\scripts\resolve_tiktok_links.py" `
  "https://www.tiktok.com/t/ZP8example/" --json
```

The script follows redirects and also returns a clean TikTok URL with query parameters removed.

If not using the script, resolve one link with PowerShell:

```powershell
try {
  $r = Invoke-WebRequest -Uri 'https://www.tiktok.com/t/SHORT/' -MaximumRedirection 5 -TimeoutSec 15 -UseBasicParsing
  $r.BaseResponse.ResponseUri.AbsoluteUri
} catch {
  if ($_.Exception.Response) { $_.Exception.Response.Headers.Location } else { $_.Exception.Message }
}
```

Keep both forms:

- Full long URL: includes TikTok tracking query such as `_r` and `_t`.
- Clean long URL: `https://www.tiktok.com/@user/video/id` with query removed.

Use the full long URL first when it works. If DownSub shows an error page, retry with the clean URL before marking the item failed.

## Browser And DownSub

### Default BitBrowser workspace

Use the `bitbrowser-seo-browser` skill for this workflow. Unless the user explicitly chooses another browser, bind to this BitBrowser workspace:

- Workspace: `6-anyidphoto`
- Profile ID: `a5145d814904441fbc3f60debc17cbfc`
- Profile user-data directory: `D:\1_Program\27bitbrowser\a5145d814904441fbc3f60debc17cbfc`

Never fall back to ordinary Chrome, the Chrome extension browser, or the in-app browser for TikTok/DownSub work. If this BitBrowser profile is not running, ask the user to open `6-anyidphoto`; do not silently switch browsers.

### Discover the real DevTools port

Run the discovery script bundled with `bitbrowser-seo-browser` at the start of every batch. First try the workspace title:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\17137\.codex\skills\bitbrowser-seo-browser\scripts\find-bitbrowser-devtools.ps1" `
  -TitlePattern '6-anyidphoto' -IncludeTabs
```

The visible window title may become the active page title, such as DownSub, so `-TitlePattern` can return no match even when the correct workspace is open. In that case, rerun discovery without a title filter:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File `
  "C:\Users\17137\.codex\skills\bitbrowser-seo-browser\scripts\find-bitbrowser-devtools.ps1" `
  -IncludeTabs
```

Select only the result whose evidence matches the configured profile:

- `CommandLine` contains the profile user-data directory or profile ID.
- A tab URL contains `console.bitbrowser.net` and `id=a5145d814904441fbc3f60debc17cbfc`.
- A tab title is `6-anyidphoto-工作台`.

Use the returned `DevTools.Port` for the current run. A value such as `8841` is temporary and may change after the browser restarts. Never use the `port=54345` value from the BitBrowser console URL as the Chromium DevTools port.

If multiple BitBrowser results remain and none uniquely matches this profile, stop and ask the user instead of choosing the first available browser.

Preferred browser flow:

1. Attach Playwright to `http://127.0.0.1:<DevTools.Port>`.
2. Reuse the existing DownSub tab in that BitBrowser profile if present.
3. Navigate to:

   ```text
   https://downsub.com/?url=<encoded TikTok long URL>
   ```

4. Wait for the video title, duration, and subtitle buttons.
5. Click `TXT`, not `SRT`, unless the user asks otherwise.
6. Save the downloaded TXT with a readable filename before creating the note.
7. Read the downloaded TXT file before creating the note.

When using Playwright, `download.path()` usually points to a hidden temporary file such as:

```text
C:\Users\<user>\AppData\Local\Temp\playwright-artifacts-*\uuid
```

Do not leave the user with only these UUID download records. After receiving the download, call `download.suggestedFilename()` and `download.saveAs(...)` into a readable scratch folder such as:

```text
.skills/01_video-subtitle-md-sync/.tmp/downsub/
```

Use filenames that include the sequence number or video slug, for example:

```text
01-are-you-single-dating-in-nyc.txt
```

When attaching through Python Playwright on this Windows repository, build the save path from the current working directory. Do not place the repository's Chinese absolute path inside a Python script piped through PowerShell stdin:

```python
from pathlib import Path

output = Path.cwd() / ".skills" / "01_video-subtitle-md-sync" / ".tmp" / "downsub" / "01-video-slug.txt"
download.save_as(str(output))
```

The synced Markdown note is the durable output. The raw TXT files are scratch artifacts and may be deleted after successful sync if the user does not need them.

DownSub retry rules:

- If page title is `Error - DownSub.com` or body includes `Oops an error has occurred`, retry once with the clean TikTok URL.
- If `TXT` is missing after retry, mark that item failed with the reason and continue only after clearly recording the failure.
- If the transcript is empty or clearly belongs to another video, stop and re-check the current item before syncing.

## Note Generation And Sync

Use the existing `video-subtitle-md-sync` workflow for every successful transcript.

In this repository, read:

```text
.skills/01_video-subtitle-md-sync/SKILL.md
```

Then create a UTF-8 draft file at:

```text
.skills/01_video-subtitle-md-sync/.tmp/draft.md
```

Run the save/sync command:

```powershell
py ".\.skills\01_video-subtitle-md-sync\scripts\save_review_markdown.py" `
  ".\.skills\01_video-subtitle-md-sync\.tmp\draft.md" `
  --repo-root "." `
  --title "Title Here" `
  --video-url "https://www.tiktok.com/@user/video/id" `
  --sync
```

Important:

- Do not pipe Chinese text through PowerShell stdin.
- Put the video URL near the top of the note.
- Preserve the full transcript in `Sentence Breakdown`.
- After each successful sync, record the written Markdown path before moving on.

## Final Checks

After all links are handled:

1. Run `git status --short` and expect a clean tree.
2. Run the repository encoding guard if available.
3. List the newest files in the month folder to verify newest-first numbering.
4. Summarize each input as completed, failed, or retried successfully.

Useful final check:

```powershell
Get-ChildItem -LiteralPath '2026-06' -Filter '*.md' |
  Sort-Object Name |
  Select-Object -First 20 -ExpandProperty Name
```

## Failure Handling

Be explicit but keep going when safe:

- Short link cannot resolve: mark failed and continue to next link.
- DownSub fails with full URL: retry clean URL.
- DownSub fails with clean URL: mark failed and continue.
- GitHub sync fails: stop the batch, report the failing item, and do not process further links until the sync problem is resolved.
- Existing repo changes appear: do not revert them; work with them or stop if they block safe sync.
