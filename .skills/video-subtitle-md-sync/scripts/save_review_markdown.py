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


def find_section_bounds(markdown: str, heading: str) -> tuple[int, int] | None:
    pattern = re.compile(rf"(?ms)^## {re.escape(heading)}\s*\n")
    match = pattern.search(markdown)
    if not match:
        return None

    section_start = match.start()
    content_start = match.end()
    next_heading = re.search(r"(?m)^## ", markdown[content_start:])
    section_end = content_start + next_heading.start() if next_heading else len(markdown)
    return section_start, section_end


def extract_section_body(markdown: str, heading: str) -> str | None:
    bounds = find_section_bounds(markdown, heading)
    if not bounds:
        return None
    _, section_end = bounds
    content_start = re.search(rf"(?ms)^## {re.escape(heading)}\s*\n", markdown).end()
    return markdown[content_start:section_end].strip()


def replace_section_body(markdown: str, heading: str, body: str) -> str:
    bounds = find_section_bounds(markdown, heading)
    if not bounds:
        return markdown

    section_start, section_end = bounds
    heading_match = re.search(rf"(?ms)^## {re.escape(heading)}\s*\n", markdown[section_start:section_end])
    if not heading_match:
        return markdown

    content_start = section_start + heading_match.end()
    new_body = body.strip("\n")
    replacement = markdown[section_start:content_start] + "\n" + new_body + "\n\n"
    return markdown[:section_start] + replacement + markdown[section_end:].lstrip("\n")


def strip_code_fence(text: str) -> str:
    stripped = text.strip()
    if not stripped.startswith("```"):
        return stripped

    lines = stripped.splitlines()
    if len(lines) >= 2 and lines[0].startswith("```") and lines[-1].strip() == "```":
        return "\n".join(lines[1:-1]).strip()
    return stripped


def split_transcript_segments(transcript: str) -> list[str]:
    segments: list[str] = []
    current: list[str] = []

    for raw_line in transcript.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        line = raw_line.strip()
        if not line:
            if current:
                segments.append(" ".join(current))
                current = []
            continue

        if line.startswith(">>"):
            if current:
                segments.append(" ".join(current))
                current = []
            stripped = line[2:].strip()
            if stripped.startswith("[") and stripped.endswith("]"):
                segments.append(f">> {stripped}")
            else:
                current.append(f">> {stripped}")
            continue

        if line.startswith("[") and line.endswith("]"):
            if current:
                segments.append(" ".join(current))
                current = []
            segments.append(line)
            continue

        current.append(line)

    if current:
        segments.append(" ".join(current))

    return [re.sub(r"\s+", " ", segment).strip() for segment in segments if segment.strip()]


def normalize_word(word: str) -> str:
    return word.lower().strip(",.!?;:\"'()[]")


def tail_matches(words: list[str], tail: tuple[str, ...]) -> bool:
    if len(words) < len(tail):
        return False
    normalized = [normalize_word(word) for word in words[-len(tail) :]]
    return normalized == list(tail)


def should_split_before_word(
    words: list[str],
    index: int,
    current: list[str],
    target_words: int,
    min_words: int,
) -> bool:
    current_length = len(current)
    if current_length < min_words or index >= len(words):
        return False

    first = normalize_word(words[index])
    second = normalize_word(words[index + 1]) if index + 1 < len(words) else ""
    pair = (first, second)

    strong_pairs = {
        ("and", "i"),
        ("and", "then"),
        ("and", "we"),
        ("and", "it"),
        ("and", "you"),
        ("but", "i"),
        ("but", "you"),
        ("so", "i"),
        ("so", "that's"),
        ("then", "i"),
        ("because", "i"),
        ("because", "something"),
        ("when", "i"),
        ("if", "i"),
    }
    subject_starters = {
        "i",
        "i'm",
        "i've",
        "i'll",
        "i'd",
        "we",
        "we're",
        "it's",
        "he",
        "she",
        "they",
        "there",
        "there's",
        "that's",
        "that",
        "this",
    }
    connector_starters = {
        "and",
        "but",
        "so",
        "because",
        "if",
        "then",
        "when",
        "while",
        "although",
        "though",
        "or",
        "as",
    }
    discourse_starters = {
        "honestly",
        "wait",
        "well",
        "okay",
        "ok",
        "oh",
        "anyway",
        "anyways",
    }

    if pair in strong_pairs and current_length >= min_words:
        return True
    if first == "or" and current and normalize_word(current[0]) == "if":
        return False
    if first in connector_starters and current_length >= min_words + 1:
        return True
    if first in discourse_starters and current_length >= min_words + 1:
        return True
    if first in subject_starters and current and normalize_word(current[-1]) in {"if", "when", "because", "that", "what", "like", "of", "to", "as"}:
        return False
    if first in subject_starters and current and normalize_word(current[0]) in connector_starters and current_length >= min_words:
        return True
    if first in subject_starters and current_length >= target_words:
        return True
    if first in {"is", "are", "was", "were"} and (
        tail_matches(current, ("as", "you", "guys", "know"))
        or tail_matches(current, ("you", "guys", "know"))
        or tail_matches(current, ("you", "know"))
    ):
        return True
    return False


def should_split_after_word(current: list[str], next_word: str | None, max_words: int) -> bool:
    if not current:
        return False

    next_norm = normalize_word(next_word) if next_word else ""
    last_norm = normalize_word(current[-1])
    weak_end_words = {
        "a",
        "an",
        "and",
        "as",
        "at",
        "because",
        "for",
        "from",
        "in",
        "into",
        "my",
        "of",
        "on",
        "or",
        "the",
        "their",
        "this",
        "to",
        "with",
        "your",
    }
    standalone_markers = {"honestly", "wait", "well", "okay", "ok"}
    next_clause_starters = {
        "i",
        "i'm",
        "i've",
        "i'll",
        "it",
        "it's",
        "that's",
        "we",
        "you",
        "because",
        "if",
        "when",
        "but",
        "so",
        "then",
        "probably",
        "maybe",
    }

    if tail_matches(current, ("as", "you", "guys", "know")):
        return True
    if tail_matches(current, ("you", "guys", "know")) and next_norm:
        return True
    if tail_matches(current, ("you", "know")) and next_norm in next_clause_starters:
        return True
    if tail_matches(current, ("oh", "sh")) and next_norm in next_clause_starters:
        return True
    if tail_matches(current, ("oh", "my")) and next_norm in next_clause_starters:
        return True
    if last_norm in {"it", "me", "you", "him", "her", "us", "them", "back", "today"} and next_norm in next_clause_starters:
        return True
    if last_norm in standalone_markers and next_norm:
        return True
    if len(current) >= max_words and last_norm not in weak_end_words:
        return True
    if len(current) >= max_words + 2:
        return True
    return False


def chunk_sentence_piece(piece: str, target_words: int = 4, max_words: int = 11, min_words: int = 3) -> list[str]:
    words = piece.split()
    if not words:
        return []

    chunks: list[str] = []
    current: list[str] = []

    for index, word in enumerate(words):
        if should_split_before_word(words, index, current, target_words, min_words):
            chunks.append(" ".join(current))
            current = []

        current.append(word)
        next_word = words[index + 1] if index + 1 < len(words) else None

        if re.search(r"[.!?][\"')\]]*$", word) and len(current) >= min_words:
            chunks.append(" ".join(current))
            current = []
            continue

        if should_split_after_word(current, next_word, max_words):
            chunks.append(" ".join(current))
            current = []

    if current:
        chunks.append(" ".join(current))
    return chunks


def build_sentence_breakdown(transcript: str) -> list[str]:
    breakdown: list[str] = []
    for segment in split_transcript_segments(transcript):
        if segment.startswith("[") or segment.startswith(">> ["):
            breakdown.append(segment)
            continue

        pieces = re.split(r"(?<=[.!?])\s+(?=(?:[\"'(\[]?[A-Z0-9>]))", segment)
        for piece in pieces:
            piece = piece.strip()
            if not piece:
                continue
            breakdown.extend(chunk_sentence_piece(piece))
    return [item for item in breakdown if item]


def render_shadowing_transcript(lines: list[str]) -> str:
    rendered: list[str] = []

    for line in lines:
        if line.startswith("[") or line.startswith(">> ["):
            if rendered and rendered[-1] != "":
                rendered.append("")
            rendered.append(line)
            rendered.append("")
            continue

        rendered.append(f"{line}  ")

    while rendered and rendered[-1] == "":
        rendered.pop()

    return "\n".join(rendered).rstrip() + "\n"


def ensure_shadowing_full_transcript(markdown: str) -> str:
    transcript_body = extract_section_body(markdown, "Full Transcript")
    if not transcript_body:
        return markdown

    transcript_text = strip_code_fence(transcript_body)
    lines = build_sentence_breakdown(transcript_text)
    if not lines:
        return markdown

    rendered = render_shadowing_transcript(lines)
    return replace_section_body(markdown, "Full Transcript", rendered)


def ensure_sentence_breakdown(markdown: str) -> str:
    transcript_body = extract_section_body(markdown, "Full Transcript")
    if not transcript_body:
        return markdown

    transcript_text = strip_code_fence(transcript_body)
    lines = build_sentence_breakdown(transcript_text)
    if not lines:
        return markdown

    breakdown_section = "## Sentence Breakdown\n\n" + "\n\n".join(f"- {line}" for line in lines) + "\n\n"
    existing_breakdown = find_section_bounds(markdown, "Sentence Breakdown")
    if existing_breakdown:
        start, end = existing_breakdown
        return markdown[:start].rstrip() + "\n\n" + breakdown_section + markdown[end:].lstrip("\n")

    bounds = find_section_bounds(markdown, "Full Transcript")
    if not bounds:
        return markdown
    _, section_end = bounds
    return markdown[:section_end].rstrip() + "\n\n" + breakdown_section + markdown[section_end:].lstrip("\n")


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
    final_markdown = ensure_shadowing_full_transcript(final_markdown)
    final_markdown = ensure_sentence_breakdown(final_markdown)
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
