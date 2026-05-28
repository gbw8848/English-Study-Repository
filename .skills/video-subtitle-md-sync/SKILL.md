---
name: video-subtitle-md-sync
description: Turn pasted English transcript text into a study-ready Markdown review note and sync it to GitHub. Use when the user gives Codex a transcript, subtitle text, or rough English learning content and wants a clean review document rather than a raw dump.
---

# Transcript Review Sync

The job is to turn the user's transcript text into a Markdown note that is useful for English review, then save it in the current repository and sync it to GitHub.

## Required Filename Order

This rule is mandatory and easy to miss, so treat it as a first-check item before finishing the task:

- Within each month folder, filenames must stay newest-first for GitHub browsing.
- The newest note in that month must be `001-YYYY-MM-DD-slug.md`.
- The second newest note must be `002-...`, the third `003-...`, and so on.
- If you add a newer note, rename the older notes in that same month so the newest file becomes `001`.
- Do not leave a newly added latest note as `004`, `005`, or any other later number just because it was created last.

Non-negotiable rules:

- Keep the full transcript content inside `Sentence Breakdown`. Do not delete paragraphs just because they feel repetitive.
- Use model judgment first when rewriting the transcript for study. Do not rely on the Python script as the primary source of pause placement.
- Put `Sentence Breakdown` at the top of the Markdown file as the only transcript section.
- Reformat hard-wrapped transcript lines into shadowing-friendly chunks while preserving all words.
- Make `Sentence Breakdown` shadowing-friendly: prefer spoken pauses and thought groups over full grammar analysis.
- Keep month-folder filenames sorted newest-first for GitHub browsing. The newest note in a month should be renamed to `001-YYYY-MM-DD-slug.md`, the next to `002-...`, and so on.
- If the user provides a video URL, include a clickable video link near the top of the file.
- Put review notes after the transcript, not before it.
- Chinese sections (`Summary`, `Practice Lines`, `Useful Vocabulary`, `Review Notes`) must stay valid UTF-8. Never push garbled `?` text to GitHub.
- Do not include a `Useful Expressions` section. Sentence-level practice belongs in `Practice Lines` only.

## Encoding Rules

PowerShell stdin piping often corrupts Chinese text on Windows. Treat that as a known failure mode.

- Prefer writing the prepared Markdown with the editor as UTF-8, then pass the draft file path as the positional `source` argument.
- Do not use `@' ... '@ | py ... --stdin` when the note contains Chinese.
- Before `--sync`, the save script must pass the encoding check. If it fails, rewrite the Chinese sections and save again.
- After saving, quickly read back `Summary`, `Practice Lines`, and `Review Notes` to confirm Chinese renders correctly.

Preferred save command:

```powershell
py ".\.skills\video-subtitle-md-sync\scripts\save_review_markdown.py" `
  ".\.skills\video-subtitle-md-sync\.tmp\draft.md" `
  --repo-root "." `
  --title "Example Title" `
  --sync
```

Manual encoding check:

```powershell
py ".\.skills\video-subtitle-md-sync\scripts\check_review_encoding.py" `
  --file ".\2026-05\001-2026-05-23-example.md"
```

## Default Output Shape

Unless the user asks for a different structure, write the note with these sections in this order:

```markdown
# Title

- Date: YYYY-MM-DD
- Video: <https://...>
- Source: pasted transcript

## Sentence Breakdown

- Short chunk
- Short chunk

## Summary

Short Chinese summary of what the content is about.

## Practice Lines

| Full Line | Cloze | Answer | 中文 |
| --- | --- | --- | --- |
| I make about 140 grand. | I make about 140 _____. | grand | 我年薪大概 14 万。 |
| Don't only do it in the pursuit of money. | Don't only do it in the pursuit of _____. | money | 别只为了赚钱去学医。 |

## Useful Vocabulary

| Word / Phrase | Meaning | Note |
| --- | --- | --- |

## Review Notes

- Grammar or collocation notes
- Cultural context
- Subtitle or transcription errors
- Optional register alternatives (e.g. `grand` vs `k`) — not full alternate sentences

```

### Section roles

| Section | Purpose |
| --- | --- |
| `Sentence Breakdown` | Full transcript for shadowing; includes filler lines |
| `Summary` | Chinese overview of the content |
| `Practice Lines` | Curated full sentences with cloze drills for active recall |
| `Useful Vocabulary` | Word and phrase reference table |
| `Review Notes` | Deep notes only — no sentence-by-sentence translation |

### Practice Lines rules

`Practice Lines` replaces the old `Useful Expressions` section. Do not add both.

1. **Volume:** 8–12 rows per note.
2. **Selection:** Pick complete sentences worth practicing — idioms, collocations, punchlines, interview answers. Skip filler (`Yeah`, `Nice`, `Wait`) unless it teaches something real.
3. **Full Line:** Must come from the transcript (you may join adjacent chunks into one natural sentence). Keep the original wording.
4. **Cloze:** Same sentence as `Full Line`, but replace exactly one word or one short phrase with `_____`. Do not reorder words. Do not invent alternate sentences.
5. **Answer:** The removed word or phrase only — not the full sentence. It must appear verbatim in `Full Line`.
6. **Alignment:** Prefer blanking words that also appear in `Useful Vocabulary`. Build `Practice Lines` and `Useful Vocabulary` together so they reinforce each other.
7. **Phrases:** Multi-word targets (`wind down`, `take a step back`, `in the pursuit of money`) may be blanked as one unit.
8. **中文:** Translate the `Full Line`, not the `Cloze` row.

Study flow for the user:

1. Read `Full Line` aloud once or twice.
2. Cover `Full Line`, fill in `Cloze` from memory.
3. Check `Answer`, then say the full sentence again.

Do not generate free-form variation sentences in this section. Controlled cloze is preferred because alternate phrasings are hard to quality-check and drift away from the source video.

## Workflow

### 1. Understand the text

- Read the pasted transcript or subtitle text.
- Clean broken line wraps.
- Keep simple markers such as `[music]` only if they help context.
- Break the transcript into study-friendly chunks and keep only one transcript section.

### 2. Turn it into a review note

- Use AI-style semantic judgment to decide natural pause points, thought groups, and read-aloud rhythm before saving.
- Write a short Chinese summary.
- Build `Practice Lines` (Full Line + Cloze + Answer + 中文) from the best 8–12 sentences in the transcript.
- Extract useful words and phrases into `Useful Vocabulary`; align `Answer` values with this table when possible.
- Add `Review Notes` for grammar, culture, and subtitle errors only — do not repeat sentence translations already covered in `Practice Lines`.
- Preserve the full transcript exactly, but present it only through `Sentence Breakdown`.
- If the user wants help with pausing and reading, make the `Sentence Breakdown` section more fine-grained rather than more compressed.
- Rebuild `Sentence Breakdown` from the transcript source when the note is regenerated.
- Prefer English thought groups rather than fixed-length cuts: split at connectors, new clauses, restarts like `I...`, and short parenthetical phrases such as `as you guys know`.
- Prefer chunks that someone can actually read aloud in one breath. Usually that means short spoken units, not long written-style sentences.
- Do not split in places that make shadowing awkward, such as `I like it`, `if you...`, or other tightly connected mini-phrases.
- Treat the script as a fallback saver and section normalizer. If the note already contains a natural AI-written `Sentence Breakdown`, keep it instead of regenerating it mechanically.

### 3. Save and sync

Use `scripts/save_review_markdown.py` to write the final Markdown into the repo.

Before you finish, explicitly verify the month folder order again:

- If the new note is the latest one by date, it must end up as `001-...`.
- Renumber the older files in that same month as needed.
- Do not assume the write step already made the ordering obvious enough; check the actual filenames.

Save workflow:

1. Write the full note to a UTF-8 file with the editor, for example `.skills/video-subtitle-md-sync/.tmp/draft.md`.
2. Run `save_review_markdown.py` with the draft path as the positional `source` argument, not `--stdin`.
3. Let the script validate encoding before write and again before GitHub sync.
4. If validation fails, fix the Chinese sections directly in the file and rerun.

```powershell
py ".\.skills\video-subtitle-md-sync\scripts\save_review_markdown.py" `
  ".\.skills\video-subtitle-md-sync\.tmp\draft.md" `
  --repo-root "." `
  --title "Example Title" `
  --video-url "https://..." `
  --sync
```

The script writes into a month folder such as `2026-04/` by default and then optionally calls `scripts/sync_to_github.ps1`.
Within each month folder, the script also reorders filenames so the newest note appears first in GitHub's alphabetical file list.
`sync_to_github.ps1` runs `check_review_encoding.py` on changed Markdown files before commit; sync aborts if mojibake is detected.

Avoid this pattern on Windows because it often turns Chinese into `?`:

```powershell
@'
## Summary
中文摘要
'@ | py ".\.skills\video-subtitle-md-sync\scripts\save_review_markdown.py" --stdin --sync
```

## Important Rule

Do not omit parts of the transcript. The final file should start with `Sentence Breakdown`, include the video URL in visible copyable form when available, then continue with `Summary`, `Practice Lines`, `Useful Vocabulary`, and `Review Notes`.

Treat `Sentence Breakdown` as a speaking aid, not just a formatting step. The result should look like natural pause points for imitation and shadowing.

Treat `Practice Lines` as an active-recall aid: the user shadows the full line first, then drills the blanked keyword inside the same sentence frame.
