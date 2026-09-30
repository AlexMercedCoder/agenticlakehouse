#!/usr/bin/env python3
"""Build the /patterns/ section from scripts/patterns/*.html body fragments.

Each pattern page is a step-by-step implementation guide whose code matches
the companion demo repository (mcp-semantic-lakehouse-demo). Page metadata
lives in PAGES below; the body of each page lives in
scripts/patterns/<slug>.html. Inside a fragment, fenced blocks

    ```python
    code here, written raw
    ```

become escaped <pre><code> blocks, so code can be pasted from the repo as is.

Run order (see README.md):
    python3 build_patterns.py
    node scripts/apply-network.mjs
    git commit ...
    python3 apply_dates.py && python3 build_sitemap.py && python3 build_llms.py
"""
import html
import json
import pathlib
import re

ROOT = pathlib.Path(__file__).parent
SRC = ROOT / "scripts" / "patterns"
BASE = "https://agenticlakehouse.com"
CROSSLINKS = json.loads((ROOT / "data" / "crosslinks.json").read_text())
PERSON = {"@id": "https://alexmerced.com/#alexmerced"}
# First publication of the /patterns/ section. Stated explicitly because git
# --follow can pair a new page with an older, similar file.
PUBLISHED = "2026-09-29"

# Tested versions, shown on every page. Keep in step with the demo README.
TESTED = "Tested September 29, 2026 with Python 3.12 and 3.13, mcp 2.2.0 (official MCP Python SDK), pyiceberg 0.12.0, and duckdb 1.5.6."

PAGES = [
    {
        "slug": "agent-safe-governed-views",
        "title": "Agent-Safe Governed Views | Agentic Lakehouse Patterns",
        "h1": "Agent-safe governed views",
        "subtitle": "Give agents views, never raw tables: a curated column list, joins done once, and an engine that cannot read anything else.",
        "description": "Step-by-step pattern for agent-safe governed views over Apache Iceberg tables: raw and governed schemas, PII left out, locked engine, and tests, with working Python code.",
        "leader": "one-copy-many-readers",
        "kb": [("/kb/pii-data-protection/", "PII data protection"), ("/kb/data-masking/", "Data masking"), ("/kb/governed-ai-querying/", "Governed AI querying"), ("/kb/iceberg-view-specification/", "Iceberg view specification")],
    },
    {
        "slug": "row-and-column-policies-for-agents",
        "title": "Row and Column Policies for AI Agents | Agentic Lakehouse Patterns",
        "h1": "Row and column policies for agents",
        "subtitle": "Tie what an agent can see to the identity it acts for, and enforce it in the data path instead of the prompt.",
        "description": "How to enforce row-level and column-level security for AI agents: roles in a semantic model, row filters baked into governed views, denied metrics and dimensions, and tests that try to escape.",
        "leader": "governance-for-agents",
        "kb": [("/kb/row-level-security/", "Row-level security"), ("/kb/column-level-security/", "Column-level security"), ("/kb/ai-agent-authorization/", "AI agent authorization"), ("/kb/abac-data/", "ABAC for data")],
    },
    {
        "slug": "query-guardrails-for-agents",
        "title": "Query Guardrails for AI Agents: Allowlists, Limits, Timeouts, Cost Caps | Agentic Lakehouse Patterns",
        "h1": "Query guardrails for agents",
        "subtitle": "Allowlists, row limits, timeouts, cost caps, and an audit log, each one a few lines of code with a test.",
        "description": "Step-by-step query guardrails for AI agents on lakehouse data: name and relation allowlists, row limits, statement timeouts, Iceberg metadata cost caps, session budgets, and audit logs.",
        "leader": "cost-and-latency",
        "kb": [("/kb/safe-action-loops/", "Safe action loops"), ("/kb/lakehouse-cost-optimization/", "Lakehouse cost optimization"), ("/kb/iceberg-manifest-files/", "Iceberg manifest files"), ("/kb/trustworthy-ai-execution/", "Trustworthy AI execution")],
    },
    {
        "slug": "semantic-layer-over-mcp",
        "title": "Expose a Semantic Layer to AI Agents over MCP | Agentic Lakehouse Patterns",
        "h1": "Exposing a semantic layer to agents over MCP",
        "subtitle": "Metrics and dimensions as MCP tools: the agent picks business definitions, the server writes the SQL.",
        "description": "Build an MCP server that exposes a semantic layer to AI agents: tool design, metric definitions as tool descriptions, read-only annotations, errors the agent can act on, and in-process tests.",
        "leader": "semantic-layer-as-contract",
        "kb": [("/kb/semantic-layer/", "Semantic layer"), ("/kb/ai-semantic-layer/", "AI semantic layer"), ("/kb/metric-store/", "Metric store"), ("/kb/text-to-sql/", "Text-to-SQL")],
    },
    {
        "slug": "mcp-server-over-iceberg-catalog",
        "title": "Build an MCP Server over an Apache Iceberg Catalog | Agentic Lakehouse Patterns",
        "h1": "An MCP server over an Iceberg catalog",
        "subtitle": "PyIceberg for the catalog and table metadata, DuckDB for execution, MCP for the agent, all runnable on a laptop.",
        "description": "Build an MCP server on top of an Apache Iceberg catalog with PyIceberg: a local SQL catalog, partitioned tables, reading into DuckDB, and using Iceberg metadata for cost estimates.",
        "leader": "open-interfaces",
        "kb": [("/kb/iceberg-catalog/", "Iceberg catalog"), ("/kb/iceberg-rest-catalog/", "Iceberg REST catalog"), ("/kb/apache-polaris/", "Apache Polaris"), ("/kb/llm-data-access/", "LLM data access")],
    },
]

INDEX = {
    "slug": "",
    "title": "Agentic Lakehouse Implementation Patterns | Step by Step with Code",
    "h1": "Implementation patterns",
    "subtitle": "Step-by-step patterns for giving AI agents safe, governed access to lakehouse data, each with code you can run.",
    "description": "Implementation patterns for the agentic lakehouse: agent-safe governed views, row and column policies, query guardrails, a semantic layer over MCP, and an MCP server over an Iceberg catalog.",
    "leader": "evaluation-and-trust",
}

NAV = [
    ("/what-is-agentic-lakehouse/", "Agentic Lakehouse"),
    ("/agentic-bi/", "Agentic BI"),
    ("/agentic-lakehouse-architecture/", "Architecture"),
    ("/patterns/", "Patterns"),
    ("https://luma.com/agenticlakehouse", "Community"),
    ("/kb/", "Knowledge Base"),
    ("/books/", "Books"),
    ("/videos/", "Videos"),
]

FENCE = re.compile(r"```([a-z]*)\n(.*?)\n```", re.S)


def render_fences(body):
    def repl(m):
        lang = m.group(1) or "text"
        return f'<pre class="code" data-lang="{lang}"><code>{html.escape(m.group(2))}</code></pre>'
    return FENCE.sub(repl, body)


def nav_html():
    items = []
    for url, label in NAV:
        cur = ' aria-current="page"' if url == "/patterns/" else ""
        ev = ' data-network-event="cta_luma_community"' if "luma.com" in url else ""
        items.append(f'            <li><a href="{url}"{cur}{ev}>{label}</a></li>')
    items.append('            <li><a href="https://amdatalakehouse.substack.com/p/the-open-lakehouse-explained-then" class="btn btn-primary nav-cta" data-network-event="cta_laptop_lakehouse">Try it on your laptop</a></li>')
    return "\n".join(items)


def business_link(key):
    leader = CROSSLINKS["leader"][key]
    return f"""        <aside class="business-link" aria-label="Why this matters to the business"><div class="container"><div class="business-link__inner">
            <p class="business-link__label">Why this matters to the business</p>
            <p>{html.escape(leader['why'], quote=False)} <a href="{leader['url']}">Read &ldquo;{html.escape(leader['title'], quote=False)}&rdquo; on Agentic Analytics Now</a>.</p>
        </div></div></aside>"""


def page(meta, body, crumbs):
    url = f"{BASE}/patterns/" + (f"{meta['slug']}/" if meta["slug"] else "")
    t = html.escape(meta["title"])
    d = html.escape(meta["description"])
    main_type = "TechArticle" if meta["slug"] else "CollectionPage"
    ld = {
        "@context": "https://schema.org",
        "@type": main_type,
        "headline": meta["h1"][0].upper() + meta["h1"][1:],
        "description": meta["description"],
        "url": url,
        "author": PERSON,
        "publisher": {"@type": "Organization", "name": "Agentic Lakehouse", "url": f"{BASE}/"},
        "inLanguage": "en",
        "datePublished": PUBLISHED,
    }
    if meta["slug"]:
        ld["proficiencyLevel"] = "Expert"
        ld["dependencies"] = "Python 3.10+, mcp 2.x, pyiceberg 0.12, duckdb 1.5"
        ld["isPartOf"] = {"@type": "CollectionPage", "@id": f"{BASE}/patterns/", "name": "Agentic lakehouse implementation patterns"}
    else:
        ld["hasPart"] = [{"@type": "TechArticle", "headline": p["h1"][0].upper() + p["h1"][1:], "url": f"{BASE}/patterns/{p['slug']}/"} for p in PAGES]
    bc = {
        "@context": "https://schema.org",
        "@type": "BreadcrumbList",
        "itemListElement": [
            {"@type": "ListItem", "position": i + 1, "name": n, "item": u} for i, (n, u) in enumerate(crumbs)
        ],
    }
    crumb_html = " &rsaquo; ".join(
        f'<a href="{u.replace(BASE, "")}">{html.escape(n)}</a>' if i < len(crumbs) - 1 else html.escape(n)
        for i, (n, u) in enumerate(crumbs)
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{t}</title>
    <meta name="description" content="{d}">
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Outfit:wght@500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="/style.css">
    <link rel="icon" type="image/svg+xml" href="data:image/svg+xml,<svg xmlns=%22http://www.w3.org/2000/svg%22 viewBox=%220 0 64 64%22><rect width=%2264%22 height=%2264%22 rx=%2216%22 fill=%22%233999e5%22/><path d=%22M12 32 Q 32 12 52 32%22 stroke=%22white%22 stroke-width=%226%22 fill=%22none%22 stroke-linecap=%22round%22/><path d=%22M12 44 Q 32 24 52 44%22 stroke=%22white%22 stroke-width=%226%22 fill=%22none%22 stroke-linecap=%22round%22/></svg>">
    <link rel="canonical" href="{url}">
    <meta property="og:type" content="article">
    <meta property="og:url" content="{url}">
    <meta property="og:title" content="{t}">
    <meta property="og:description" content="{d}">
    <meta property="og:image" content="{BASE}/social-share.jpg">
    <meta property="og:site_name" content="Agentic Lakehouse">
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{t}">
    <meta name="twitter:description" content="{d}">
    <meta name="twitter:image" content="{BASE}/social-share.jpg">
    <meta name="twitter:creator" content="@AMdatalakehouse">
    <script type="application/ld+json">
{json.dumps(ld, indent=2)}
    </script>
    <script type="application/ld+json">
{json.dumps(bc, indent=2)}
    </script>
    <script defer src="https://unpkg.com/@phosphor-icons/web"></script>
<!-- network:head:start -->
<!-- network:head:end -->
</head>
<body>
    <header class="site-header"><div class="container">
        <a href="/" class="logo"><span class="logo-icon"><i class="ph-fill ph-waves"></i></span><span class="logo-text">The Agentic Lakehouse</span></a>
        <nav class="site-nav"><ul>
{nav_html()}
        </ul></nav>
    </div></header>

    <main>
        <section class="page-header pattern-header"><div class="container">
            <div class="breadcrumb">{crumb_html}</div>
            <h1 class="gradient-text">{html.escape(meta['h1'][0].upper() + meta['h1'][1:])}</h1>
            <p class="hero-subtitle mx-auto">{html.escape(meta['subtitle'])}</p>
        </div></section>
{business_link(meta['leader'])}

        <article class="pattern container">
{body}
        </article>
    </main>
    <!-- network:footer:start -->
<!-- network:footer:end -->
  <script src="/webmcp/alex-merced-webmcp.js" defer></script>
  <script src="/webmcp/init.js" defer></script>
</body>
</html>
"""


def companion_box():
    return f"""            <aside class="pattern-companion" aria-label="Companion code">
                <p class="pattern-companion__label">Companion code</p>
                <p>Every snippet on this page comes from <strong>mcp-semantic-lakehouse-demo</strong>, a small Apache-2.0 Python project that runs on a laptop: PyIceberg with a local SQLite catalog, DuckDB, a YAML semantic model, and the official MCP Python SDK. Repository link coming soon.</p>
                <p class="pattern-companion__tested">{html.escape(TESTED)}</p>
            </aside>"""


def related(meta):
    others = [p for p in PAGES if p["slug"] != meta["slug"]]
    links = "\n".join(f'                    <a href="/patterns/{p["slug"]}/">{html.escape(p["h1"][0].upper() + p["h1"][1:])}</a>' for p in others)
    kb = "\n".join(f'                    <a href="{u}">{html.escape(n)}</a>' for u, n in meta.get("kb", []))
    return f"""            <nav class="pattern-related" aria-label="Related patterns and terms">
                <h2>More patterns</h2>
                <div class="pattern-related__grid">
{links}
                    <a href="/patterns/">All patterns</a>
                    <a href="/agentic-lakehouse-architecture/">Reference architecture</a>
                </div>
                <h2>Glossary terms</h2>
                <div class="pattern-related__grid">
{kb}
                </div>
            </nav>"""


def main():
    home = ("Home", f"{BASE}/")
    section = ("Patterns", f"{BASE}/patterns/")
    written = 0
    for meta in PAGES:
        body = render_fences((SRC / f"{meta['slug']}.html").read_text())
        body = body.replace("<!-- companion -->", companion_box())
        body += "\n" + related(meta)
        out = ROOT / "patterns" / meta["slug"] / "index.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        new = page(meta, body, [home, section, (meta["h1"][0].upper() + meta["h1"][1:], f"{BASE}/patterns/{meta['slug']}/")])
        written += _write(out, new)
    body = render_fences((SRC / "index.html").read_text())
    body = body.replace("<!-- companion -->", companion_box())
    written += _write(ROOT / "patterns" / "index.html", page(INDEX, body, [home, section]))
    print(f"build_patterns: {len(PAGES) + 1} pages, {written} changed")


def _write(path, new):
    """Write a page, keeping the network blocks apply-network.mjs already filled in."""
    if path.exists():
        old = path.read_text()
        for name in ("head", "footer"):
            m = re.search(rf"<!-- network:{name}:start -->.*?<!-- network:{name}:end -->", old, re.S)
            if m:
                new = re.sub(rf"<!-- network:{name}:start -->.*?<!-- network:{name}:end -->", lambda _: m.group(0), new, flags=re.S)
        # Keep the dateModified that apply_dates.py wrote.
        dm = re.search(r'"dateModified": "[^"]*"', old)
        if dm and '"dateModified"' not in new:
            new = re.sub(r'("@type": "(?:TechArticle|CollectionPage)")', lambda m: f"{m.group(1)}, {dm.group(0)}", new, count=1)
        if old == new:
            return 0
    path.write_text(new)
    return 1


if __name__ == "__main__":
    main()
