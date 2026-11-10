# -*- coding: utf-8 -*-
"""check_template.py - confirm the Lab4 template copy matches the Lab3 contract."""
import hashlib
import sys

from docx import Document
from docx.text.paragraph import Paragraph

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"C:\University Courses\计算机网络lab\_lab4_work\template.docx"
EXPECT = "100d6b4eb208559ef3a88bc0ea838a5e0945f056676604a9bd4beaf6c73ced7b"

h = hashlib.sha256(open(P, "rb").read()).hexdigest()
print("sha256 :", h)
print("match  :", h == EXPECT)
print()

d = Document(P)
for i, el in enumerate(d.element.body.iterchildren()):
    tag = el.tag.split("}")[-1]
    if tag != "p":
        print(f"  [{i:2d}] <{tag}>")
        continue
    para = Paragraph(el, d)
    t = para.text.strip()
    red = any(r.font.color is not None and r.font.color.type is not None
              and str(r.font.color.rgb) == "FF0000" for r in para.runs)
    mark = "RED" if red else "   "
    print(f"  [{i:2d}] {mark} {t[:48]!r}")
