#!/usr/bin/env python3
"""Capture high-DPI hero screenshot for README."""
from pathlib import Path

from playwright.sync_api import sync_playwright

OUT = Path(__file__).resolve().parents[1] / "docs/assets/demo-screenshot.png"
URL = "http://127.0.0.1:8760/snapextract_v3.html"


def main() -> None:
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(
            viewport={"width": 1440, "height": 900},
            device_scale_factor=2,
        )
        page.goto(URL, wait_until="networkidle", timeout=120_000)
        page.wait_for_timeout(1500)
        page.evaluate(
            """
            () => {
              const splash = document.getElementById('splash');
              if (splash) {
                splash.classList.remove('hidden');
                splash.classList.add('flex');
              }
            }
            """
        )
        page.wait_for_timeout(800)
        hero = page.locator("#hero")
        hero.screenshot(path=str(OUT), type="png")
        browser.close()
    print(f"Saved {OUT}")


if __name__ == "__main__":
    main()
