# Automated site checks

    pip install playwright
    playwright install chromium

Serve the site (Live Server, or `python -m http.server 5500`), then:

    python tests/site_test.py                    # defaults to 127.0.0.1:5500
    python tests/site_test.py http://localhost:8080

Exits `1` on any failure, so it can gate a deploy.

## What it checks

| # | Check | Why it exists |
|---|---|---|
| 1 | Console errors, failed requests | Catches JS breakage and 404s |
| 2 | Every local asset resolves; every `<img>` decodes | **A missing logo file left the header blank** |
| 3 | Nav logo visible at top *and* after the hero | The logo swaps background-image on `.stuck`; if the second file is missing the header silently goes blank mid-page |
| 4 | No horizontal overflow at 13 widths, 320→1440 | **Bootstrap row negative margins escaped `.shell` and made every phone width scroll sideways** |
| 5 | Touch targets ≥44px (respects invisible hit areas) | Links were 23–29px |
| 6 | Burger opens, sets `aria-expanded`, locks scroll, closes on link | |
| 7 | In-page anchors resolve, empty form is blocked, one `<h1>`, alt text, labels, title/description/canonical/OG | |
| 8 | Content visible under `prefers-reduced-motion` | Reveal animations can leave content stuck at `opacity: 0` |

Checks 2, 3 and 4 exist because those bugs actually shipped.

## Notes

- External assets (Bootstrap CDN, Google Fonts, Unsplash) are reported but
  not failed, so the suite still runs offline.
- `PW_CHROMIUM=/path/to/chrome` uses an existing browser instead of
  Playwright's own build.
- Check 5 scrolls each candidate into view before probing, because
  `elementFromPoint` returns null outside the viewport.
