# ShaloTrack — website

Static site. No build step. Open `index.html`, or deploy the folder as-is
to Cloudflare Pages.

## Structure

    index.html          Everything — markup + a single inline <script>
    CSS/index.css       The design system
    CSS/legal.css       Privacy / terms / support pages
    PHOTOGRAPHY.md      Read before launch
    BRAND.md            Colour, type and logo rules

## Design notes

**Type.** Archivo Bold for display, Inter for body. Accent phrases are set
in italic orange, mirroring how the logo sets SHALO navy and TRACK orange.
See BRAND.md.

**Colour.** Navy `#021f4a` and orange `#fa6908`, both sampled directly from
the logo file. Orange is rationed — italic accents, one CTA per section,
list marks.

**Structure over decoration.** Sections are separated by hairline rules
and white space, not boxes and drop shadows. Numerals (01–07) run through
the page as the connective device.

**Rhythm.** Light sections and dark sections alternate. Dark carries the
product and the contact form; light carries the offer.

## Layout — read before touching `.shell`

Bootstrap 5.3 (CDN) handles grid, flex and spacing. `CSS/index.css` handles
identity.

`.shell` is the container. It **must keep its horizontal padding**:

    .shell { width:100%; max-width:1328px; padding-inline:24px; margin-inline:auto; }

Bootstrap's `.row` applies negative side margins equal to half the gutter
(`g-5` = −24px per side). That padding is what absorbs them. Remove it and
every row punches past the viewport — the whole site scrolls sideways on
phones, which is exactly what happened once already.

For the same reason, **don't use bare `g-5` on a row.** Use `g-4 g-lg-5`:
24px gutters on phones (12px overhang, inside the 18px mobile padding),
48px from `lg` up. If you ever need a bigger mobile gutter, raise the mobile
`.shell` padding to match half of it.

The nav collapses to a burger at **991px**, not 768 — seven links plus the
CTA don't fit on a tablet.

## Accessibility

Reduced-motion is respected throughout. Focus rings are visible.
Contrast was checked on both the light and dark sections. If you change
`--stone` on the light background, re-check it.

## If the layout looks broken after an update

The stylesheet is linked as `CSS/index.css?v=2`. If you edit the CSS, bump
that number. Live Server and browsers cache aggressively, and because the
filename never changes you can end up running new markup against an old
stylesheet — which is exactly how the logo once rendered at full size and
crushed the nav. `Ctrl+F5` clears it; bumping `?v=` prevents it.

## Before deploying

    python tests/site_test.py

37 checks — asset integrity, horizontal overflow at 13 widths, the nav logo
in both scroll states, touch targets, the mobile menu, form validation,
accessibility and SEO. Exits non-zero on failure. See `tests/README.md`.

## Known follow-ups

- Self-host the photos (see PHOTOGRAPHY.md)
- Swap the inline SVG pin for your official logo export (see BRAND.md)
- Self-host the two fonts if you'd rather not depend on Google Fonts
- The contact form opens WhatsApp; it does not post to a server
