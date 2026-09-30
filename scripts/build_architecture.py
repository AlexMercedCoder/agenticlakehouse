#!/usr/bin/env python3
"""Build the agentic lakehouse reference architecture diagram.

Writes, under agentic-lakehouse-architecture/:
  agentic-lakehouse-reference-architecture.svg        adapts to light and dark
  agentic-lakehouse-reference-architecture-light.png  2400 x 1920
  agentic-lakehouse-reference-architecture-dark.png   2400 x 1920
and refreshes the inline copy of the diagram in index.html (between the
<!-- arch-svg:start --> and <!-- arch-svg:end --> markers, forced dark to
match the site).

PNGs are rendered with headless Chrome (google-chrome on PATH).
License: CC BY 4.0, attribution Alex Merced.

    python3 scripts/build_architecture.py
"""
import html
import pathlib
import re
import shutil
import subprocess
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[1]
OUT = ROOT / "agentic-lakehouse-architecture"
NAME = "agentic-lakehouse-reference-architecture"

W, H = 1200, 930
MAIN_X, MAIN_W = 40, 850
RAIL_X, RAIL_W = 910, 250
BAND_H, GAP, TOP = 88, 20, 118

# (key, number, name, job, examples, connector label to the band below)
LAYERS = [
    ("agents", 7, "Agents", "Ask questions and act for people and teams",
     ["Assistants", "Coding agents", "Workflows"], "tool calls over MCP"),
    ("interface", 6, "Agent interface (MCP)", "Typed tools the agent can discover and call",
     ["MCP servers", "Tool schemas", "OAuth identity"], "metric requests, never raw SQL"),
    ("semantic", 5, "Semantic layer", "Business definitions and agent-safe views",
     ["Metrics", "Dimensions", "Governed views"], "governed SQL"),
    ("engine", 4, "Query engine", "Plans and runs SQL, enforces grants",
     ["Dremio", "Trino", "Spark", "DuckDB"], "table metadata and credentials"),
    ("catalog", 3, "Catalog", "Names tables and tracks their metadata",
     ["Apache Polaris", "Iceberg REST", "Nessie"], "snapshots and manifests"),
    ("format", 2, "Table format", "Files become tables with ACID snapshots",
     ["Apache Iceberg", "Snapshots", "Time travel"], "Parquet data files"),
    ("storage", 1, "Object storage", "Holds every byte once, in open formats",
     ["Amazon S3", "Azure ADLS", "Google GCS", "MinIO"], None),
]
GOVERNANCE = ("governance", "G", "Governance",
              ["Agent identity", "Row and column policies", "Query guardrails", "Cost caps", "Audit log", "Catalog access control"])

# light, dark accent per layer
ACCENT = {
    "agents": ("#6d28d9", "#c4b5fd"),
    "interface": ("#1d4ed8", "#93c5fd"),
    "semantic": ("#0f766e", "#5eead4"),
    "engine": ("#0e7490", "#67e8f9"),
    "catalog": ("#a16207", "#fde047"),
    "format": ("#c2410c", "#fdba74"),
    "storage": ("#475569", "#cbd5e1"),
    "governance": ("#b91c1c", "#fca5a5"),
}

FONT = "Inter, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif"


def chip_w(text):
    return int(len(text) * 7.9 + 26)


def style():
    light = "\n".join(f"  --{k}: {v[0]};" for k, v in ACCENT.items())
    dark = "\n".join(f"  --{k}: {v[1]};" for k, v in ACCENT.items())
    dark_vars = f"""  --bg: #0f172a; --band: #1e293b; --chip: #0f172a; --ink: #f1f5f9; --muted: #cbd5e1; --line: #94a3b8; --badge-ink: #0f172a;
{dark}"""
    return f"""<style>
.alr {{
  --bg: #ffffff; --band: #f8fafc; --chip: #ffffff; --ink: #0f172a; --muted: #334155; --line: #64748b; --badge-ink: #ffffff;
{light}
}}
@media (prefers-color-scheme: dark) {{
  .alr:not(.alr-light) {{
{dark_vars}
  }}
}}
.alr.alr-dark {{
{dark_vars}
}}
.alr text {{ font-family: {FONT}; fill: var(--ink); }}
.alr .bg {{ fill: var(--bg); }}
.alr .band {{ fill: var(--band); stroke-width: 2; }}
.alr .chip {{ fill: var(--chip); stroke-width: 1.5; }}
.alr .title {{ font-size: 30px; font-weight: 700; }}
.alr .subtitle {{ font-size: 17px; fill: var(--muted); }}
.alr .name {{ font-size: 21px; font-weight: 700; }}
.alr .job {{ font-size: 15px; fill: var(--muted); }}
.alr .chiptext {{ font-size: 14px; font-weight: 500; }}
.alr .num {{ font-size: 15px; font-weight: 700; fill: var(--badge-ink); }}
.alr .flow {{ stroke: var(--line); stroke-width: 2; fill: none; }}
.alr .flowhead {{ fill: var(--line); }}
.alr .flowlabel {{ font-size: 13.5px; fill: var(--muted); font-style: italic; }}
.alr .railitem {{ font-size: 15px; }}
.alr .foot {{ font-size: 13.5px; fill: var(--muted); }}
</style>"""


def svg(force=None):
    cls = "alr" + (f" alr-{force}" if force else "")
    p = "alr-" + (force or "auto")  # id prefix, unique per variant on one page
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" class="{cls}" role="img" aria-labelledby="{p}-title {p}-desc">',
        f'<title id="{p}-title">Agentic lakehouse reference architecture</title>',
        f'<desc id="{p}-desc">A stack of seven numbered layers, top (7) to bottom (1): agents; agent interface such as MCP; semantic layer; query engine; catalog; table format such as Apache Iceberg; and object storage. '
        "Agents call typed tools over MCP, the interface sends metric requests to the semantic layer, which compiles governed SQL for the query engine. "
        "The engine reads table metadata from the catalog, snapshots and manifests from the table format, and Parquet data files from object storage. "
        "A governance rail runs beside the agent interface, semantic layer, query engine, and catalog: agent identity, row and column policies, query guardrails, cost caps, audit log, and catalog access control. "
        "Diagram by Alex Merced, CC BY 4.0, agenticlakehouse.com.</desc>",
        style(),
        f'<rect class="bg" width="{W}" height="{H}" rx="20"/>',
        f'<text class="title" x="{MAIN_X}" y="56">Agentic lakehouse reference architecture</text>',
        f'<text class="subtitle" x="{MAIN_X}" y="86">How AI agents reach open lakehouse data through governed, typed interfaces</text>',
    ]
    for i, (key, num, name, job, examples, flow) in enumerate(LAYERS):
        y = TOP + i * (BAND_H + GAP)
        parts.append(f'<rect class="band" x="{MAIN_X}" y="{y}" width="{MAIN_W}" height="{BAND_H}" rx="12" style="stroke: var(--{key})"/>')
        parts.append(f'<rect x="{MAIN_X}" y="{y}" width="8" height="{BAND_H}" rx="4" style="fill: var(--{key})"/>')
        parts.append(f'<circle cx="{MAIN_X + 42}" cy="{y + BAND_H / 2}" r="17" style="fill: var(--{key})"/>')
        parts.append(f'<text class="num" x="{MAIN_X + 42}" y="{y + BAND_H / 2 + 5}" text-anchor="middle">{num}</text>')
        parts.append(f'<text class="name" x="{MAIN_X + 74}" y="{y + 38}">{html.escape(name)}</text>')
        parts.append(f'<text class="job" x="{MAIN_X + 74}" y="{y + 64}">{html.escape(job)}</text>')
        # chips, right-aligned inside the band
        x = MAIN_X + MAIN_W - 16
        for ex in reversed(examples):
            w = chip_w(ex)
            x -= w
            parts.append(f'<rect class="chip" x="{x}" y="{y + 27}" width="{w}" height="34" rx="17" style="stroke: var(--{key})"/>')
            parts.append(f'<text class="chiptext" x="{x + w / 2}" y="{y + 49}" text-anchor="middle">{html.escape(ex)}</text>')
            x -= 10
        if flow:
            fy = y + BAND_H
            cx = MAIN_X + 42
            parts.append(f'<line class="flow" x1="{cx}" y1="{fy + 2}" x2="{cx}" y2="{fy + GAP - 7}"/>')
            parts.append(f'<path class="flowhead" d="M{cx - 5} {fy + GAP - 8} L{cx + 5} {fy + GAP - 8} L{cx} {fy + GAP - 1} Z"/>')
            parts.append(f'<text class="flowlabel" x="{cx + 16}" y="{fy + GAP - 5}">{html.escape(flow)}</text>')

    # governance rail beside interface..catalog (bands 1..4)
    key, num, name, items = GOVERNANCE
    top = TOP + 1 * (BAND_H + GAP)
    bottom = TOP + 4 * (BAND_H + GAP) + BAND_H
    parts.append(f'<rect class="band" x="{RAIL_X}" y="{top}" width="{RAIL_W}" height="{bottom - top}" rx="12" style="stroke: var(--{key})"/>')
    parts.append(f'<rect x="{RAIL_X + 12}" y="{top + 1}" width="{RAIL_W - 24}" height="6" rx="3" style="fill: var(--{key})"/>')
    parts.append(f'<text class="name" x="{RAIL_X + 22}" y="{top + 46}">{name}</text>')
    parts.append(f'<text class="job" x="{RAIL_X + 22}" y="{top + 72}">Applies to layers 3 to 6</text>')
    for j, item in enumerate(items):
        iy = top + 118 + j * 44
        parts.append(f'<rect x="{RAIL_X + 22}" y="{iy - 12}" width="10" height="10" rx="2" style="fill: var(--{key})"/>')
        parts.append(f'<text class="railitem" x="{RAIL_X + 42}" y="{iy - 2}">{html.escape(item)}</text>')
    for i in range(1, 5):
        y = TOP + i * (BAND_H + GAP) + BAND_H / 2
        parts.append(f'<line x1="{MAIN_X + MAIN_W}" y1="{y}" x2="{RAIL_X}" y2="{y}" stroke-width="2" stroke-dasharray="4 4" style="stroke: var(--{key})"/>')

    parts.append(f'<text class="foot" x="{MAIN_X}" y="{H - 34}">Diagram: Alex Merced, agenticlakehouse.com. License: CC BY 4.0 (creativecommons.org/licenses/by/4.0). Examples are illustrative, not endorsements.</text>')
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def render_png(svg_text, path):
    chrome = shutil.which("google-chrome") or shutil.which("chromium")
    if not chrome:
        raise SystemExit("google-chrome not found; cannot render PNG")
    with tempfile.TemporaryDirectory() as tmp:
        page = pathlib.Path(tmp) / "d.html"
        page.write_text(f'<!doctype html><html><head><meta charset="utf-8"><style>html,body{{margin:0;background:transparent}}svg{{display:block;width:{W}px;height:{H}px}}</style></head><body>{svg_text}</body></html>')
        subprocess.run(
            [chrome, "--headless=new", "--disable-gpu", "--hide-scrollbars", "--force-device-scale-factor=2",
             f"--window-size={W},{H}", "--default-background-color=00000000", f"--screenshot={path}", page.as_uri()],
            check=True, capture_output=True,
        )


def main():
    adaptive = svg()
    (OUT / f"{NAME}.svg").write_text('<?xml version="1.0" encoding="UTF-8"?>\n' + adaptive)
    render_png(svg("light"), OUT / f"{NAME}-light.png")
    render_png(svg("dark"), OUT / f"{NAME}-dark.png")
    index = OUT / "index.html"
    page = index.read_text()
    inline = svg("dark").replace(f'width="{W}" height="{H}" ', "")
    new, n = re.subn(r"<!-- arch-svg:start -->.*?<!-- arch-svg:end -->",
                     lambda _: f"<!-- arch-svg:start -->\n{inline}<!-- arch-svg:end -->", page, flags=re.S)
    if n != 1:
        raise SystemExit("index.html needs one <!-- arch-svg:start --> ... <!-- arch-svg:end --> marker pair")
    index.write_text(new)
    print("build_architecture: wrote SVG, two PNGs, and the inline copy")


if __name__ == "__main__":
    main()
