"""
Create a PDF from the latest eth_15m markdown report and PNG chart.
Writes: analysis_reports/eth_15m_<ts>.pdf
"""
import os
import re
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "analysis_reports")
if not os.path.isdir(REPORTS_DIR):
    os.makedirs(REPORTS_DIR, exist_ok=True)

# Find latest eth_15m_*.md
files = [f for f in os.listdir(REPORTS_DIR) if f.startswith('eth_15m_') and f.endswith('.md')]
files = sorted(files, key=lambda x: os.path.getmtime(os.path.join(REPORTS_DIR, x)))
md_path = None
ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
if files:
    md_path = os.path.join(REPORTS_DIR, files[-1])
    m = re.match(r'eth_15m_(\d{8}_\d{6})\.md', files[-1])
    if m:
        ts = m.group(1)

# Corresponding PNG and JSON
png_path = os.path.join(REPORTS_DIR, f'eth_15m_{ts}.png')
json_path = os.path.join(REPORTS_DIR, f'eth_15m_{ts}.json')

pdf_path = os.path.join(REPORTS_DIR, f'eth_15m_{ts}.pdf')

if md_path is None:
    print('No markdown report found in', REPORTS_DIR)
    raise SystemExit(1)

with open(md_path, 'r', encoding='utf-8') as f:
    md = f.read()

# Very small markdown -> reportlab conversion
styles = getSampleStyleSheet()
heading = ParagraphStyle('Heading', parent=styles['Heading1'], spaceAfter=12)
subheading = ParagraphStyle('SubHeading', parent=styles['Heading2'], spaceAfter=8)
body = ParagraphStyle('Body', parent=styles['BodyText'], spaceAfter=6)

flow = []
# Cover
title = f"Ethereum 15m Goldbach Analysis"
flow.append(Paragraph(title, heading))
flow.append(Spacer(1, 0.05*inch))
flow.append(Paragraph(f"Generated: {ts} UTC", subheading))
flow.append(Spacer(1, 0.2*inch))
flow.append(Paragraph("Prepared by: FINANCIAL-TOOLS analysis pipeline", body))
flow.append(PageBreak())

# Insert PNG if exists
if os.path.exists(png_path):
    try:
        img = Image(png_path)
        # scale to page width with margin
        max_width = 7.5 * inch
        if img.drawWidth > max_width:
            ratio = max_width / img.drawWidth
            img.drawWidth = img.drawWidth * ratio
            img.drawHeight = img.drawHeight * ratio
        flow.append(img)
        flow.append(Spacer(1, 0.15*inch))
    except Exception as e:
        flow.append(Paragraph(f"(Could not include image: {e})", body))

# Simple parser
for line in md.splitlines():
    line = line.rstrip()
    if not line:
        flow.append(Spacer(1, 0.08*inch))
        continue
    if line.startswith('# '):
        flow.append(Paragraph(line[2:].strip(), subheading))
    elif line.startswith('## '):
        flow.append(Paragraph(line[3:].strip(), styles['Heading3']))
    elif line.startswith('- ') or line.startswith('* '):
        flow.append(Paragraph('• ' + line[2:].strip(), body))
    else:
        # escape < and > for reportlab's paragraph
        safe = line.replace('<', '&lt;').replace('>', '&gt;')
        flow.append(Paragraph(safe, body))

# Footer with JSON path
flow.append(Spacer(1, 0.2*inch))
if os.path.exists(json_path):
    flow.append(PageBreak())
    flow.append(Paragraph('Appendix: Full audit JSON', subheading))
    with open(json_path, 'r', encoding='utf-8') as jf:
        jtext = jf.read()
    # include as preformatted monospace block
    flow.append(Spacer(1, 0.1*inch))
    flow.append(Preformatted(jtext, style=ParagraphStyle('Mono', fontName='Courier', fontSize=8)))

# Build PDF
try:
    doc = SimpleDocTemplate(pdf_path, pagesize=letter, rightMargin=0.5*inch, leftMargin=0.5*inch, topMargin=0.5*inch, bottomMargin=0.5*inch)
    doc.build(flow)
    print('PDF written:', pdf_path)
except Exception as e:
    print('Failed to write PDF:', e)
    raise
