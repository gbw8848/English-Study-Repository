#!/usr/bin/env python3
from __future__ import annotations

import argparse
import html
import importlib
import re
import subprocess
import sys
import tempfile
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse


SUPPORTED_TEXT_SUFFIXES = {".srt", ".vtt", ".txt"}


def configure_stdio() -> None:
    for stream_name in ("stdout", "stderr"):
        stream = getattr(sys, stream_name, None)
        if stream and hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")


@dataclass
class Cue:
    start: str | None
    end: str | None
    text: str


@dataclass
class SubtitlePayload:
    title: str
    source_label: str
    source_link: str | None
    language: str
    cues: list[Cue]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Export subtitles into a Markdown transcript and optionally sync to GitHub."
    )
    parser.add_argument("source", help="Subtitle file path or video URL.")
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
    parser.add_argument("--title", help="Override the generated transcript title.")
    parser.add_argument("--date", help="Override filename date in YYYY-MM-DD format.")
    parser.add_argument("--language", default="en", help="Subtitle language for URL mode.")
    parser.add_argument("--slug", help="Override the filename slug.")
    parser.add_argument(
        "--sync",
        action="store_true",
        help="Commit and push the generated Markdown file after writing it.",
    )
    parser.add_argument(
        "--install-missing",
        action="store_true",
        help="Allow automatic install of yt-dlp into .tools/pydeps when URL mode needs it.",
    )
    parser.add_argument(
        "--cookies-from-browser",
        choices=["chrome", "edge", "firefox", "brave", "opera", "safari", "vivaldi"],
        help="Read YouTube cookies from a local browser for blocked videos.",
    )
    parser.add_argument("--branch", help="Git branch to push. Defaults to the current branch.")
    parser.add_argument("--commit-message", help="Override the Git commit message.")
    return parser.parse_args()


def is_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


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


def parse_timed_subtitles(raw_text: str) -> list[Cue]:
    cues: list[Cue] = []
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

        timing_line = lines[timing_index]
        parts = [part.strip() for part in timing_line.split("-->", 1)]
        if len(parts) != 2:
            continue

        text_lines = lines[timing_index + 1 :]
        text = normalize_text(" ".join(text_lines))
        if not text:
            continue

        end_part = re.split(r"\s+", parts[1], maxsplit=1)[0]
        cues.append(
            Cue(
                start=normalize_timestamp(parts[0]),
                end=normalize_timestamp(end_part),
                text=text,
            )
        )
    return cues


def parse_plain_text(raw_text: str) -> list[Cue]:
    cues: list[Cue] = []
    for block in split_blocks(raw_text):
        text = normalize_text(" ".join(block.splitlines()))
        if text:
            cues.append(Cue(start=None, end=None, text=text))
    return cues


def read_local_subtitle(
    source_path: Path, title_override: str | None, language: str, source_label: str | None = None
) -> SubtitlePayload:
    if not source_path.exists():
        raise FileNotFoundError(f"Subtitle source does not exist: {source_path}")

    suffix = source_path.suffix.lower()
    if suffix not in SUPPORTED_TEXT_SUFFIXES:
        supported = ", ".join(sorted(SUPPORTED_TEXT_SUFFIXES))
        raise ValueError(f"Unsupported subtitle file: {source_path.name}. Supported: {supported}")

    raw_text = source_path.read_text(encoding="utf-8-sig")
    cues = parse_plain_text(raw_text) if suffix == ".txt" else parse_timed_subtitles(raw_text)
    if not cues:
        raise ValueError(f"No subtitle lines were parsed from: {source_path}")

    title = title_override or source_path.stem
    return SubtitlePayload(
        title=title,
        source_label=source_label or str(source_path),
        source_link=None,
        language=language,
        cues=cues,
    )


def ensure_yt_dlp(allow_install: bool, repo_root: Path):
    local_dependency_dir = repo_root / ".tools" / "pydeps"
    if local_dependency_dir.exists():
        sys.path.insert(0, str(local_dependency_dir))

    try:
        return importlib.import_module("yt_dlp")
    except ImportError:
        if not allow_install:
            raise RuntimeError(
                "yt-dlp is required for URL mode. Install it with "
                "`py -m pip install --target .tools/pydeps yt-dlp` or rerun with --install-missing."
            ) from None

    local_dependency_dir.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "--target", str(local_dependency_dir), "yt-dlp"],
        check=True,
    )
    sys.path.insert(0, str(local_dependency_dir))
    return importlib.import_module("yt_dlp")


def read_url_subtitle(
    source_url: str,
    title_override: str | None,
    language: str,
    allow_install: bool,
    repo_root: Path,
    cookies_from_browser: str | None,
) -> SubtitlePayload:
    yt_dlp = ensure_yt_dlp(allow_install, repo_root)

    with tempfile.TemporaryDirectory(prefix="subtitle-export-") as temp_dir:
        temp_path = Path(temp_dir)
        options = {
            "skip_download": True,
            "writesubtitles": True,
            "writeautomaticsub": True,
            "subtitleslangs": [language, f"{language}.*", f"{language}-*"],
            "subtitlesformat": "vtt/best",
            "outtmpl": str(temp_path / "%(title)s.%(id)s"),
            "quiet": True,
            "no_warnings": True,
        }
        if cookies_from_browser:
            options["cookiesfrombrowser"] = (cookies_from_browser,)

        try:
            with yt_dlp.YoutubeDL(options) as downloader:
                info = downloader.extract_info(source_url, download=True)
        except Exception as exc:
            message = str(exc)
            if "Sign in to confirm you’re not a bot" in message or "Sign in to confirm you're not a bot" in message:
                raise RuntimeError(
                    "YouTube blocked anonymous subtitle access for this video. "
                    "Retry with --cookies-from-browser chrome (or your active browser) on your own machine."
                ) from exc
            raise

        subtitle_files = sorted(
            [
                path
                for path in temp_path.iterdir()
                if path.is_file() and path.suffix.lower() in SUPPORTED_TEXT_SUFFIXES
            ],
            key=lambda item: item.stat().st_size,
            reverse=True,
        )
        if not subtitle_files:
            raise RuntimeError(
                "No downloadable subtitles were found at this URL. "
                "Provide a local subtitle file or add a speech-to-text step later."
            )

        subtitle_path = subtitle_files[0]
        raw_text = subtitle_path.read_text(encoding="utf-8-sig")
        cues = parse_plain_text(raw_text) if subtitle_path.suffix.lower() == ".txt" else parse_timed_subtitles(raw_text)
        if not cues:
            raise RuntimeError(f"Subtitles were downloaded but no cues could be parsed from {subtitle_path.name}.")

        title = title_override or info.get("title") or subtitle_path.stem
        webpage_url = info.get("webpage_url") or source_url
        return SubtitlePayload(
            title=title,
            source_label=webpage_url,
            source_link=webpage_url,
            language=language,
            cues=cues,
        )


def slugify(value: str) -> str:
    ascii_value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    lowered = ascii_value.lower()
    slug = re.sub(r"[^a-z0-9]+", "-", lowered).strip("-")
    return slug or "transcript"


def dedupe_lines(cues: list[Cue]) -> list[str]:
    lines: list[str] = []
    previous = None
    for cue in cues:
        if cue.text != previous:
            lines.append(cue.text)
            previous = cue.text
    return lines


def render_markdown(payload: SubtitlePayload, exported_at: datetime) -> str:
    transcript_lines = []
    for cue in payload.cues:
        if cue.start:
            transcript_lines.append(f"- [{cue.start}] {cue.text}")
        else:
            transcript_lines.append(f"- {cue.text}")

    plain_text = "\n".join(dedupe_lines(payload.cues))
    metadata_lines = [
        f"- Exported: {exported_at.strftime('%Y-%m-%d %H:%M:%S')}",
        f"- Source: {payload.source_label}",
        f"- Language: {payload.language}",
        f"- Transcript entries: {len(payload.cues)}",
    ]

    if payload.source_link:
        metadata_lines.insert(2, f"- Link: {payload.source_link}")

    sections = [
        f"# {payload.title}",
        "",
        *metadata_lines,
        "",
        "## Transcript",
        "",
        *transcript_lines,
        "",
        "## Plain Text",
        "",
        "```text",
        plain_text,
        "```",
        "",
    ]
    return "\n".join(sections)


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


def write_markdown(repo_root: Path, output_dir: str, date_token: str, slug: str, markdown: str) -> Path:
    target_dir = repo_root / output_dir
    target_dir.mkdir(parents=True, exist_ok=True)
    output_path = target_dir / f"{date_token}-{slug}.md"
    output_path.write_text(markdown, encoding="utf-8", newline="\n")
    return output_path


def build_commit_message(path: Path, title: str, date_token: str, override: str | None) -> str:
    if override:
        return override
    return f"Add transcript: {title} ({date_token})"


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

    if is_url(args.source):
        payload = read_url_subtitle(
            args.source,
            args.title,
            args.language,
            args.install_missing,
            repo_root,
            args.cookies_from_browser,
        )
    else:
        payload = read_local_subtitle(Path(args.source).resolve(), args.title, args.language, args.source)

    date_token = resolve_date_token(args.date)
    exported_at = datetime.now()
    slug = args.slug or slugify(payload.title)
    markdown = render_markdown(payload, exported_at)
    output_path = write_markdown(repo_root, args.output_dir, date_token, slug, markdown)

    print(f"Wrote transcript: {output_path}")

    if args.sync:
        commit_message = build_commit_message(output_path, payload.title, date_token, args.commit_message)
        run_sync(repo_root, args.branch, commit_message)

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise SystemExit(1)
