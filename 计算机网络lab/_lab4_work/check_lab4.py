# -*- coding: utf-8 -*-
"""check_lab4.py - final compliance and coverage gate for the Lab4 report."""
import sys
import zipfile

from docx import Document
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = r"C:\University Courses\计算机网络lab"
DOC = ROOT + r"\10244602411_刘小凡_Lab4_ARP.docx"
TPL = ROOT + r"\_lab4_work\template.docx"

d = Document(DOC)
t = Document(TPL)
ds, ts = d.sections[0], t.sections[0]

print("=== geometry ===")
keys = ("page_width", "page_height", "top_margin", "bottom_margin",
        "left_margin", "right_margin")
print("  identical:", all(abs(getattr(ds, k).cm - getattr(ts, k).cm) < 0.001 for k in keys))
for k in keys:
    print(f"    {k:14s} report={getattr(ds,k).cm:.4f} template={getattr(ts,k).cm:.4f}")

print("=== header / footer ===")
print("  header:", repr(ds.header.paragraphs[0].text))
print("  footer:", repr(ds.footer.paragraphs[0].text))
print("  footer has PAGE field:", "PAGE" in ds.footer.paragraphs[0]._p.xml)

print("=== sections in order ===")
want = ["一、实验目的", "二、实验内容与实验步骤", "三、实验环境",
        "四、实验过程与分析", "五、必做题目与解答", "六、实验结果总结", "七、附录"]
kids = list(d.element.body.iterchildren())
heads = []
for el in kids:
    if el.tag == qn("w:p"):
        from docx.text.paragraph import Paragraph
        s = Paragraph(el, d).text.strip()
        if s in want:
            heads.append(s)
print("  found :", heads)
print("  order ok:", heads == want)

print("=== metadata ===")
tb = d.tables[0]
for ri in range(3):
    print("  ", " | ".join(tb.rows[ri].cells[c].text.strip() for c in range(3)))

print("=== package preservation ===")
zt = set(zipfile.ZipFile(TPL).namelist())
zn = set(zipfile.ZipFile(DOC).namelist())
print("  template parts lost:", sorted(zt - zn) or "none")
print("  media:", len([n for n in zn if n.startswith("word/media/")]))

print("=== coverage of the manual's Turn-in items ===")
txt = "\n".join(p.text for p in d.paragraphs)
for tb_ in d.tables:
    for row in tb_.rows:
        for c in row.cells:
            txt += "\n" + c.text
need = {
    "Turn-in ① 交换示意图": "必做题目一" in txt and "图 11" in txt,
    "Turn-in ② 五问": all(f"问题 {i}：" in txt for i in range(1, 6)),
    "opcode 1/2": ("请求 = 1，应答 = 2" in txt) or ("操作码为 1" in txt and "为 2" in txt),
    "首部 28 B": "28 字节" in txt,
    "未知目标 MAC 全零": "00:00:00:00:00:00" in txt,
    "EtherType 0x0806": "0x0806" in txt,
    "应答单播": "单播" in txt,
    "题目原文标注": txt.count("题目原文") >= 2,
}
for k, v in need.items():
    print(f"  {k:24s} {v}")
print("  all covered:", all(need.values()))

print("=== red placeholder text ===")
reds = []
for p in d.paragraphs:
    for r in p.runs:
        if (r.font.color and r.font.color.type is not None
                and str(r.font.color.rgb) == "FF0000" and r.text.strip()):
            reds.append(r.text[:40])
print("  visible red runs:", reds or "none")
