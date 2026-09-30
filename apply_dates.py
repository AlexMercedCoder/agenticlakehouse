#!/usr/bin/env python3
"""Write git-derived datePublished / dateModified into each page's JSON-LD.

The main page node (Article, TechArticle, WebPage, CollectionPage, ...) gets
dateModified from page_dates.py and datePublished from the first commit of the
file when it has none. The homepage byline <time> is kept in step. Edits are
string-level so the surrounding JSON formatting is preserved; every changed
block is re-parsed to prove it is still valid JSON.

Run after committing content changes, then commit the result as [mechanical].
"""
import json
import pathlib
import re

from page_dates import page_dates

ROOT = pathlib.Path(__file__).parent
MAIN_TYPES = ["TechArticle", "Article", "BlogPosting", "CollectionPage", "WebPage", "AboutPage"]
LD = re.compile(r'(<script type="application/ld\+json">)(.*?)(</script>)', re.S)


def set_dates(body, published, modified):
    if re.search(r'"dateModified"\s*:', body):
        body = re.sub(r'("dateModified"\s*:\s*")[^"]*(")', rf"\g<1>{modified}\g<2>", body, count=1)
        if not re.search(r'"datePublished"\s*:', body):
            body = re.sub(r'("dateModified"\s*:\s*"[^"]*")', rf'"datePublished": "{published}", \g<1>', body, count=1)
        return body, True
    for t in MAIN_TYPES:
        m = re.search(rf'"@type"\s*:\s*(?:"{t}"|\[[^\]]*"{t}"[^\]]*\])', body)
        if m:
            sep = ", " if " " in m.group(0) else ","
            ins = f'{sep}"datePublished":{" " if sep == ", " else ""}"{published}"' if not re.search(r'"datePublished"\s*:', body) else ""
            ins += f'{sep}"dateModified":{" " if sep == ", " else ""}"{modified}"'
            return body[:m.end()] + ins + body[m.end():], True
    return body, False


changed = skipped = 0
for p in sorted(ROOT.glob("**/index.html")):
    if p.relative_to(ROOT).parts[0] in {"network", ".git", "scripts", "python"}:
        continue
    published, modified = page_dates(p)
    if not modified:
        continue
    html = p.read_text()
    done = False

    def repl(m):
        global done
        if done or "Person" in m.group(2) and '"sameAs"' in m.group(2):
            return m.group(0)
        body, ok = set_dates(m.group(2), published, modified)
        if ok:
            json.loads(body)
            done = True
        return m.group(1) + body + m.group(3)

    out = LD.sub(repl, html)
    if p == ROOT / "index.html":
        from datetime import date
        d = date.fromisoformat(modified)
        out = re.sub(r'(<p class="answer-byline">.*?<time datetime=")[^"]*(">)[^<]*(</time>)',
                     rf"\g<1>{modified}\g<2>{d.strftime('%B')} {d.day}, {d.year}\g<3>", out, count=1, flags=re.S)
    if not done:
        skipped += 1
        print("no main JSON-LD node:", p.relative_to(ROOT))
    if out != html:
        p.write_text(out)
        changed += 1
print(f"apply_dates: {changed} pages updated, {skipped} without a main node")
