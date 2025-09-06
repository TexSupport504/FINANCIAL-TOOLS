Knowledge Base schema and contribution guidelines

Purpose

This document defines the simple schema and contribution workflow for the repo knowledge base.

Schema (file-level)

- Each topic is a directory under `knowledge_base/` (e.g., `us_economics/`).
- Each concept is a Markdown file: `YYYY-MM-DD--slug.md` or `slug.md`.
- Frontmatter (optional, YAML) may include:
  - title: human title
  - tags: ["policy","inflation","goldbach"]
  - source: file or URL
  - source_page: page number (if from a PDF)
  - author: who added the note
  - created: ISO timestamp

Recommended file template

---
# Title

Short summary (1-3 sentences)

Key takeaways

- bullet 1
- bullet 2

Details / quotes

> Quote or excerpt (with citation)

References

- Source: `Goldbach/goldbach.pdf` page X

Change process

- Add a new file in the relevant folder and open a PR.
- Add tests or usage examples if the note produces code changes (e.g., new parameters, thresholds).

Indexing / search

- For now the KB is filesystem-based (Markdown). If you want vector search later, we can add a small script to embed files and push to a vector DB or local FAISS store.
