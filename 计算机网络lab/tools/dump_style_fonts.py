# -*- coding: utf-8 -*-
"""dump_style_fonts.py - show rFonts / bold / size for key styles and sample runs."""
import sys
from docx import Document
from docx.oxml.ns import qn

doc = Document(sys.argv[1])
print("=== styles ===")
for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3", "Caption"]:
    st = doc.styles[name]
    rpr = st.element.find(qn("w:rPr"))
    fonts = rpr.find(qn("w:rFonts")) if rpr is not None else None
    info = {}
    if fonts is not None:
        for k in ("w:ascii", "w:hAnsi", "w:eastAsia", "w:cs"):
            info[k] = fonts.get(qn(k))
    b = rpr.find(qn("w:b")) if rpr is not None else None
    print(f"{name:12s} rFonts={info}  w:b={'yes' if b is not None else 'no'}")

print("\n=== first few heading paragraphs: style + run rFonts ===")
count = 0
for p in doc.paragraphs:
    if p.style.name.startswith("Heading") and p.text.strip():
        for r in p.runs:
            rpr = r._element.find(qn("w:rPr"))
            fonts = rpr.find(qn("w:rFonts")) if rpr is not None else None
            info = {}
            if fonts is not None:
                for k in ("w:ascii", "w:hAnsi", "w:eastAsia"):
                    info[k] = fonts.get(qn(k))
            print(f"  [{p.style.name}] run={r.text[:24]!r} rFonts={info} bold={r.font.bold}")
        count += 1
        if count >= 4:
            break
