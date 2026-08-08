#!/usr/bin/env python3
"""One-off, re-runnable SEO/AEO pass over the static pages.

Idempotent: every insertion checks for its own marker first, so running it twice
changes nothing. What it does:

  1. Adds a /videos/ item to the site nav on every page that has one.
  2. Adds Open Graph + Twitter Card tags to pages missing them, derived from the
     page's own <title>, meta description and canonical.
  3. Adds a BreadcrumbList JSON-LD block to top-level pages that lack one.
  4. Fills the empty footer stub on the pillar pages with real internal links.
"""
import pathlib
import re
import html as htmllib

ROOT = pathlib.Path(__file__).parent
BASE = "https://agenticlakehouse.com"

TOP_LEVEL = [
    d.name
    for d in sorted(ROOT.iterdir())
    if d.is_dir() and d.name not in {"kb", "images", ".git", "videos"} and (d / "index.html").exists()
]

NAV_ITEM = '                    <li><a href="/videos/">Videos</a></li>\n'

PILLAR_FOOTER = """<div class="footer-grid">
                <div class="footer-brand">
                    <a href="/" class="footer-logo-link" aria-label="Agentic Lakehouse Home">
                        <span class="footer-logo-text">Agentic<br><strong>Lakehouse</strong></span>
                    </a>
                    <p class="footer-tagline">A working reference for agentic lakehouse and agentic analytics architecture.</p>
                </div>
                <div class="footer-col">
                    <h4 class="footer-col-title">Explore</h4>
                    <ul class="footer-nav-list">
                        <li><a href="/what-is-agentic-lakehouse/">What is an Agentic Lakehouse?</a></li>
                        <li><a href="/what-is-agentic-analytics/">What is Agentic Analytics?</a></li>
                        <li><a href="/agentic-lakehouse-architecture/">Architecture Guide</a></li>
                        <li><a href="/apache-iceberg/">Apache Iceberg</a></li>
                        <li><a href="/data-lakehouse/">Data Lakehouse</a></li>
                        <li><a href="/kb/">Knowledge Base</a></li>
                        <li><a href="/videos/">Video Explainers</a></li>
                    </ul>
                </div>
                <div class="footer-col">
                    <h4 class="footer-col-title">Partner Sites</h4>
                    <ul class="footer-nav-list">
                        <li><a href="https://alexmerceddata.com" target="_blank" rel="noopener">alexmerceddata.com</a></li>
                        <li><a href="https://datalakehousehub.com" target="_blank" rel="noopener">datalakehousehub.com</a></li>
                        <li><a href="https://iceberglakehouse.com" target="_blank" rel="noopener">iceberglakehouse.com</a></li>
                        <li><a href="https://dataengr.com" target="_blank" rel="noopener">dataengr.com</a></li>
                        <li><a href="https://semanticlakehouse.com" target="_blank" rel="noopener">semanticlakehouse.com</a></li>
                        <li><a href="https://opendatalakehouse.com" target="_blank" rel="noopener">opendatalakehouse.com</a></li>
                    </ul>
                </div>
            </div>
            <div class="footer-bottom">
                <p>&copy; 2026 AgenticLakehouse.com. A resource by <a href="https://alexmerceddata.com" target="_blank" rel="noopener">Alex Merced</a>.</p>
            </div>"""


def first(pattern, text, default=""):
    m = re.search(pattern, text, re.S)
    return m.group(1).strip() if m else default


def add_nav_videos(text):
    if "/videos/" in text or "site-nav" not in text:
        return text, False
    # Insert immediately before the trial CTA list item, else before </ul>.
    m = re.search(r'\n(\s*)<li><a href="[^"]*get-started[^"]*"[^>]*class="btn btn-primary nav-cta"', text)
    if m:
        indent = m.group(1)
        item = f'\n{indent}<li><a href="/videos/">Videos</a></li>'
        return text[: m.start()] + item + text[m.start():], True
    m = re.search(r'(<nav class="site-nav">.*?)(\s*</ul>)', text, re.S)
    if not m:
        return text, False
    return text[: m.end(1)] + "\n" + NAV_ITEM.rstrip("\n") + text[m.end(1):], True


def add_og(text, canonical):
    if "og:title" in text:
        return text, False
    title = htmllib.unescape(first(r"<title>(.*?)</title>", text))
    desc = first(r'<meta\s+name="description"\s+content="([^"]*)"', text)
    if not title:
        return text, False
    title_a = htmllib.escape(title, quote=True)
    desc_a = desc  # already an attribute value in the source
    block = f"""
    <!-- Open Graph / Twitter -->
    <meta property="og:type" content="article">
    <meta property="og:url" content="{canonical}">
    <meta property="og:title" content="{title_a}">
    <meta property="og:description" content="{desc_a}">
    <meta property="og:image" content="{BASE}/social-share.jpg">
    <meta property="og:site_name" content="Agentic Lakehouse">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title_a}">
    <meta name="twitter:description" content="{desc_a}">
    <meta name="twitter:image" content="{BASE}/social-share.jpg">
    <meta name="twitter:creator" content="@alexmercedcoder">
"""
    m = re.search(r'<link rel="canonical"[^>]*>', text)
    if not m:
        return text, False
    return text[: m.end()] + block + text[m.end():], True


def add_breadcrumb(text, name, canonical):
    if "BreadcrumbList" in text:
        return text, False
    block = f"""    <script type="application/ld+json">
    {{
      "@context": "https://schema.org",
      "@type": "BreadcrumbList",
      "itemListElement": [
        {{"@type": "ListItem", "position": 1, "name": "Home", "item": "{BASE}/"}},
        {{"@type": "ListItem", "position": 2, "name": "{name}", "item": "{canonical}"}}
      ]
    }}
    </script>
"""
    m = re.search(r"</head>", text)
    if not m:
        return text, False
    return text[: m.start()] + block + text[m.start():], True


def fill_footer(text):
    stub = '<div class="footer-content"></div>'
    if stub not in text:
        return text, False
    return text.replace(stub, PILLAR_FOOTER), True


def page_name(text, slug):
    h1 = first(r"<h1[^>]*>(.*?)</h1>", text)
    h1 = re.sub(r"<[^>]+>", "", h1).strip()
    return htmllib.escape(h1 or slug.replace("-", " ").title(), quote=True)


changed = {"nav": 0, "og": 0, "crumb": 0, "footer": 0}

targets = [(ROOT / "index.html", None)]
targets += [(ROOT / s / "index.html", s) for s in TOP_LEVEL]
kb = ROOT / "kb"
if kb.exists():
    if (kb / "index.html").exists():
        targets.append((kb / "index.html", "kb"))
    targets += [(d / "index.html", f"kb/{d.name}") for d in sorted(kb.iterdir()) if d.is_dir() and (d / "index.html").exists()]

for path, slug in targets:
    text = path.read_text(errors="ignore")
    orig = text

    text, ok = add_nav_videos(text)
    changed["nav"] += ok

    if slug is not None:
        canonical = f"{BASE}/{slug}/"
        text, ok = add_og(text, canonical)
        changed["og"] += ok
        # Breadcrumbs only for top-level pages; kb pages already carry them.
        if "/" not in slug:
            text, ok = add_breadcrumb(text, page_name(text, slug), canonical)
            changed["crumb"] += ok
        text, ok = fill_footer(text)
        changed["footer"] += ok

    if text != orig:
        path.write_text(text)

print(f"nav +/videos/: {changed['nav']}   og tags: {changed['og']}   "
      f"breadcrumbs: {changed['crumb']}   footers filled: {changed['footer']}")
