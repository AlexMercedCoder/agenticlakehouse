#!/usr/bin/env python3
"""Git-derived page dates for agenticlakehouse.com.

lastmod / dateModified = the date of the last commit that changed the page's
content. datePublished = the date of the first commit that added the page.

Commits that only touch shared chrome (network footer, nav, WebMCP loader,
Person block, performance attributes) are skipped, so a site-wide footer edit
does not make all 200+ pages look freshly modified. Mark any future chrome-only
commit with "[mechanical]" in its subject and it is skipped too.

Uncommitted edits are not seen: commit content changes first, then run
apply_dates.py and build_sitemap.py, and commit their output as "[mechanical]".
"""
import pathlib
import re
import subprocess

ROOT = pathlib.Path(__file__).parent

SKIP = re.compile(
    r"\[mechanical\]|footer|webmcp|site navigation|cta strip|^cwv|person @id|timezone",
    re.I,
)


def _log(path):
    out = subprocess.run(
        ["git", "log", "--follow", "--format=%cs%x09%s", "--", str(path)],
        cwd=ROOT, capture_output=True, text=True, check=False,
    ).stdout
    rows = []
    for line in out.splitlines():
        if "\t" in line:
            d, s = line.split("\t", 1)
            rows.append((d, s))
    return rows  # newest first


def page_dates(path):
    """Return (date_published, date_modified) as YYYY-MM-DD, or (None, None)."""
    rows = _log(path)
    if not rows:
        return None, None
    published = rows[-1][0]
    content = [d for d, s in rows if not SKIP.search(s)]
    modified = content[0] if content else published
    return published, max(modified, published)


if __name__ == "__main__":
    import sys
    for p in sys.argv[1:]:
        print(p, *page_dates(pathlib.Path(p)))
