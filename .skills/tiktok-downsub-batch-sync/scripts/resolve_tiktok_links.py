#!/usr/bin/env python3
"""Resolve TikTok short links and print clean long URLs.

This helper intentionally does only the safe upstream step: resolve redirects
and remove tracking query parameters. DownSub download and note sync should
still be handled one video at a time by the agent.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.parse
import urllib.request


def clean_tiktok_url(url: str) -> str:
    parsed = urllib.parse.urlsplit(url)
    return urllib.parse.urlunsplit((parsed.scheme, parsed.netloc, parsed.path.rstrip("/"), "", ""))


def resolve_url(url: str, timeout: int) -> dict[str, str | bool]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0 Safari/537.36"
            )
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            long_url = response.geturl()
        return {
            "ok": True,
            "short_url": url,
            "long_url": long_url,
            "clean_url": clean_tiktok_url(long_url),
            "error": "",
        }
    except urllib.error.HTTPError as exc:
        location = exc.headers.get("Location") if exc.headers else None
        if location:
            return {
                "ok": True,
                "short_url": url,
                "long_url": urllib.parse.urljoin(url, location),
                "clean_url": clean_tiktok_url(urllib.parse.urljoin(url, location)),
                "error": "",
            }
        return {"ok": False, "short_url": url, "long_url": "", "clean_url": "", "error": str(exc)}
    except Exception as exc:  # noqa: BLE001 - command-line helper should report any failure.
        return {"ok": False, "short_url": url, "long_url": "", "clean_url": "", "error": str(exc)}


def read_links(args: argparse.Namespace) -> list[str]:
    links: list[str] = []
    if args.file:
        with open(args.file, "r", encoding="utf-8") as handle:
            links.extend(line.strip() for line in handle if line.strip())
    links.extend(args.links)
    if args.stdin:
        links.extend(line.strip() for line in sys.stdin if line.strip())
    return links


def main() -> int:
    parser = argparse.ArgumentParser(description="Resolve TikTok short links to long and clean URLs.")
    parser.add_argument("links", nargs="*", help="TikTok links to resolve.")
    parser.add_argument("--file", help="UTF-8 text file containing one link per line.")
    parser.add_argument("--stdin", action="store_true", help="Read links from stdin.")
    parser.add_argument("--timeout", type=int, default=15, help="Per-link timeout in seconds.")
    parser.add_argument("--json", action="store_true", help="Print JSON Lines instead of a table.")
    parser.add_argument("--clean-only", action="store_true", help="Do not fetch; only strip query strings.")
    args = parser.parse_args()

    links = read_links(args)
    if not links:
        parser.error("provide at least one link, --file, or --stdin")

    rows = []
    for link in links:
        if args.clean_only:
            rows.append({"ok": True, "short_url": link, "long_url": link, "clean_url": clean_tiktok_url(link), "error": ""})
        else:
            rows.append(resolve_url(link, args.timeout))

    if args.json:
        for row in rows:
            print(json.dumps(row, ensure_ascii=False))
    else:
        for index, row in enumerate(rows, start=1):
            status = "OK" if row["ok"] else "ERR"
            print(f"{index}. {status}")
            print(f"   short: {row['short_url']}")
            print(f"   long : {row['long_url']}")
            print(f"   clean: {row['clean_url']}")
            if row["error"]:
                print(f"   error: {row['error']}")
    return 0 if all(row["ok"] for row in rows) else 1


if __name__ == "__main__":
    raise SystemExit(main())
