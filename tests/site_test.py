#!/usr/bin/env python3
"""
ShaloTrack — automated site checks.

    pip install playwright
    playwright install chromium

    python tests/site_test.py                        # defaults to 127.0.0.1:5500
    python tests/site_test.py http://localhost:8080

Exits 1 if anything fails, so it can gate a deploy.

Every check here exists because something actually broke in this project:
a logo asset that 404'd and left the header blank, Bootstrap rows overflowing
the viewport on every phone width, a stale cached stylesheet running against
new markup, and CSS classes renamed in one file but not the other.
"""

import sys, os
from urllib.parse import urljoin, urlparse
from playwright.sync_api import sync_playwright

BASE = (sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:5500").rstrip("/")
PAGE = f"{BASE}/index.html"
WIDTHS = [320, 360, 375, 390, 414, 480, 576, 768, 820, 991, 1024, 1280, 1440]
TAP_MIN = 44

G, R, Y, B, X = "\033[32m", "\033[31m", "\033[33m", "\033[1m", "\033[0m"
counts = {"pass": 0, "fail": 0, "warn": 0}


def ok(m, d=""):
    counts["pass"] += 1
    print(f"  {G}PASS{X} {m}" + (f"  {d}" if d else ""))


def bad(m, d=""):
    counts["fail"] += 1
    print(f"  {R}FAIL{X} {m}" + (f"\n       {d}" if d else ""))


def warn(m, d=""):
    counts["warn"] += 1
    print(f"  {Y}WARN{X} {m}" + (f"  {d}" if d else ""))


def head(t):
    print(f"\n{B}{t}{X}")


def main():
    origin = f"{urlparse(PAGE).scheme}://{urlparse(PAGE).netloc}"

    with sync_playwright() as p:
        launch = {}
        if os.environ.get("PW_CHROMIUM"):
            launch["executable_path"] = os.environ["PW_CHROMIUM"]
        browser = p.chromium.launch(**launch)
        ctx = browser.new_context()

        # ── 1. Load integrity ────────────────────────────────
        head("1. Load integrity")
        errors, failed = [], []
        page = ctx.new_page()
        page.on("console", lambda m: errors.append(m.text[:140]) if m.type == "error" else None)
        page.on("pageerror", lambda e: errors.append(f"pageerror: {str(e)[:140]}"))
        page.on("response", lambda r: failed.append(f"{r.status} {r.url}") if r.status >= 400 else None)

        page.goto(PAGE, wait_until="load", timeout=30000)
        page.evaluate("document.documentElement.style.scrollBehavior='auto'")
        page.wait_for_timeout(1200)

        same = [u for u in failed if origin in u]
        ext = [u for u in failed if origin not in u]
        bad("No failed same-origin requests", "\n       ".join(same)) if same else ok("No failed same-origin requests")
        if ext:
            warn(f"{len(ext)} external request(s) failed (CDN/fonts — expected if offline)")
        bad("No console errors", "\n       ".join(errors)) if errors else ok("No console errors")

        # ── 2. Asset references ──────────────────────────────
        head("2. Asset references")
        assets = page.evaluate("""() => {
          const u = new Set();
          document.querySelectorAll('img[src]').forEach(i => u.add(i.src));
          document.querySelectorAll('link[href]').forEach(l => u.add(l.href));
          document.querySelectorAll('script[src]').forEach(s => u.add(s.src));
          document.querySelectorAll('video source[src]').forEach(s => u.add(s.src));
          for (const sh of document.styleSheets) {
            try { for (const r of sh.cssRules) {
              const bg = r.style && r.style.backgroundImage;
              if (bg && bg.includes('url(')) {
                [...bg.matchAll(/url\\(["']?([^"')]+)["']?\\)/g)].forEach(m => {
                  if (!m[1].startsWith('data:')) u.add(new URL(m[1], sh.href || location.href).href);
                });
              }
            }} catch (e) {}
          }
          return [...u];
        }""")
        broken = []
        for a in assets:
            if not a.startswith(origin):
                continue
            try:
                r = ctx.request.get(a)
                if r.status >= 400:
                    broken.append(f"{r.status} {a.replace(origin,'')}")
            except Exception:
                broken.append(f"ERR {a.replace(origin,'')}")
        bad("All local assets resolve", "\n       ".join(broken)) if broken \
            else ok("All local assets resolve", f"({len(assets)} refs checked)")

        undecoded = page.evaluate("""async () => {
          const i = [...document.images];
          await Promise.all(i.map(x => x.complete ? 1 : new Promise(r => { x.onload = r; x.onerror = r; })));
          return i.filter(x => !x.naturalWidth).map(x => x.getAttribute('src'));
        }""")
        bad("All <img> decoded", ", ".join(undecoded)) if undecoded else ok("All <img> decoded")

        # ── 3. Nav logo in BOTH scroll states ────────────────
        # The logo swaps background-image on .stuck. If the second file is
        # missing, the header silently goes blank after the hero.
        head("3. Nav logo, both scroll states")

        def logo_state(label, y):
            page.evaluate("y => window.scrollTo(0, y)", y)
            page.wait_for_timeout(600)
            s = page.evaluate("""() => {
              const w = document.querySelector('.nav .wordmark');
              if (!w) return {missing: true};
              const cs = getComputedStyle(w), r = w.getBoundingClientRect();
              const m = cs.backgroundImage.match(/url\\(["']?([^"')]+)["']?\\)/);
              return {stuck: document.querySelector('.nav').classList.contains('stuck'),
                      url: m ? m[1] : null, w: Math.round(r.width), h: Math.round(r.height),
                      opacity: cs.opacity, display: cs.display, visibility: cs.visibility};
            }""")
            if s.get("missing"):
                return bad(f"{label}: .wordmark not found")
            if not s.get("url"):
                return bad(f"{label}: no background-image set")
            try:
                res = ctx.request.get(s["url"])
                loaded = res.status < 400
                status = res.status
            except Exception:
                loaded, status = False, "ERR"
            visible = s["w"] > 40 and s["h"] > 10 and s["opacity"] != "0" \
                and s["visibility"] != "hidden" and s["display"] != "none"
            name = s["url"].split("/")[-1]
            if loaded and visible:
                ok(f"{label} (stuck={s['stuck']})", f"{s['w']}x{s['h']} {name}")
            else:
                bad(f"{label} (stuck={s['stuck']})",
                    f"{'image loads' if loaded else f'IMAGE {status}'} · box {s['w']}x{s['h']} · opacity {s['opacity']} · {name}")

        vh = page.evaluate("window.innerHeight")
        logo_state("Logo at top", 0)
        logo_state("Logo after hero", int(vh * 1.6))
        logo_state("Logo mid-page", int(page.evaluate("document.body.scrollHeight") * 0.6))
        page.evaluate("window.scrollTo(0,0)")

        # ── 4. Horizontal overflow ───────────────────────────
        head("4. Horizontal overflow")
        wp = ctx.new_page()
        for w in WIDTHS:
            wp.set_viewport_size({"width": w, "height": 850})
            wp.goto(PAGE, wait_until="domcontentloaded", timeout=30000)
            wp.wait_for_timeout(420)
            wp.evaluate("document.querySelectorAll('[data-r],.wipe').forEach(e=>e.classList.add('in'))")
            wp.wait_for_timeout(120)
            r = wp.evaluate("""() => {
              const vw = document.documentElement.clientWidth, off = [];
              document.querySelectorAll('body *').forEach(el => {
                const b = el.getBoundingClientRect();
                if (!b.width && !b.height) return;
                if (getComputedStyle(el).position === 'fixed') return;
                if (b.right - vw > 1)
                  off.push(el.tagName.toLowerCase()+'.'+(el.className||'').toString().split(' ')[0]+' +'+Math.round(b.right-vw)+'px');
              });
              return {vw, sw: document.documentElement.scrollWidth, off: [...new Set(off)].slice(0,4)};
            }""")
            if r["sw"] > r["vw"] + 1:
                bad(f"{w}px no horizontal scroll", f"scrollWidth {r['sw']} > {r['vw']}   {', '.join(r['off'])}")
            else:
                ok(f"{w}px no horizontal scroll")
        wp.close()

        # ── 5. Touch targets ─────────────────────────────────
        head("5. Touch targets (390px)")
        mp = ctx.new_page()
        mp.set_viewport_size({"width": 390, "height": 844})
        mp.goto(PAGE, wait_until="load")
        mp.evaluate("document.documentElement.style.scrollBehavior='auto'")
        mp.wait_for_timeout(800)
        mp.evaluate("document.documentElement.style.scrollBehavior='auto'; document.querySelectorAll('[data-r],.wipe').forEach(e=>e.classList.add('in'))")
        small = mp.evaluate("""(MIN) => {
          const out = [];
          const els = [...document.querySelectorAll('a,button,summary,input,select,textarea')];
          for (const el of els) {
            let b = el.getBoundingClientRect();
            if (!b.width || !b.height || b.height >= MIN) continue;
            // elementFromPoint only works inside the viewport, so bring the
            // element into view before probing for an expanded hit area.
            el.scrollIntoView({block: 'center', behavior: 'instant'});
            b = el.getBoundingClientRect();
            const probe = dy => {
              const e = document.elementFromPoint(b.left+b.width/2, b.top+b.height/2+dy);
              return !!(e && (e === el || el.contains(e) || e.parentElement === el));
            };
            const h = MIN/2 - 2;
            if (probe(-h) && probe(h)) continue;   // expanded hit area covers it
            out.push(el.tagName.toLowerCase()+'.'+(el.className||'').toString().split(' ')[0]
                     +' '+Math.round(b.height)+'px "'+(el.textContent||'').trim().slice(0,22)+'"');
          }
          return [...new Set(out)];
        }""", TAP_MIN)
        if small:
            warn(f"{len(small)} target(s) under {TAP_MIN}px", "\n       " + "\n       ".join(small[:8]))
        else:
            ok(f"All touch targets >= {TAP_MIN}px effective")

        # ── 6. Mobile menu ───────────────────────────────────
        # section 5 scrolls the page around; reset before interacting
        mp.evaluate("window.scrollTo(0,0)")
        mp.wait_for_timeout(300)
        head("6. Mobile menu")
        m = mp.evaluate("""() => {
          const b = document.getElementById('burger'), m = document.getElementById('menu');
          if (!b || !m) return {missing: true};
          return {visible: getComputedStyle(b).display !== 'none'};
        }""")
        if m.get("missing"):
            bad("Burger and menu present")
        else:
            ok("Burger visible at 390px") if m["visible"] else bad("Burger visible at 390px")
            mp.click("#burger"); mp.wait_for_timeout(450)
            o = mp.evaluate("""() => ({open: document.getElementById('menu').classList.contains('open'),
                exp: document.getElementById('burger').getAttribute('aria-expanded'),
                lock: document.body.classList.contains('nav-open')})""")
            if o["open"] and o["exp"] == "true" and o["lock"]:
                ok("Menu opens, aria-expanded=true, scroll locked")
            else:
                bad("Menu opens correctly", str(o))
            mp.click("#menu a"); mp.wait_for_timeout(450)
            closed = mp.evaluate("!document.getElementById('menu').classList.contains('open')")
            ok("Menu closes on link click") if closed else bad("Menu closes on link click")
        mp.close()

        # ── 7. Links, form, a11y, SEO ────────────────────────
        head("7. Links, form, accessibility, SEO")
        dead = page.evaluate("""() => [...document.querySelectorAll('a[href^="#"]')]
            .map(a => a.getAttribute('href'))
            .filter(h => h.length > 1 && !document.querySelector(h))""")
        bad("All in-page anchors resolve", ", ".join(dead)) if dead else ok("All in-page anchors resolve")

        fr = page.evaluate("""() => {
          const f = document.getElementById('form'); if (!f) return {missing: true};
          let opened = false; const real = window.open; window.open = () => { opened = true; };
          f.dispatchEvent(new Event('submit', {cancelable: true, bubbles: true}));
          window.open = real;
          return {opened, msg: (document.getElementById('formMsg')||{}).textContent || ''};
        }""")
        if fr.get("missing"):
            bad("Contact form present")
        elif not fr["opened"] and fr["msg"].strip():
            ok("Empty form blocked with a message", f'"{fr["msg"].strip()[:48]}"')
        else:
            bad("Empty form blocked with a message", str(fr))

        a = page.evaluate("""() => ({
          h1: document.querySelectorAll('h1').length,
          noAlt: [...document.images].filter(i => !i.hasAttribute('alt')).length,
          noLabel: [...document.querySelectorAll('input,select,textarea')]
                    .filter(i => !i.id || !document.querySelector('label[for="'+i.id+'"]')).length,
          lang: document.documentElement.lang || '',
          title: document.title || '',
          desc: (document.querySelector('meta[name=description]')||{}).content || '',
          canonical: !!document.querySelector('link[rel=canonical]'),
          favicon: !!document.querySelector('link[rel~=icon]'),
          og: document.querySelectorAll('meta[property^="og:"]').length,
          viewport: !!document.querySelector('meta[name=viewport]')
        })""")
        ok("Exactly one <h1>") if a["h1"] == 1 else bad("Exactly one <h1>", f"found {a['h1']}")
        ok("All images have alt") if a["noAlt"] == 0 else bad("All images have alt", f"{a['noAlt']} missing")
        ok("All form fields labelled") if a["noLabel"] == 0 else bad("All form fields labelled", f"{a['noLabel']} unlabelled")
        ok("html[lang] set", a["lang"]) if a["lang"] else bad("html[lang] set")
        ok("viewport meta present") if a["viewport"] else bad("viewport meta present")
        ok("Title length sane", f"{len(a['title'])} chars") if 10 < len(a["title"]) < 65 else warn("Title length", f"{len(a['title'])} chars")
        ok("Meta description length sane", f"{len(a['desc'])} chars") if 50 < len(a["desc"]) < 165 else warn("Meta description length", f"{len(a['desc'])} chars")
        ok("Canonical set") if a["canonical"] else warn("Canonical set")
        ok("Favicon set") if a["favicon"] else warn("Favicon set")
        ok("Open Graph tags present", str(a["og"])) if a["og"] >= 3 else warn("Open Graph tags", str(a["og"]))

        # ── 8. Reduced motion ────────────────────────────────
        head("8. Reduced motion")
        rm = browser.new_context(reduced_motion="reduce").new_page()
        rm.goto(PAGE, wait_until="load")
        rm.wait_for_timeout(900)
        stuck = rm.evaluate("[...document.querySelectorAll('[data-r]')].filter(e=>getComputedStyle(e).opacity==='0').length")
        ok("Content visible with reduced motion") if stuck == 0 \
            else bad("Content visible with reduced motion", f"{stuck} elements stuck at opacity 0")
        rm.close()

        browser.close()

    print("\n" + "─" * 58)
    print(f"{B}{counts['pass']} passed, {counts['fail']} failed, {counts['warn']} warnings{X}")
    print("─" * 58)
    sys.exit(1 if counts["fail"] else 0)


if __name__ == "__main__":
    main()
