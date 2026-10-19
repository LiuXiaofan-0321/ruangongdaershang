# -*- coding: utf-8 -*-
"""audit_docx.py - accurate structural audit of a DOCX body.

Counts real <w:tbl> elements (not tblPr/tblGrid), lists each table's first cell,
images, figure captions, and flags empty tables or captions without an image.

Usage: python audit_docx.py [--doc path]
"""
import argparse
import sys
import zipfile

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"

ap = argparse.ArgumentParser()
ap.add_argument("--doc", default=r"C:\University Courses\计算机网络lab\10244602411_刘小凡_IPv4.docx")
args = ap.parse_args()

d = Document(args.doc)
body = d.element.body

print(f"file: {args.doc}")
print(f"direct body paragraphs: {len([e for e in body.iterchildren() if e.tag == qn('w:p')])}")
print(f"direct body tables    : {len([e for e in body.iterchildren() if e.tag == qn('w:tbl')])}")

zi = zipfile.ZipFile(args.doc)
raw = zi.read("word/document.xml").decode("utf-8")
import re
print(f"XML <w:tbl>...</w:tbl> pairs : {len(re.findall(r'<w:tbl[ >]', raw)) - raw.count('<w:tblPr') - raw.count('<w:tblGrid')}")
print(f"media parts                  : {len([n for n in zi.namelist() if n.startswith('word/media/')])}")
print()

n_tbl = n_img = n_cap = 0
problems = []
pending_img = False
for el in body.iterchildren():
    tag = el.tag.split("}")[-1]
    if tag == "tbl":
        n_tbl += 1
        grid = el.find(qn("w:tblGrid")) is not None
        rows = len(el.findall(qn("w:tr")))
        tr = el.find(qn("w:tr"))
        first = ""
        if tr is not None:
            first = "".join(t.text or "" for t in tr.iter(qn("w:t")))[:34]
        flag = ""
        if not grid or not rows:
            flag = "   !! EMPTY"
            problems.append(f"table {n_tbl} empty")
        print(f"  table {n_tbl}: rows={rows:<2} grid={'Y' if grid else 'N'} "
              f"first={first!r}{flag}")
    elif tag == "p":
        para = Paragraph(el, d)
        if el.findall(f".//{BLIP}"):
            n_img += 1
            pending_img = True
        elif para.text.strip().startswith("图 "):
            n_cap += 1
            if not pending_img:
                problems.append(f"caption without image: {para.text.strip()[:36]}")
            pending_img = False
        elif para.text.strip():
            pending_img = False

print()
print(f"tables={n_tbl}  images={n_img}  figure captions={n_cap}")
print("problems:", problems if problems else "none")
