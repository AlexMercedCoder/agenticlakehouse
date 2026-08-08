#!/usr/bin/env python3
"""Regenerate sitemap.xml from the directory structure.

Scans for top-level pages and kb/*/index.html pages and rebuilds the
sitemap so it never drifts from the actual content.
"""
import pathlib
from datetime import date

BASE = "https://agenticlakehouse.com"
ROOT = pathlib.Path(__file__).parent
TODAY = date.today().isoformat()

urls = []  # (loc, priority)

# Homepage
urls.append((f"{BASE}/", "1.0"))

# Top-level pillar pages: directories with an index.html (excluding kb, images, python)
for d in sorted(ROOT.iterdir()):
    if d.is_dir() and d.name not in {"kb", "images", "python", ".git", "assets"} and (d / "index.html").exists():
        # Pillar pages and the video gallery carry more weight than the rest.
        priority = "0.8" if d.name in {
            "what-is-agentic-lakehouse", "what-is-agentic-analytics",
            "agentic-lakehouse-architecture", "videos",
        } else "0.6"
        urls.append((f"{BASE}/{d.name}/", priority))

# KB pages
kb = ROOT / "kb"
if kb.exists():
    for d in sorted(kb.iterdir()):
        if d.is_dir() and (d / "index.html").exists():
            urls.append((f"{BASE}/kb/{d.name}/", "0.6"))

xml = ['<?xml version="1.0" encoding="UTF-8"?>',
       '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for loc, priority in urls:
    xml.append("  <url>")
    xml.append(f"    <loc>{loc}</loc>")
    xml.append(f"    <lastmod>{TODAY}</lastmod>")
    xml.append(f"    <priority>{priority}</priority>")
    xml.append("  </url>")
xml.append("</urlset>")

(ROOT / "sitemap.xml").write_text("\n".join(xml) + "\n")
print(f"Wrote {len(urls)} URLs to sitemap.xml")
