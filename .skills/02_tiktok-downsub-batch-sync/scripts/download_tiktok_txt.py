#!/usr/bin/env python3
"""Resolve a TikTok short link in BitBrowser, close its tab, then get DownSub TXT."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
from playwright.sync_api import sync_playwright


PROFILE_ID = "a5145d814904441fbc3f60debc17cbfc"
VIDEO_ID_RE = re.compile(r"tiktok\.com/@[^/]+/video/(\d+)")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("short_url", help="TikTok short link to open in BitBrowser")
    parser.add_argument("--cdp-url", required=True, help="BitBrowser DevTools URL, e.g. http://127.0.0.1:1248")
    args = parser.parse_args()

    with sync_playwright() as playwright:
        browser = playwright.chromium.connect_over_cdp(args.cdp_url)
        context = next(
            (
                item
                for item in browser.contexts
                if any(PROFILE_ID in page.url for page in item.pages)
            ),
            None,
        )
        if context is None:
            raise RuntimeError("The CDP endpoint is not the configured 6-anyidphoto profile")

        tiktok_page = context.new_page()
        try:
            tiktok_page.goto(args.short_url, wait_until="domcontentloaded", timeout=45_000)
            if VIDEO_ID_RE.search(tiktok_page.url) is None:
                tiktok_page.wait_for_url(VIDEO_ID_RE, wait_until="domcontentloaded", timeout=15_000)
            long_url = tiktok_page.url
        finally:
            tiktok_page.close()
        print(f"TIKTOK_TAB_CLOSED {tiktok_page.is_closed()}")

        match = VIDEO_ID_RE.search(long_url)
        if match is None:
            raise RuntimeError(f"Short link did not resolve to a TikTok video: {long_url}")
        video_id = match.group(1)
        print(f"LONG_URL {long_url}")

        downsub_page = context.new_page()
        try:
            downsub_page.goto("https://downsub.com/", wait_until="domcontentloaded", timeout=45_000)
            downsub_page.locator("input[type=text]").fill(long_url)
            downsub_page.get_by_role("button", name="DOWNLOAD").click()
            try:
                downsub_page.get_by_text("TXT", exact=True).first.wait_for(timeout=25_000)
            except PlaywrightTimeoutError as exc:
                print(f"DOWNSUB_STATE {downsub_page.title()} {ascii(downsub_page.locator('body').inner_text()[:1200])}")
                raise RuntimeError("DownSub did not provide a TXT subtitle; reject this video") from exc
            if downsub_page.locator(f'a[href*="/video/{video_id}"]').count() == 0:
                raise RuntimeError("DownSub result does not match the resolved TikTok video ID")
            print(f"DOWNSUB_TITLE {ascii(downsub_page.title())}")
            with downsub_page.expect_download(timeout=30_000) as download_info:
                downsub_page.get_by_text("TXT", exact=True).first.click()
            download = download_info.value
            target_dir = Path.cwd() / ".skills" / "01_video-subtitle-md-sync" / ".tmp" / "downsub"
            target_dir.mkdir(parents=True, exist_ok=True)
            target = target_dir / f"{video_id}.txt"
            download.save_as(str(target))
            if not target.read_text(encoding="utf-8-sig").strip():
                raise RuntimeError("Downloaded TXT is empty; reject this video")
            print(f"TXT_PATH {target.relative_to(Path.cwd())}")
            return 0
        finally:
            downsub_page.close()


if __name__ == "__main__":
    raise SystemExit(main())
