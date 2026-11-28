# -*- coding: utf-8 -*-
"""render_pdf.py - convert docx to PDF via LibreOffice and render PNG pages via fitz."""
import subprocess
import sys
from pathlib import Path
import fitz

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

SOFFICE = r"C:\Users\18963\AppData\Local\LibreOffice-26.8.0\program\soffice.exe"
ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab5_work"
DOC = ROOT / "10244602411_刘小凡_UDP.docx"
QA = WORK / "qa"
PAGES = QA / "pages"
PAGES.mkdir(parents=True, exist_ok=True)
for old in PAGES.glob("*.png"):
    old.unlink()

# LibreOffice puts output PDF in --outdir with stem.pdf
subprocess.run([
    SOFFICE, "--headless", "--convert-to", "pdf",
    "--outdir", str(QA), str(DOC)
], check=True)

pdf_raw = QA / (DOC.stem + ".pdf")
pdf_final = WORK / "Lab5报告_渲染预览.pdf"
if pdf_final.exists():
    pdf_final.unlink()
pdf_raw.replace(pdf_final)

doc = fitz.open(str(pdf_final))
print(f"Rendered {doc.page_count} pages -> {pdf_final}")
for i, page in enumerate(doc, 1):
    pix = page.get_pixmap(dpi=110)
    out = PAGES / f"page-{i:02d}.png"
    pix.save(str(out))
print("Saved PNGs to", PAGES)
