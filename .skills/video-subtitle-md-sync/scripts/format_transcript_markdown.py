#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import re
import subprocess
import sys
import unicodedata
from datetime import datetime
from pathlib import Path


SUPPORTED_TEXT_SUFFIXES = {".srt", ".vtt", ".txt"}
BOUNDARY = "\n<<PARA_BREAK>>\n"


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Format transcript text into Markdown and optionally sync to GitHub."
    )
    parser.add_argument("source", nargs="?", help="Optional local transcript file path.")
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="Read transcript text from standard input instead of a file.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Git repository that should receive the Markdown file. Defaults to the current directory.",
    )
    parser.add_argument(
        "--output-dir",
        default="transcripts",
        help="Relative output directory inside the repository. Defaults to transcripts.",
    )
    parser.add_argument(
        "--source-dir",
        default="sources",
        help="Relative source archive directory for stdin input. Defaults to sources.",
    )
    parser.add_argument("--title", help="Override the generated transcript title.")
    parser.add_argument("--date", help="Override filename date in YYYY-MM-DD format.")
    parser.add_argument("--slug", help="Override the filename slug.")
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


def normalize_text(text: str) -> str:
    cleaned = text.replace("\ufeff", "")
    cleaned = re.sub(r"<[^>]+>", "", cleaned)
    cleaned = html.unescape(cleaned)
    cleaned = cleaned.replace("\\N", " ")
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    return cleaned


def normalize_timestamp(raw: str | None) -> str | None:
    if not raw:
        return None
    token = raw.strip().replace(",", ".")
    match = re.match(r"(?:(\d{1,2}):)?(\d{1,2}):(\d{2})(?:\.\d+)?$", token)
    if not match:
        return token
    hours = int(match.group(1) or 0)
    minutes = int(match.group(2))
    seconds = int(match.group(3))
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


def split_blocks(raw_text: str) -> list[str]:
    return [block.strip() for block in re.split(r"\r?\n\s*\r?\n", raw_text) if block.strip()]


def parse_timed_subtitles(raw_text: str) -> list[str]:
    entries: list[str] = []
    for block in split_blocks(raw_text):
        lines = [line.strip() for line in block.splitlines() if line.strip()]
        if not lines:
            continue
        if lines[0].upper() == "WEBVTT":
            continue
        if lines[0].startswith(("NOTE", "STYLE", "REGION")):
            continue

        timing_index = 0
        if "-->" not in lines[0]:
            if len(lines) < 2 or "-->" not in lines[1]:
                continue
            timing_index = 1

        text_lines = lines[timing_index + 1 :]
        text = normalize_text(" ".join(text_lines))
        if text:
            entries.append(text)
    return dedupe_consecutive(entries)


def dedupe_consecutive(items: list[str]) -> list[str]:
    result: list[str] = []
    previous = None
    for item in items:
        if item != previous:
            result.append(item)
            previous = item
    return result


def build_segments_from_lines(raw_text: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []

    for raw_line in raw_text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip().replace("\ufeff", "")
        if not line:
            if current:
                segments.append(" ".join(current))
                current = []
            continue

        marker = line.removeprefix(">>").strip()
        if marker.startswith("[") and marker.endswith("]"):
            if current:
                segments.append(" ".join(current))
                current = []
            segments.append(marker)
            continue

        if line.startswith(">>"):
            if current:
                segments.append(" ".join(current))
                current = []
            current.append(marker)
            continue

        current.append(line)

    if current:
        segments.append(" ".join(current))
    return [normalize_text(segment) for segment in segments if normalize_text(segment)]


def split_sentences(text: str) -> list[str]:
    pieces = re.split(r"(?<=[.!?])\s+(?=(?:[\"'(\[]?[A-Z0-9]))", text)
    return [piece.strip() for piece in pieces if piece.strip()]


def chunk_sentences(sentences: list[str], max_sentences: int = 4, max_chars: int = 550) -> list[str]:
    chunks: list[str] = []
    current: list[str] = []
    current_chars = 0

    for sentence in sentences:
        proposed_chars = current_chars + len(sentence) + (1 if current else 0)
        if current and (len(current) >= max_sentences or proposed_chars > max_chars):
            chunks.append(" ".join(current))
            current = [sentence]
            current_chars = len(sentence)
        else:
            current.append(sentence)
            current_chars = proposed_chars

    if current:
        chunks.append(" ".join(current))
    return chunks


def parse_plain_text(raw_text: str) -> list[str]:
    paragraphs: list[str] = []
    for segment in build_segments_from_lines(raw_text):
        if segment.startswith("[") and segment.endswith("]"):
            paragraphs.append(segment)
            continue

        sentences = split_sentences(segment)
        if sentences:
            paragraphs.extend(chunk_sentences(sentences))
        else:
            normalized = normalize_text(segment)
            if normalized:
                paragraphs.append(normalized)
    return paragraphs


def read_input_text(source: Path | None, use_stdin: bool) -> tuple[str, str]:
    if use_stdin:
        raw_text = sys.stdin.read()
        if not raw_text.strip():
            raise ValueError("No transcript text was provided on stdin.")
        return raw_text, "stdin"

    if source is None:
        raise ValueError("A source file is required when --stdin is not used.")
    if not source.exists():
        raise FileNotFoundError(f"Transcript source does not exist: {source}")

    suffix = source.suffix.lower()
    if suffix not in SUPPORTED_TEXT_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_TEXT_SUFFIXES))
        raise ValueError(f"Unsupported transcript file: {source.name}. Supported: {supported}")

    return source.read_text(encoding="utf-8-sig"), str(source)


def build_paragraphs(raw_text: str, source_label: str) -> list[str]:
    suffix = Path(source_label).suffix.lower()
    if suffix in {".srt", ".vtt"}:
        return parse_timed_subtitles(raw_text)
    return parse_plain_text(raw_text)


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "transcript"


def infer_title(raw_text: str, source_label: str) -> str:
    if source_label != "stdin":
        return Path(source_label).stem.replace("-", " ").replace("_", " ").strip().title()

    normalized = normalize_text(raw_text)
    words = normalized.split()
    if not words:
        return "Transcript"
    return " ".join(words[:8]).strip().rstrip(".") or "Transcript"


def resolve_date_token(raw_date: str | None) -> str:
    if not raw_date:
        return datetime.now().strftime("%Y-%m-%d")
    return datetime.strptime(raw_date, "%Y-%m-%d").strftime("%Y-%m-%d")


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


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8", newline="\n")


def maybe_write_source_archive(
    repo_root: Path,
    source_dir: str,
    date_token: str,
    slug: str,
    raw_text: str,
    source_label: str,
) -> str:
    if source_label != "stdin":
        return source_label

    archive_path = repo_root / source_dir / f"{date_token}-{slug}.txt"
    write_text(archive_path, raw_text.strip() + "\n")
    return str(Path(source_dir) / archive_path.name)


def render_markdown(title: str, source_label: str, paragraphs: list[str], exported_at: datetime) -> str:
    transcript_lines = [paragraph for paragraph in paragraphs if paragraph]
    plain_text = "\n\n".join(transcript_lines)

    sections = [
        f"# {title}",
        "",
        f"- Exported: {exported_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Source: {source_label}",
        f"- Transcript entries: {len(transcript_lines)}",
        "",
        "## Transcript",
        "",
    ]

    for paragraph in transcript_lines:
        sections.append(paragraph)
        sections.append("")

    sections.extend(
        [
            "## Plain Text",
            "",
            "```text",
            plain_text,
            "```",
            "",
        ]
    )
    return "\n".join(sections)


def write_markdown(repo_root: Path, output_dir: str, date_token: str, slug: str, markdown: str) -> Path:
    output_path = repo_root / output_dir / f"{date_token}-{slug}.md"
    write_text(output_path, markdown)
    return output_path


def build_commit_message(title: str, date_token: str, override: str | None) -> str:
    if override:
        return override
    return f"Add transcript note: {title} ({date_token})"


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
    raw_text, original_source_label = read_input_text(source_path, args.stdin)
    title = args.title or infer_title(raw_text, original_source_label)
    date_token = resolve_date_token(args.date)
    slug = args.slug or slugify(title)

    archived_source_label = maybe_write_source_archive(
        repo_root,
        args.source_dir,
        date_token,
        slug,
        raw_text,
        original_source_label,
    )
    paragraphs = build_paragraphs(raw_text, original_source_label)
    if not paragraphs:
        raise ValueError("No transcript content could be parsed from the input.")

    markdown = render_markdown(title, archived_source_label, paragraphs, datetime.now())
    output_path = write_markdown(repo_root, args.output_dir, date_token, slug, markdown)
    print(f"Wrote transcript: {output_path}")

    if args.sync:
        run_sync(repo_root, args.branch, build_commit_message(title, date_token, args.commit_message))

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
