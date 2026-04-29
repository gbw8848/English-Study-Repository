#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Save a prepared Markdown review note and optionally sync it to GitHub."
    )
    parser.add_argument("source", nargs="?", help="Optional path to a prepared Markdown file.")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read prepared Markdown from standard input instead of a file.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Git repository that should receive the Markdown file. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Optional relative output directory. Defaults to a YYYY-MM month folder in the repository root.",
    )
    parser.add_argument("--title", help="Document title. Used for filename and header fallback.")
    parser.add_argument("--date", help="Override filename date in YYYY-MM-DD format.")
    parser.add_argument("--slug", help="Override the filename slug.")
    parser.add_argument("--video-url", help="Optional video URL to include near the top of the note.")
    parser.add_argument(
        "--source-label",
        default="pasted transcript",
        help="Source label to include near the top of the note when metadata is missing.",
    )
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Commit and push the generated files after writing them.",
    )
    parser.add_argument("--branch", help="Git branch to push. Defaults to the current branch.")
    parser.add_argument("--commit-message", help="Override the Git commit message.")
    args = parser.parse_args()

    if args.stdin and args.source:
        parser.error("Use either a source file or --stdin, not both.")
    if not args.stdin and not args.source:
        parser.error("Provide a source file or use --stdin.")
    return args


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "review-note"


def resolve_date_token(raw_date: str | None) -> str:
    if not raw_date:
        return datetime.now().strftime("%Y-%m-%d")
    return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")


def resolve_output_dir(raw_output_dir: str, date_token: str) -> Path:
    if raw_output_dir.strip():
        return Path(raw_output_dir)
    return Path(date_token[:7])


def ensure_git_repo(repo_root: Path) -> None:
    result = subprocess.run(
        ["git", "rev-parse", "--is-inside-work-tree"],
        cwd=repo_root,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"Not a Git repository: {repo_root}")


def read_markdown(source: Path | None, use_stdin: bool) -> str:
    if use_stdin:
        content = sys.stdin.read()
    else:
        if source is None or not source.exists():
            raise FileNotFoundError(f"Markdown source does not exist: {source}")
        content = source.read_text(encoding="utf-8-sig")

    if not content.strip():
        raise ValueError("No Markdown content was provided.")
    return content.strip() + "\n"


def extract_title(markdown: str, title_override: str | None) -> str:
    if title_override:
        return title_override.strip()

    for line in markdown.splitlines():
        stripped = line.strip()
        if stripped.startswith("# "):
            return stripped[2:].strip()

    first_nonempty = next((line.strip() for line in markdown.splitlines() if line.strip()), "Review Note")
    return first_nonempty[:80]


def ensure_title_header(markdown: str, title: str) -> str:
    for line in markdown.splitlines():
        if line.strip():
            if line.startswith("# "):
                return markdown
            break
    return f"# {title}\n\n{markdown.lstrip()}"


def ensure_metadata_block(markdown: str, date_token: str, source_label: str, video_url: str | None) -> str:
    lines = markdown.splitlines()
    if not lines:
        return markdown

    title_idx = next((idx for idx, line in enumerate(lines) if line.strip()), None)
    if title_idx is None or not lines[title_idx].startswith("# "):
        return markdown

    insert_at = title_idx + 1
    while insert_at < len(lines) and not lines[insert_at].strip():
        insert_at += 1

    metadata_lines: list[str] = []
    while insert_at < len(lines) and lines[insert_at].startswith("- "):
        metadata_lines.append(lines[insert_at])
        insert_at += 1

    has_date = any(line.startswith("- Date:") for line in metadata_lines)
    has_video = any(line.startswith("- Video:") for line in metadata_lines)
    has_source = any(line.startswith("- Source:") for line in metadata_lines)

    missing: list[str] = []
    if not has_date:
        missing.append(f"- Date: {date_token}")
    if video_url and not has_video:
        missing.append(f"- Video: [Watch on YouTube]({video_url})")
    if not has_source:
        missing.append(f"- Source: {source_label}")

    if not missing:
        return markdown

    rebuilt: list[str] = []
    rebuilt.extend(lines[: title_idx + 1])
    rebuilt.append("")
    rebuilt.extend(metadata_lines)
    rebuilt.extend(missing)

    if insert_at < len(lines):
        if lines[insert_at].strip():
            rebuilt.append("")
        rebuilt.extend(lines[insert_at:])

    return "\n".join(rebuilt).rstrip() + "\n"


def write_markdown(repo_root: Path, output_dir: str, date_token: str, slug: str, markdown: str) -> Path:
    output_path = repo_root / output_dir / f"{date_token}-{slug}.md"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(markdown, encoding="utf-8", newline="\n")
    return output_path


def build_commit_message(title: str, date_token: str, override: str | None) -> str:
    if override:
        return override
    return f"Add review note: {title} ({date_token})"


def run_sync(repo_root: Path, branch: str | None, message: str) -> None:
    script_path = Path(__file__).with_name("sync_to_github.ps1")
    command = [
        "powershell",
        "-NoProfile",
        "-ExecutionPolicy",
        "Bypass",
        "-File",
        str(script_path),
        "-RepoRoot",
        str(repo_root),
        "-Message",
        message,
    ]
    if branch:
        command.extend(["-Branch", branch])
    subprocess.run(command, check=True)


def main() -> int:
    configure_stdio()
    args = parse_args()
    repo_root = Path(args.repo_root).resolve()
    ensure_git_repo(repo_root)

    source_path = Path(args.source).resolve() if args.source else None
    markdown = read_markdown(source_path, args.stdin)
    title = extract_title(markdown, args.title)
    date_token = resolve_date_token(args.date)
    final_markdown = ensure_title_header(markdown, title)
    final_markdown = ensure_metadata_block(final_markdown, date_token, args.source_label, args.video_url)
    slug = args.slug or slugify(title)
    output_dir = resolve_output_dir(args.output_dir, date_token)

    output_path = write_markdown(repo_root, str(output_dir), date_token, slug, final_markdown)
    print(f"Wrote review note: {output_path}")

    if args.sync:
        run_sync(repo_root, args.branch, build_commit_message(title, date_token, args.commit_message))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
