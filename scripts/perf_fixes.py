#!/usr/bin/env python3
"""Page-weight fixes applied to every HTML page (idempotent).

1. Inline SVG icons instead of the Phosphor icon fonts.
2. Load the Google Fonts stylesheet without blocking first render.

Icons: 
The site used to load the whole @phosphor-icons/web package from unpkg (six
icon fonts plus their CSS, about 160 KB for the duotone font alone) to draw
about 35 icons. This script swaps each <i class="ph-WEIGHT ph-NAME"></i> for
the matching inline SVG from data/icons.json and removes the unpkg script tag.
It is idempotent, so run it after build_patterns.py or after adding pages:

    python3 scripts/perf_fixes.py

To use a new icon, add its SVG body to data/icons.json (from
@phosphor-icons/core, same version) under the key "WEIGHT ph-NAME".
"""
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
ICONS = json.loads((ROOT / "data" / "icons.json").read_text())["icons"]
SKIP = {"network", ".git", "scripts", "node_modules"}

TAG = re.compile(r'<i class="((?:ph|ph-bold|ph-fill|ph-duotone) ph-([a-z0-9-]+))"></i>')
LOADER = re.compile(r'\s*(?:<!-- Icons \(using Phosphor[^>]*-->\s*)?<script defer src="https://unpkg\.com/@phosphor-icons/web"></script>')

FONTS = re.compile(r'<link\s+href="(https://fonts\.googleapis\.com/css2\?[^"]+)"\s+rel="stylesheet"\s*/?>')


def async_fonts(html):
    """Fonts use display=swap, so the page can paint in fallback fonts first."""
    return FONTS.sub(lambda m: (f'<link rel="stylesheet" href="{m.group(1)}" media="print" onload="this.media=\'all\'">'
                                f'<noscript><link rel="stylesheet" href="{m.group(1)}"></noscript>'), html)


def svg(key, name, extra=""):
    return (f'<svg class="ph-icon ph-{name}" viewBox="0 0 256 256" width="1em" height="1em" '
            f'fill="currentColor" aria-hidden="true" focusable="false"{extra}>{ICONS[key]}</svg>')


def convert(html):
    # The mobile menu toggle swaps between a list and an x icon (see script.js).
    html = html.replace('<i class="ph ph-list"></i>',
                        svg("ph ph-list", "list") + svg("ph ph-x", "x", " hidden"))

    def repl(m):
        if m.group(1) not in ICONS:
            raise SystemExit(f"icon {m.group(1)!r} missing from data/icons.json")
        return svg(m.group(1), m.group(2))

    html = TAG.sub(repl, html)
    return async_fonts(LOADER.sub("", html))


def main():
    changed = 0
    for p in sorted(ROOT.glob("**/*.html")):
        if p.relative_to(ROOT).parts[0] in SKIP:
            continue
        old = p.read_text()
        new = convert(old)
        if new != old:
            p.write_text(new)
            changed += 1
    print(f"perf_fixes: {changed} pages changed")


if __name__ == "__main__":
    main()
