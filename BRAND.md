# Brand notes

Everything here is derived from `IMG/logo.jpeg`, not invented.

## Colour — sampled from the logo file

| Token | Hex | Use |
|---|---|---|
| `--navy` | `#021F4A` | Dark sections, body text, primary buttons |
| `--orange` | `#FA6908` | Accent only — italic words, one CTA per section, list marks |
| `--navy-3` | `#103D78` | Lifted navy for gradients |
| `--mist` | `#F4F7FA` | Light alternate sections |

The orange is deliberately rationed. It appears on italic accent words, one
primary button per section, and the small skewed list marks. If it starts
turning up everywhere it stops signalling anything.

## Type — mirrors the wordmark

Your logo sets SHALO in navy and TRACK in orange, both italic, in a bold
geometric sans. The site does the same thing at every scale: **Archivo Bold**
for display, with the accent phrase set in **italic orange**. That single
move is what ties page to logo.

    Every vehicle, always *within sight.*
    GPS *Tracking*  ·  Vehicle *Security*  ·  Fleet *Management*

Inter carries body copy. The skewed list marks (`transform: skewX(-12deg)`)
echo the wordmark's slant. Don't add a third typeface.

## Tagline and pillars

"Always Connected" is used as the hero chip and closes the opening statement.
Your three pillars — GPS Tracking, Vehicle Security, Fleet Management — are
the three capability sections and the hero strip, rather than headings I made
up.

## Logo assets

Your real logo is used throughout. `logo.jpeg` couldn't be dropped in
directly — a white-background JPEG shows as a white box on navy — so it was
processed into a proper asset set. The white background was knocked out and
un-premultiplied so the anti-aliased edges stay clean, and a light variant
was made by mapping navy to white while preserving the orange.

| File | Use |
|---|---|
| `logo-lockup-light.png` | Horizontal pin + wordmark, knockout. Nav over hero, footer. |
| `logo-lockup.png` | Same lockup, full colour. Nav once scrolled. |
| `logo-full-light.png` | Full stacked lockup incl. tagline + services, knockout. |
| `logo-full.png` | Full stacked lockup, full colour. |
| `logo-mark-light.png` / `logo-mark.png` | Pin only. |
| `favicon-32.png`, `apple-touch-icon.png` | Browser and iOS icons. |
| `logo.jpeg` | Original. Kept for OG/social, where white is fine. |

The nav cross-fades between the two lockups: knockout while transparent over
the hero, full colour once the white bar appears. Both `<img>` tags are
stacked, one absolutely positioned, and CSS swaps opacity on `.nav.stuck`.

The horizontal lockup was composited from the stacked original — the pin and
the SHALOTRACK wordmark placed side by side, with the two tagline lines
dropped, because a stacked four-line lockup is too tall for a 34px nav.

**If you have vector artwork**, swap these PNGs for SVG. Everything is
raster-derived from a 1536×1024 JPEG, which is sharp enough at the sizes used
here but won't scale indefinitely.

---

## Modern CSS layer

The stylesheet ends with a block of current CSS, tiered by support so
nothing breaks on older browsers.

### Shipped outright (near-universal support)

| Feature | Where | What it does |
|---|---|---|
| `text-wrap: balance` | every heading | Evens out ragged line breaks. The hero and the "Fitted, activated and reporting" heading both wrapped badly before this. |
| `text-wrap: pretty` | body copy | Kills orphaned last words. |
| `@property --edge` | featured plan | Types a custom angle so a conic gradient can actually animate. |
| `field-sizing: content` | contact textarea | Grows with typing instead of scrolling. |
| `:has()` | form fields | Label lights up when a field is focused or filled — no JS. |
| container queries | team cards | Cards respond to their own width, not the viewport. |
| `oklch()` | gradient stops | Perceptually even orange ramp; no muddy midpoint. |

### Progressive enhancement (behind `@supports`)

| Feature | Where |
|---|---|
| `animation-timeline: view()` | All reveals, the capability photo wipes, hero drift, photo-band parallax, step rules drawing in |
| `animation-timeline: scroll(root)` | The scroll progress bar |
| `@starting-style` | Mobile menu opens from a real start state, no first-frame flash |
| `@view-transition` | Cross-fade to the legal pages |

These run on the compositor thread, so they stay smooth even when the main
thread is busy. **The JavaScript stands down when they're supported** —
`CSS.supports('animation-timeline','view()')` is checked before the
IntersectionObserver is created, and the scroll listener for the progress
bar is never attached.

Every scroll-driven rule sits inside `@media (prefers-reduced-motion:
no-preference)`, and `html:not(.js) [data-r]` guarantees content is visible
even with JavaScript disabled entirely — verified: 53 revealed elements, 0
invisible with JS off.
