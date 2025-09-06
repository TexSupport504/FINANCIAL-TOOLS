"""Ingest Goldbach PDF and create Markdown notes.

Usage:
    python tools/ingest_goldbach_pdf.py --pdf Goldbach/goldbach.pdf --out knowledge_base/goldbach

This script attempts multiple extraction methods (PyPDF2, pdfplumber, PyMuPDF) and writes:
 - raw-page-<n>.md : raw extracted text per page
 - summary.md : short automated summary
 - key_terms.md : detected keyword occurrences with page contexts

Note: This script performs local file IO only. It does not call external services.
"""
import argparse
import os
import re
from collections import defaultdict

try:
    import pdfplumber
except Exception:
    pdfplumber = None
try:
    import PyPDF2
except Exception:
    PyPDF2 = None
try:
    import fitz
except Exception:
    fitz = None


def extract_with_pdfplumber(path):
    if not pdfplumber:
        return None
    out = []
    with pdfplumber.open(path) as pdf:
        for p in pdf.pages:
            text = p.extract_text() or ""
            out.append(text)
    return out


def extract_with_pypdf2(path):
    if not PyPDF2:
        return None
    out = []
    try:
        with open(path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            for p in reader.pages:
                out.append(p.extract_text() or "")
    except Exception:
        return None
    return out


def extract_with_pymupdf(path):
    if not fitz:
        return None
    out = []
    doc = fitz.open(path)
    for page in doc:
        out.append(page.get_text() or "")
    doc.close()
    return out


def detect_key_terms(pages, terms=None):
    if terms is None:
        terms = [
            'algorithm', 'phase', 'pivot', 'premium', 'discount', 'entry', 'stop', 'ATR', 'RSI', 'EMA', 'Bollinger', 'divergence'
        ]
    found = defaultdict(list)
    for i, text in enumerate(pages):
        low = (text or '').lower()
        for t in terms:
            if t.lower() in low:
                # capture context
                ctx = []
                lines = (text or '').splitlines()
                for ln_idx, ln in enumerate(lines):
                    if t.lower() in ln.lower():
                        start = max(0, ln_idx - 1)
                        end = min(len(lines), ln_idx + 2)
                        snippet = '\n'.join(lines[start:end])
                        found[t].append({'page': i + 1, 'snippet': snippet})
    return found


def simple_summary(text, max_sent=6):
    # crude summary: take the first N non-empty lines as a proxy
    lines = [l.strip() for l in (text or '').splitlines() if l.strip()]
    return '\n\n'.join(lines[:max_sent])


def write_output(out_dir, pages, terms_index):
    os.makedirs(out_dir, exist_ok=True)
    # raw pages
    for i, p in enumerate(pages):
        fn = os.path.join(out_dir, f'raw-page-{i+1:03d}.md')
        with open(fn, 'w', encoding='utf-8') as f:
            f.write(f"# Page {i+1}\n\n")
            f.write(p or '')
    # combined summary
    combined = '\n\n'.join([p or '' for p in pages])
    summary = simple_summary(combined, max_sent=8)
    with open(os.path.join(out_dir, 'summary.md'), 'w', encoding='utf-8') as f:
        f.write('# Automated summary\n\n')
        f.write(summary + '\n')
    # key terms
    with open(os.path.join(out_dir, 'key_terms.md'), 'w', encoding='utf-8') as f:
        f.write('# Detected key terms\n\n')
        for term, hits in terms_index.items():
            f.write(f'## {term}\n')
            for h in hits:
                f.write(f"- page {h['page']}: `{h['snippet'].strip()[:200].replace('\n',' ')}...`\n")
    # touch a README note
    with open(os.path.join(out_dir, 'README_AUTOGEN.md'), 'w', encoding='utf-8') as f:
        f.write('This folder was populated by tools/ingest_goldbach_pdf.py. Review and edit generated files for accuracy.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--pdf', required=True)
    p.add_argument('--out', required=True)
    args = p.parse_args()
    path = args.pdf
    out_dir = args.out

    extractors = [extract_with_pdfplumber, extract_with_pypdf2, extract_with_pymupdf]
    pages = None
    for ex in extractors:
        try:
            pages = ex(path)
            if pages:
                print(f'Extracted {len(pages)} pages using {ex.__name__}')
                break
        except Exception as e:
            print(f'extractor {ex.__name__} failed: {e}')
    if not pages:
        print('No extractor produced text. Please install pdfplumber or PyMuPDF or check the PDF file.')
        return
    terms_index = detect_key_terms(pages)
    write_output(out_dir, pages, terms_index)
    print('Wrote outputs to', out_dir)


if __name__ == '__main__':
    main()
