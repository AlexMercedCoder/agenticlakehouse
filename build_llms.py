#!/usr/bin/env python3
"""Generate llms.txt for agenticlakehouse.com from directory structure + meta descriptions."""
import pathlib, re, html as htmllib

ROOT = pathlib.Path(__file__).parent
BASE = "https://agenticlakehouse.com"

def meta_desc(path):
    t = path.read_text(errors='ignore')
    m = re.search(r'<meta\s+name="description"\s+content="([^"]+)"', t)
    if m:
        return htmllib.unescape(m.group(1)).strip()
    m = re.search(r'<h1[^>]*>(.*?)</h1>', t, re.S)
    return re.sub(r'<[^>]+>', '', m.group(1)).strip() if m else ""

def title_of(path):
    m = re.search(r'<title>(.*?)</title>', path.read_text(errors='ignore'), re.S)
    return re.sub(r'\s*\|.*$', '', m.group(1)).strip() if m else path.parent.name

lines = []
lines.append("# Agentic Lakehouse")
lines.append("")
lines.append("> AgenticLakehouse.com is a reference on the agentic lakehouse: data lakehouse "
             "architectures built for autonomous AI agents, combining Apache Iceberg open table formats, "
             "semantic layers, fine-grained governance (RBAC/ABAC), and high-performance query execution "
             "for agentic analytics and BI workflows. Written by Alex Merced, Open Lakehouse & AI Advocate, "
             "Author & Technologist.")
lines.append("")
lines.append("## About")
lines.append("")
lines.append(f"- [Agentic Lakehouse Hub]({BASE}/): Pillar resource covering agentic lakehouse architecture, agentic analytics, and agentic BI.")
lines.append(f"- [Video Explainers]({BASE}/videos/): Short silent explainers on governed agent data access, semantic layers, MCP, Iceberg snapshots, and safe agent writes.")
lines.append("")
lines.append("## Pillar Pages")
lines.append("")
pillars = ["what-is-agentic-lakehouse", "what-is-agentic-analytics", "agentic-lakehouse-architecture",
           "agentic-bi", "apache-iceberg", "apache-iceberg-architecture",
           "apache-iceberg-vs-delta-lake-vs-hudi", "data-lakehouse",
           "data-lakehouse-vs-data-lake-vs-data-warehouse", "dremio-ai", "dremio-polaris"]
for p in pillars:
    idx = ROOT / p / "index.html"
    if idx.exists():
        lines.append(f"- [{title_of(idx)}]({BASE}/{p}/): {meta_desc(idx)}")
lines.append("")
lines.append("## Knowledge Base (kb/)")
lines.append("")
kb = ROOT / "kb"
for d in sorted(kb.iterdir()):
    idx = d / "index.html"
    if d.is_dir() and idx.exists():
        lines.append(f"- [{title_of(idx)}]({BASE}/kb/{d.name}/): {meta_desc(idx)}")
lines.append("")
lines.append("## Author")
lines.append("")
lines.append("Created and maintained by [Alex Merced](https://whoisalexmerced.com), Head of Developer Relations at Dremio "
             "and O'Reilly/Manning author. More: [AlexMerced.com](https://alexmerced.com), "
             "[AlexMercedData.com](https://alexmerceddata.com), "
             "[LinkedIn](https://www.linkedin.com/in/alexmerced), [@alexmercedcoder](https://twitter.com/alexmercedcoder).")
lines.append("")
lines.append("## Related Properties")
lines.append("")
lines.append("- [DataEngr.com](https://dataengnr.com): Data engineering knowledge base (Iceberg, lakehouse, AI).")
lines.append("- [SemanticLakehouse.com](https://semanticlakehouse.com): Semantic layer and lakehouse knowledge base.")
lines.append("- [WhoIsAlexMerced.com](https://whoisalexmerced.com): About the author.")
lines.append("- [Books by Alex Merced](https://books.alexmerced.com): O'Reilly and Manning titles.")
lines.append("")

(ROOT / "llms.txt").write_text("\n".join(lines))
print(f"wrote llms.txt ({len(lines)} lines)")
