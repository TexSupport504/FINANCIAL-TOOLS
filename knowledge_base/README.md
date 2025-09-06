# Knowledge Base — FINANCIAL-TOOLS

This folder contains curated, version-controlled knowledge the Repo Assistant uses when making changes and generating analysis.

Top-level topics:

- `global_economics/` — macro themes, global indicators, central bank policies, cross-border capital flows.
- `us_economics/` — US-specific policy, Fed guidance, fiscal policy, labor and inflation dynamics.
- `market_sentiment/` — sentiment sources, news flows, on-chain signals, retail/institutional indicators.
- `goldbach/` — research notes and artifacts related to the Goldbach strategy (extracted from `Goldbach/goldbach.pdf` and other documentation).

Guidelines:

- Keep notes factual and cite sources (PDF page, URL, date).
- Store each major concept as a single markdown file under the appropriate subfolder.
- Keep summaries short (1-3 paragraphs) and include a short "Key takeaways" list and relevant tags.
- Add a `meta.yml` at the topic root if needed to track provenance.

How the agent should use this:

- When asked to change strategy code or produce analysis, consult the KB folder for authoritative summaries before changing code.
- Prefer to reference KB excerpts in PR descriptions and include citations to the original source.
