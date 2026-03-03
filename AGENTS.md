# AGENTS.md instructions for d:\2_Code\04_英语学习

<INSTRUCTIONS>
## Default Working Mode In This Repository
- Enable **Auto English Capture Mode** by default.
- If the user message contains English words/sentences (including mixed Chinese-English), automatically treat it as potential learning content.
- Automatically trigger `.skills/english_partner/SKILL.md` for that turn.
- If the message contains learnable content, create/update today's `Review_Plan_YYYY-MM-DD.md` without waiting for explicit "please record" commands.

## What Counts As Learnable Content
- Grammar errors, unnatural phrasing, and corrected rewrites.
- New vocabulary, collocations, pronunciation points, and useful spoken sentence patterns.
- Correct expressions worth reuse.

## Write Rules
- Keep updates incremental and deduplicated.
- Prefer appending new learning points instead of rewriting the whole file.
- Always keep `README.md` latest review link at the top without duplicates.

## Sync Rules
- After markdown updates, run:
  - `powershell -NoProfile -ExecutionPolicy Bypass -File .\.skills\english_partner\scripts\sync-to-github.ps1 -Date YYYY-MM-DD`
- If no file change, report "No changes to sync."

## Opt-out
- If the user explicitly says "do not record", skip file writes for that turn.
</INSTRUCTIONS>
