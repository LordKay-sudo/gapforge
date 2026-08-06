#!/usr/bin/env python3
"""Capture review UI screenshots from review-ui-capture.html (no Docker required)."""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "demo-recordings"
HTML = OUT / "review-ui-capture.html"


def main() -> int:
    if not HTML.is_file():
        print(f"Missing {HTML}", file=sys.stderr)
        return 1

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("Installing playwright...", file=sys.stderr)
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright", "-q"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        from playwright.sync_api import sync_playwright

    url = HTML.resolve().as_uri()
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1400, "height": 900})

        page.goto(url, wait_until="networkidle")
        page.locator("#capture-fail").screenshot(path=str(OUT / "screenshot-review-ontology-fail.png"))
        print("Saved screenshot-review-ontology-fail.png")

        page.locator("#capture-pass").screenshot(path=str(OUT / "screenshot-review-ontology-pass.png"))
        print("Saved screenshot-review-ontology-pass.png")

        browser.close()

    print(f"Screenshots in {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
