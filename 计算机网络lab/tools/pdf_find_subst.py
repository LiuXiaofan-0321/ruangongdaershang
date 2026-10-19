# -*- coding: utf-8 -*-
"""pdf_find_subst.py - show which text runs use a substituted font in a PDF."""
import sys
import fitz

MARKERS = ("Gothic", "JhengHei", "Calibri", "Batang", "MingLiU", "PMingLiU",
           "MSung", "DFKai", "Arial", "Helvetica", "Liberation")

path = sys.argv[1]
targets = sys.argv[2:] or MARKERS
doc = fitz.open(path)
found = 0
for pno, page in enumerate(doc, 1):
    for blk in page.get_text("dict")["blocks"]:
        for line in blk.get("lines", []):
            for span in line["spans"]:
                if any(t in span["font"] for t in targets):
                    found += 1
                    print(f"p{pno:2d} font={span['font']:28s} size={span['size']:.1f} "
                          f"text={span['text']!r}")
print(f"\ntotal substituted spans: {found}")
