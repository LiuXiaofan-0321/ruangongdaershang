# -*- coding: utf-8 -*-
"""pdf_fonts.py - list fonts embedded in a PDF, flagging substituted CJK faces."""
import sys
import fitz

SUBSTITUTE_MARKERS = ("Gothic", "JhengHei", "Calibri", "Batang", "MingLiU",
                      "PMingLiU", "SimSun-Ext", "MSung", "DFKai")

for path in sys.argv[1:]:
    doc = fitz.open(path)
    fonts = {}
    for i, page in enumerate(doc, 1):
        for f in page.get_fonts():
            fonts.setdefault(f[3], set()).add(i)
    print(f"\n{path}  ({doc.page_count} pages)")
    bad = []
    for name in sorted(fonts):
        pages = sorted(fonts[name])
        flag = ""
        if any(m in name for m in SUBSTITUTE_MARKERS):
            flag = "   <-- SUBSTITUTED"
            bad.append(name)
        print(f"   {name:34s} pages={pages}{flag}")
    print(f"   substituted faces: {len(bad)}")
