# -*- coding: utf-8 -*-
"""check_lab5.py - final compliance, typography, pairing, and coverage gate for Lab5."""
import hashlib
import json
import sys
import zipfile
from pathlib import Path

from docx import Document
from docx.oxml.ns import qn
from docx.text.paragraph import Paragraph

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab5_work"
DOC = ROOT / "10244602411_刘小凡_UDP.docx"
TPL = WORK / "template.docx"
F = json.loads((WORK / "facts.json").read_text(encoding="utf-8"))

TPL_SHA = "100d6b4eb208559ef3a88bc0ea838a5e0945f056676604a9bd4beaf6c73ced7b"
got_sha = hashlib.sha256(TPL.read_bytes()).hexdigest()
print("=== template sha256 ===")
print("  match:", got_sha == TPL_SHA, got_sha)

d = Document(str(DOC))
t = Document(str(TPL))
ds, ts = d.sections[0], t.sections[0]

print("=== geometry ===")
keys = ("page_width", "page_height", "top_margin", "bottom_margin", "left_margin", "right_margin")
geo_ok = all(abs(getattr(ds, k).cm - getattr(ts, k).cm) < 0.001 for k in keys)
print("  identical:", geo_ok)
for k in keys:
    print(f"    {k:14s} report={getattr(ds,k).cm:.4f} template={getattr(ts,k).cm:.4f}")

print("=== header / footer ===")
print("  header:", repr(ds.header.paragraphs[0].text))
print("  footer:", repr(ds.footer.paragraphs[0].text))
print("  footer has PAGE field:", "PAGE" in ds.footer.paragraphs[0]._p.xml and "NUMPAGES" in ds.footer.paragraphs[0]._p.xml)

print("=== sections in order ===")
want = ["一、实验目的", "二、实验内容与实验步骤", "三、实验环境",
        "四、实验过程与分析", "五、必做题目与解答", "六、实验结果总结", "七、附录"]
kids = list(d.element.body.iterchildren())
heads = []
head_idx = []
for idx, el in enumerate(kids):
    if el.tag == qn("w:p"):
        s = Paragraph(el, d).text.strip()
        if s in want:
            heads.append(s)
            head_idx.append((s, idx))
print("  found :", heads)
print("  order ok:", heads == want)
# Verify no empty section (each heading is followed closely by non-heading content)
non_empty_sections = True
for i, (s, idx) in enumerate(head_idx):
    nxt = head_idx[i + 1][1] if i + 1 < len(head_idx) else len(kids)
    if nxt - idx <= 1:
        print(f"  !! EMPTY SECTION: {s}")
        non_empty_sections = False
print("  all sections populated:", non_empty_sections)

print("=== metadata ===")
tb = d.tables[0]
for ri in range(3):
    print("  ", " | ".join(tb.rows[ri].cells[c].text.strip() for c in range(3)))

print("=== package preservation ===")
zt = set(zipfile.ZipFile(TPL).namelist())
zn = set(zipfile.ZipFile(DOC).namelist())
print("  template parts lost:", sorted(zt - zn) or "none")
tpl_media = [n for n in zt if n.startswith("word/media/")]
doc_media = [n for n in zn if n.startswith("word/media/")]
print(f"  template media={len(tpl_media)} ({tpl_media}), report media={len(doc_media)}")

print("=== tables & figures ===")
bad_tbl = sum(1 for el in kids if el.tag == qn("w:tbl") and (el.find(qn("w:tblGrid")) is None or not el.findall(qn("w:tr"))))
print(f"  tables={len(d.tables)} empty_shells={bad_tbl}")

BLIP = "{http://schemas.openxmlformats.org/drawingml/2006/main}blip"
VML = "{urn:schemas-microsoft-com:vml}imagedata"
img_paras = []
cap_paras = []
for i, el in enumerate(kids):
    if el.tag == qn("w:p"):
        has_img = bool(el.findall(".//" + BLIP) or el.findall(".//" + VML))
        txt_p = Paragraph(el, d).text.strip()
        if has_img:
            img_paras.append(i)
            nxt_txt = Paragraph(kids[i + 1], d).text.strip() if i + 1 < len(kids) and kids[i + 1].tag == qn("w:p") else ""
            if not nxt_txt.startswith("图 "):
                print(f"  !! Image at body[{i}] not followed by caption: {nxt_txt[:40]}")
        if txt_p.startswith("图 "):
            cap_paras.append(txt_p[:24])
print(f"  images={len(img_paras)} captions={len(cap_paras)} paired={len(img_paras)==len(cap_paras)}")

print("=== coverage of Lab5 manual & facts ===")
txt = "\n".join(p.text for p in d.paragraphs)
for tb_ in d.tables:
    for row in tb_.rows:
        for c in row.cells:
            txt += "\n" + c.text

need = {
    "Turn-in ① 结构图": "必做题目一" in txt and "图 14" in txt,
    "Turn-in ① 三问": "问题 1：" in txt and "问题 2：" in txt and "问题 3：" in txt,
    "Turn-in ② 三问": "必做题目二" in txt and "图 15" in txt,
    "Length = 首部 + 载荷": "UDP 首部" in txt and "有效载荷" in txt,
    "Checksum 16 位": "16 位" in txt,
    "UDP 首部 8 字节": "8 字节" in txt,
    "IP Protocol 17": "17" in txt and "0x11" in txt,
    "多播 224.0.0.251": F["addressing"]["multicast_dst_ip"] in txt,
    "双非本机偏差说明": "0 帧" in txt and "混杂模式" in txt,
    "零校验和 171 帧说明": str(F["checksum"]["zero_total"]) in txt and "0x0000" in txt,
    "中位数 56 B": f"{F['udp_length_stats']['median']} B" in txt,
    "题目原文标注 >= 2": txt.count("题目原文") >= 2,
    "无 AI 字样": ("AI 制作" not in txt) and ("由 AI 生成" not in txt) and ("AI 生成" not in txt),
}
for k, v in need.items():
    print(f"  {k:24s} {v}")
print("  all covered:", all(need.values()))

reds = []
for p in d.paragraphs:
    for r in p.runs:
        if r.font.color and r.font.color.type is not None and str(r.font.color.rgb) == "FF0000" and r.text.strip():
            reds.append(r.text[:40])
print("  visible red runs:", reds or "none")

if not (got_sha == TPL_SHA and geo_ok and heads == want and non_empty_sections and bad_tbl == 0 and len(img_paras) == len(cap_paras) and all(need.values()) and not reds):
    raise SystemExit(1)
print("CHECK_LAB5_OK")
