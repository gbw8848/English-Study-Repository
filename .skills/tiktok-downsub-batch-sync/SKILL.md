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
py "$env:USERPROFILE\.codex\skills\tiktok-downsub-batch-sync\scripts\resolve_tiktok_links.py" `
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

When the user references BitBrowser, an existing browser window, or provides a screenshot of the BitBrowser workspace, use the `bitbrowser-seo-browser` skill to attach to the correct profile and find the real DevTools port. Do not trust the `port=` value in the BitBrowser console URL.

Preferred browser flow:

1. Reuse the existing DownSub tab if present.
2. Navigate to:

   ```text
   https://downsub.com/?url=<encoded TikTok long URL>
   ```

3. Wait for the video title, duration, and subtitle buttons.
4. Click `TXT`, not `SRT`, unless the user asks otherwise.
5. Save the downloaded TXT with a readable filename before creating the note.
6. Read the downloaded TXT file before creating the note.

When using Playwright, `download.path()` usually points to a hidden temporary file such as:

```text
C:\Users\<user>\AppData\Local\Temp\playwright-artifacts-*\uuid
```

Do not leave the user with only these UUID download records. After receiving the download, call `download.suggestedFilename()` and `download.saveAs(...)` into a readable scratch folder such as:

```text
.skills/video-subtitle-md-sync/.tmp/downsub/
```

Use filenames that include the sequence number or video slug, for example:

```text
01-are-you-single-dating-in-nyc.txt
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
.skills/video-subtitle-md-sync/SKILL.md
```

Then create a UTF-8 draft file at:

```text
.skills/video-subtitle-md-sync/.tmp/draft.md
```

Run the save/sync command:

```powershell
py ".\.skills\video-subtitle-md-sync\scripts\save_review_markdown.py" `
  ".\.skills\video-subtitle-md-sync\.tmp\draft.md" `
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
