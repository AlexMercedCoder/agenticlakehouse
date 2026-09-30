#!/usr/bin/env python3
"""Regenerate sitemap.xml from the directory structure.

Scans for top-level pages and kb/*/index.html pages and rebuilds the
sitemap so it never drifts from the actual content. lastmod comes from git
(see page_dates.py), so commit page changes before running this.
"""
import pathlib

from page_dates import page_dates

BASE = "https://agenticlakehouse.com"
ROOT = pathlib.Path(__file__).parent

urls = []  # (loc, priority, file)

# Homepage
urls.append((f"{BASE}/", "1.0", ROOT / "index.html"))

# Top-level pillar pages: directories with an index.html (excluding kb, images, python)
for d in sorted(ROOT.iterdir()):
    if d.is_dir() and d.name not in {"kb", "images", "python", ".git", "assets", "network", "scripts"} and (d / "index.html").exists():
        # Pillar pages and the video gallery carry more weight than the rest.
        priority = "0.8" if d.name in {
            "what-is-agentic-lakehouse", "agentic-lakehouse-architecture", "videos", "patterns",
        } else "0.6"
        urls.append((f"{BASE}/{d.name}/", priority, d / "index.html"))
        # Nested pages (the /patterns/ section).
        if d.name == "patterns":
            for sub in sorted(d.iterdir()):
                if sub.is_dir() and (sub / "index.html").exists():
                    urls.append((f"{BASE}/{d.name}/{sub.name}/", "0.8", sub / "index.html"))

# KB pages
kb = ROOT / "kb"
if (kb / "index.html").exists():
    urls.append((f"{BASE}/kb/", "0.8", kb / "index.html"))
if kb.exists():
    for d in sorted(kb.iterdir()):
        if d.is_dir() and (d / "index.html").exists():
            urls.append((f"{BASE}/kb/{d.name}/", "0.6", d / "index.html"))

xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc, priority, path in urls:
    _, lastmod = page_dates(path)
    xml.append("  <url>")
    xml.append(f"    <loc>{loc}</loc>")
    if lastmod:
        xml.append(f"    <lastmod>{lastmod}</lastmod>")
    xml.append(f"    <priority>{priority}</priority>")
    xml.append("  </url>")
xml.append("</urlset>")

(ROOT / "sitemap.xml").write_text("\n".join(xml) + "\n")
print(f"Wrote {len(urls)} URLs to sitemap.xml")
