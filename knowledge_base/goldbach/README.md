Goldbach notes and ingestion

This folder is for notes extracted from `Goldbach/goldbach.pdf` and other Goldbach-related documentation.

Current contents:

- `goldbach_summary.md` — auto-generated placeholder; run `tools/ingest_goldbach_pdf.py` to populate with extracted text and a short summary.

Ingestion guidance

- The ingestion script will attempt multiple PDF extraction methods and create a set of Markdown files with extracted text, a short automated summary, and a small "Key terms" list.
- After ingestion, review and edit the generated Markdown to add authoritative commentary and remove OCR noise.
