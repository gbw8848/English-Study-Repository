#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

CJK_RE = re.compile(r"[\u4e00-\u9fff\u3400-\u4dbf]")
MOJIBAKE_RUN_RE = re.compile(r"\?{4,}")
CHINESE_SECTIONS = ("Summary", "Useful Vocabulary", "Review Notes")
SECTION_RE_TEMPLATE = r"(?ms)^## {heading}\s*\n(.*?)(?=^## |\Z)"
REVIEW_NOTE_DIR_RE = re.compile(r"[\\/]\d{4}-\d{2}[\\/]")


def configure_stdio() -> None:
    for stream_name in ("stdin", "stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def extract_section_body(markdown: str, heading: str) -> str | None:
    match = re.search(SECTION_RE_TEMPLATE.format(heading=re.escape(heading)), markdown)
    if not match:
        return None
    body = match.group(1).strip()
    return body or None


def validate_utf8_bytes(raw: bytes) -> list[str]:
    issues: list[str] = []
    if raw.startswith(b"\xff\xfe") or raw.startswith(b"\xfe\xff"):
        issues.append("File uses UTF-16 BOM. Save as UTF-8.")
    if raw.startswith(b"\xff\xfe\x00\x00") or raw.startswith(b"\x00\x00\xfe\xff"):
        issues.append("File uses UTF-32 BOM. Save as UTF-8.")
    if b"\x00" in raw:
        issues.append("File contains NUL bytes, which usually means wrong encoding.")

    try:
        text = raw.decode("utf-8")
    except UnicodeDecodeError:
        issues.append("File is not valid UTF-8.")
        return issues

    if "\ufffd" in text:
        issues.append("Contains Unicode replacement character U+FFFD, likely mojibake.")
    return issues


def looks_like_review_note(path: Path) -> bool:
    return bool(REVIEW_NOTE_DIR_RE.search(str(path)))


def validate_review_markdown(markdown: str, path: Path | None = None) -> list[str]:
    issues = validate_utf8_bytes(markdown.encode("utf-8"))

    if path is not None and not looks_like_review_note(path):
        return issues
    if path is None and "## Sentence Breakdown" not in markdown:
        return issues

    for heading in CHINESE_SECTIONS:
        body = extract_section_body(markdown, heading)
        if not body:
            continue

        if MOJIBAKE_RUN_RE.search(body):
            issues.append(
                f"## {heading} contains long '?' runs, likely garbled Chinese from PowerShell stdin."
            )

        if heading == "Summary" and not CJK_RE.search(body):
            issues.append(f"## {heading} has no Chinese characters; expected a Chinese summary.")

        if heading == "Useful Vocabulary":
            for line in body.splitlines():
                if not line.startswith("|") or line.startswith("| ---"):
                    continue
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) < 2:
                    continue
                meaning = cells[1]
                if meaning and not CJK_RE.search(meaning) and re.fullmatch(r"[\?\s/→\-]+", meaning):
                    issues.append(
                        "## Useful Vocabulary Meaning column looks corrupted (question marks only)."
                    )
                    break

        if heading == "Review Notes":
            cjk_lines = sum(1 for line in body.splitlines() if CJK_RE.search(line))
            question_lines = sum(
                1
                for line in body.splitlines()
                if line.strip().startswith("-") and "?" in line and not CJK_RE.search(line)
            )
            if cjk_lines == 0 and question_lines >= 2:
                issues.append("## Review Notes looks corrupted: many '?' lines and no Chinese text.")

    return issues


def validate_file(path: Path) -> list[str]:
    raw = path.read_bytes()
    issues = validate_utf8_bytes(raw)
    if any("not valid UTF-8" in issue for issue in issues):
        return issues
    return validate_review_markdown(raw.decode("utf-8-sig"), path)


def changed_text_files(repo_root: Path, staged_only: bool = False, content_changes_only: bool = False) -> list[Path]:
    if staged_only:
        diff_filter = ["--diff-filter=AM"] if content_changes_only else []
        commands = [["git", "diff", "--cached", "--name-only", *diff_filter]]
    else:
        commands = [
            ["git", "diff", "--name-only"],
            ["git", "diff", "--cached", "--name-only"],
            ["git", "ls-files", "--others", "--exclude-standard"],
        ]
    seen: set[str] = set()
    paths: list[Path] = []
    for command in commands:
        result = subprocess.run(command, cwd=repo_root, capture_output=True, text=True, check=False)
        if result.returncode != 0:
            continue
        for line in result.stdout.splitlines():
            relative = line.strip()
            if not relative or relative in seen:
                continue
            seen.add(relative)
            path = repo_root / relative
            if path.suffix.lower() == ".md" and path.is_file() and looks_like_review_note(path):
                paths.append(path)
    return sorted(paths)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate review-note Markdown for UTF-8 and Chinese-section mojibake."
    )
    parser.add_argument("--file", action="append", default=[], help="Markdown file to validate.")
    parser.add_argument(
        "--repo-root",
        default=".",
        help="When no --file is given, validate changed .md files in this git repo.",
    )
    parser.add_argument(
        "--staged-only",
        action="store_true",
        help="Only validate staged Markdown files (used before git commit).",
    )
    parser.add_argument(
        "--content-changes-only",
        action="store_true",
        help="With --staged-only, ignore pure renames and validate added/modified files only.",
    )
    return parser.parse_args()


def main() -> int:
    configure_stdio()
    args = parse_args()

    targets: list[Path] = [Path(item).resolve() for item in args.file]
    if not targets:
        repo_root = Path(args.repo_root).resolve()
        targets = changed_text_files(
            repo_root,
            staged_only=args.staged_only,
            content_changes_only=args.content_changes_only,
        )

    if not targets:
        print("[encoding-check] No Markdown files to validate.")
        return 0

    failed = False
    for path in targets:
        issues = validate_file(path)
        if not issues:
            continue
        failed = True
        print(f"[encoding-check] FAILED: {path}", file=sys.stderr)
        for issue in issues:
            print(f"  - {issue}", file=sys.stderr)

    if failed:
        print(
            "[encoding-check] Fix garbled Chinese before syncing. "
            "Prefer writing the note with the editor and passing --source, not PowerShell stdin.",
            file=sys.stderr,
        )
        return 4

    print(f"[encoding-check] Passed for {len(targets)} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
