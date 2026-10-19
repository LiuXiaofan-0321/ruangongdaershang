# -*- coding: utf-8 -*-
r"""build_lab2_v2.py - Lab2 Ethernet 实验报告（实测数据版，LibreOffice 优化字体）

All values in this report come from the captures in _lab2_工作\captures:
  Lab2_刘小凡_单播.pcapng    8 帧 ICMP（ping -4 -n 4 www.baidu.com）
  Lab2_刘小凡_广播组播.pcapng 110 帧 ether multicast 背景流量（60 s）
  Lab2_LLC_构造样例.pcapng   构造的 IEEE 802.3 + LLC 样例（本机迹线中无 LLC）
"""
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab2_工作"
EV = WORK / "evidence"
CAP = WORK / "captures"
OUT = ROOT / "10244602411_刘小凡_Lab2_Ethernet_实测版_v2.docx"

# 字体方案（针对 LibreOffice 渲染优化）
#   正文：西文 Times New Roman + 中文 等线（DengXian）
#   Bug 修复记录：LibreOffice 在“样式级”指定 等线/宋体 + 加粗时，会因为
#   这些字体没有真正的粗体字形而在局部替换成 MS-Gothic / 细明体，
#   造成同一行字粗细不一（这是用户看到的问题）。因此：
#     · 标题与强调文字直接写在 run 上（不经样式继承）
#     · 统一改用有真粗体的微软雅黑（Microsoft YaHei）
LATIN = "Times New Roman"
CJK = "Microsoft YaHei"
HEI = "Microsoft YaHei"
SONG = "Microsoft YaHei"
MONO = "Consolas"

# --------------------------------------------------------------------------
# 实测数据（全部来自上面的 pcapng，可用 tshark -T fields 复核）
# --------------------------------------------------------------------------
C = {
    "host_mac": "14:ac:60:56:df:85",
    "host_mac_oui": "CloudNetwork_56:df:85",
    "host_ip": "192.168.31.135",
    "gw_mac": "28:d1:27:df:d4:95",
    "gw_mac_oui": "XiaomiMobile_df:d4:95",
    "gw_ip": "192.168.31.1",
    "remote_ip": "180.101.51.73",
    "remote_name": "www.baidu.com (www.a.shifen.com)",
    "iface": "MediaTek Wi-Fi 6E MT7922 (RZ616) 160MHz Wireless LAN Card",
    "iface_alias": "WLAN",
    "frame_len": 74,
    "ip_total_len": 60,
    "ip_hdr_len": 20,
    "icmp_data_len": 32,
    "icmp_total": 40,
    "eth_hdr": 14,
    "ttl_req": 128,
    "ttl_rep": 52,
    "icmp_id": 1,
    "seqs": "6, 7, 8, 9",
    "n_req": 4,
    "n_rep": 4,
    "frames": 110,
    "broadcast": 11,
    "mcast": 99,
    "duration": 60,
}
# frame 1 原始字节（Wireshark 导出）
FRAME1_HEX = [
    "0000  28 d1 27 df d4 95 14 ac 60 56 df 85 08 00 45 00",
    "0010  00 3c 21 e6 00 00 80 01 00 00 c0 a8 1f 87 b4 65",
    "0020  33 49 08 00 4d 55 00 01 00 06 61 62 63 64 65 66",
    "0030  67 68 69 6a 6b 6c 6d 6e 6f 70 71 72 73 74 75 76",
    "0040  77 61 62 63 64 65 66 67 68 69",
]
ARP_HEX = [
    "0000  ff ff ff ff ff ff 14 ac 60 56 df 85 08 06 00 01",
    "0010  08 00 06 04 00 01 14 ac 60 56 df 85 c0 a8 1f 87",
    "0020  00 00 00 00 00 00 c0 a8 1f 01",
]
LLC_HEX = [
    "0000  aa bb cc dd ee ff 11 22 33 44 55 66 00 0b 42 42",
    "0010  03 4c 4c 43 2d 44 45 4d 4f",
]


# --------------------------------------------------------------------------
# 字体与排版工具
# --------------------------------------------------------------------------
def cn(run, size=10.5, bold=False, face=None, color="000000", mono=False):
    """统一字体入口。

    加粗时把西文与中文都切到等线真粗体（DengXian Bold），避免对宋体做
    合成加粗（fake bold）而产生的粗细不一致。face 仅在明确指定时使用
    （例如等宽块传入 Consolas 作为中文回退）。
    """
    if mono:
        face = face if face else MONO
    else:
        face = face if face else (CJK if bold else CJK)
    latin_face = face if (bold or mono) else LATIN
    run.font.size = Pt(size)
    run.font.bold = bool(bold)
    run.font.color.rgb = RGBColor.from_string(color)
    run.font.name = latin_face
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), face)


def new_doc(title, subtitle):
    d = Document()
    s = d.sections[0]
    s.page_width, s.page_height = Cm(21), Cm(29.7)
    s.top_margin, s.bottom_margin = Cm(2.0), Cm(1.9)
    s.left_margin, s.right_margin = Cm(2.3), Cm(2.3)
    s.header_distance, s.footer_distance = Cm(0.8), Cm(0.85)

    for name in ["Normal", "Title", "Subtitle", "Heading 1", "Heading 2", "Heading 3",
                 "Caption", "List Paragraph"]:
        st = d.styles[name]
        st.font.name = LATIN
        st._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), CJK)
        st.font.color.rgb = RGBColor(0, 0, 0)

    for nm, sz in [("Heading 1", 14), ("Heading 2", 12), ("Heading 3", 11)]:
        st = d.styles[nm]
        st.font.size = Pt(sz)
        st.font.bold = True
        st.font.name = CJK
        st._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), CJK)
        st.paragraph_format.first_line_indent = Cm(0)
        st.paragraph_format.space_before = Pt(9)
        st.paragraph_format.space_after = Pt(5)
        st.paragraph_format.keep_with_next = True
        st.paragraph_format.line_spacing = 1.25

    normal = d.styles["Normal"]
    normal.font.size = Pt(10.5)
    normal.paragraph_format.line_spacing = 1.3
    normal.paragraph_format.space_after = Pt(4)

    d.styles["Caption"].font.size = Pt(9)
    d.styles["Caption"].font.name = LATIN
    d.styles["Caption"]._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), CJK)
    d.styles["Caption"].paragraph_format.first_line_indent = Cm(0)
    d.styles["Caption"].paragraph_format.space_after = Pt(8)
    d.styles["Title"].font.size = Pt(17)
    d.styles["Title"].font.bold = True
    d.styles["Title"].font.name = CJK
    d.styles["Title"]._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), CJK)
    d.styles["Subtitle"].font.size = Pt(11.5)
    d.styles["Subtitle"].font.bold = True
    d.styles["Subtitle"].font.name = CJK
    d.styles["Subtitle"]._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), CJK)

    for el in d.styles._element.xpath(".//w:pBdr"):
        el.getparent().remove(el)

    p = d.add_paragraph(style="Title")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.space_after = Pt(6)
    cn(p.add_run(title), 17, True, HEI)
    p = d.add_paragraph(style="Subtitle")
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_after = Pt(8)
    cn(p.add_run(subtitle), 11.5, True, HEI)

    hp = s.header.paragraphs[0]
    hp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cn(hp.add_run("华东师范大学软件学院  计算机网络实验报告"), 8.5)

    fp = s.footer.paragraphs[0]
    fp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    cn(fp.add_run("第 "), 9)
    fld = OxmlElement("w:fldSimple")
    fld.set(qn("w:instr"), "PAGE")
    r = OxmlElement("w:r")
    t = OxmlElement("w:t")
    t.text = "1"
    r.append(t)
    fld.append(r)
    fp._p.append(fld)
    cn(fp.add_run(" 页，共 "), 9)
    fld2 = OxmlElement("w:fldSimple")
    fld2.set(qn("w:instr"), "NUMPAGES")
    r2 = OxmlElement("w:r")
    t2 = OxmlElement("w:t")
    t2.text = "1"
    r2.append(t2)
    fld2.append(r2)
    fp._p.append(fld2)
    cn(fp.add_run(" 页"), 9)

    d.core_properties.author = "刘小凡"
    d.core_properties.title = f"{title} {subtitle}"
    return d


def para(d, text="", bold=False, indent=True, size=10.5, color="000000", align=None):
    p = d.add_paragraph()
    if not indent:
        p.paragraph_format.first_line_indent = Cm(0)
    if align is not None:
        p.alignment = align
    if text:
        cn(p.add_run(text), size, bold, color=color)
    return p


def head(d, text, level=1):
    """标题。字体显式写在 run 上：LibreOffice 对样式级 East-Asian 字体会做
    字形回退替换，直接格式化可避免标题里出现 MS-Gothic / 细明体混排。
    标题不加粗：中文报告惯例是「正文宋体/雅黑、标题黑体」，靠字号与字体
    本身区分层级，这样整行笔画粗细完全一致。"""
    size = {1: 14, 2: 12.5, 3: 11.5}.get(level, 11)
    p = d.add_paragraph(style=f"Heading {level}")
    run = p.add_run(text)
    cn(run, size, False, face=CJK)
    run.font.bold = False
    return p


def mono_lines(d, lines, size=9.5):
    """等宽字节/命令行文本块。"""
    for line in lines:
        p = d.add_paragraph()
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.space_after = Pt(1)
        p.paragraph_format.line_spacing = 1.05
        p.paragraph_format.left_indent = Cm(0.4)
        cn(p.add_run(line), size, face="Consolas", mono=True)
    g = d.add_paragraph()
    g.paragraph_format.space_after = Pt(3)
    g.paragraph_format.line_spacing = Pt(3)
    cn(g.add_run(""), 2)


def cmd(d, text):
    p = d.add_paragraph()
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.left_indent = Cm(0.4)
    p.paragraph_format.space_after = Pt(4)
    cn(p.add_run(text), 9.5, face="Consolas", mono=True)


def table(d, heads, rows, widths, header=True, size=9.5):
    t = d.add_table(rows=1, cols=len(heads))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, w in enumerate(widths):
        t.columns[i].width = Cm(w)
    for i, txt in enumerate(heads):
        t.rows[0].cells[i].text = str(txt)
    if not header:
        t._tbl.remove(t.rows[0]._tr)
    for row in rows:
        cells = t.add_row().cells
        for i, txt in enumerate(row):
            cells[i].text = str(txt)

    borders = OxmlElement("w:tblBorders")
    for edge in ["top", "left", "bottom", "right", "insideH", "insideV"]:
        el = OxmlElement("w:" + edge)
        el.set(qn("w:val"), "single")
        el.set(qn("w:sz"), "4")
        el.set(qn("w:color"), "9DB2C6")
        borders.append(el)
    t._tbl.tblPr.append(borders)

    for ri, row in enumerate(t.rows):
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
        if ri == 0 and header:
            trpr.append(OxmlElement("w:tblHeader"))
        for ci, cell in enumerate(row.cells):
            cell.width = Cm(widths[ci])
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr = cell._tc.get_or_add_tcPr()
            mar = OxmlElement("w:tcMar")
            for edge in ["top", "bottom", "left", "right"]:
                e = OxmlElement("w:" + edge)
                e.set(qn("w:w"), "80")
                e.set(qn("w:type"), "dxa")
                mar.append(e)
            tcpr.append(mar)
            if ri == 0 and header:
                shd = OxmlElement("w:shd")
                shd.set(qn("w:fill"), "E8EEF4")
                tcpr.append(shd)
            for pp in cell.paragraphs:
                pp.paragraph_format.first_line_indent = Cm(0)
                pp.paragraph_format.space_after = Pt(1)
                pp.paragraph_format.line_spacing = 1.1
                for rr in pp.runs:
                    cn(rr, size, ri == 0 and header)
    g = d.add_paragraph()
    g.paragraph_format.space_after = Pt(3)
    g.paragraph_format.line_spacing = Pt(3)
    cn(g.add_run(""), 2)
    return t


def figure(d, path, caption, width=16.0):
    p = d.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.keep_with_next = True
    r = p.add_run()
    r.add_picture(str(path), width=Cm(width))
    cp = d.add_paragraph(caption, style="Caption")
    cp.alignment = WD_ALIGN_PARAGRAPH.CENTER
    return cp


# --------------------------------------------------------------------------
# 图 1：以太网帧字节结构示意图（按字节数等比绘制）
# --------------------------------------------------------------------------
def fig_frame_structure():
    SCALE = 34  # px / byte
    W, H = 2100, 780
    im = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(im)
    fbig = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 34)
    fmid = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 25)
    fsm = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 21)

    dr.text((40, 24), "Ethernet II 抓包记录的字节布局（实测帧 1，共 74 B）", font=fbig, fill="#111111")
    dr.text((40, 74), "偏移 0 为抓包记录首字节；帧内各字段宽度按字节数等比绘制", font=fsm, fill="#555555")

    top, hgt = 150, 150
    # (起始字节, 字节数, 标签, 底色)
    segs = [
        (0, 6, "目的 MAC\n6 B\n偏移 0–5", "#DCE6F1"),
        (6, 6, "源 MAC\n6 B\n偏移 6–11", "#DCE6F1"),
        (12, 2, "Type\n2 B\n12–13\n0x0800", "#DCE6F1"),
        (14, 20, "IPv4 首部\n20 B\n偏移 14–33", "#E3EFDA"),
        (34, 8, "ICMP 首部\n8 B\n34–41", "#FBEEDA"),
        (42, 32, "ICMP 数据（32 B）\n偏移 42–73", "#FBEEDA"),
    ]
    x0 = 60
    for start, n, label, col in segs:
        xa, xb = x0 + start * SCALE, x0 + (start + n) * SCALE
        dr.rectangle((xa, top, xb, top + hgt), fill=col, outline="#5A6B7C", width=2)
        lines = label.split("\n")
        th = sum(dr.textbbox((0, 0), l, font=fmid)[3] for l in lines) + 8 * (len(lines) - 1)
        y = top + (hgt - th) / 2
        for l in lines:
            bb = dr.textbbox((0, 0), l, font=fmid)
            dr.text(((xa + xb - (bb[2] - bb[0])) / 2, y - bb[1]), l, font=fmid, fill="#12212F")
            y += (bb[3] - bb[1]) + 8

    # FCS 虚线框
    xa = x0 + 74 * SCALE
    dr.rectangle((xa + 14, top, xa + 14 + 4 * SCALE, top + hgt), outline="#5A6B7C",
                 width=2, fill="#F2F2F2")
    for xx in range(int(xa + 14), int(xa + 14 + 4 * SCALE), 12):
        dr.line((xx, top, min(xx + 6, xa + 14 + 4 * SCALE), top + hgt), fill="#C9C9C9")
    bb = dr.textbbox((0, 0), "FCS", font=fsm)
    dr.text((xa + 14 + (4 * SCALE - (bb[2] - bb[0])) / 2, top + hgt + 8), "FCS 4 B",
            font=fsm, fill="#555555")
    dr.text((xa + 14, top - 34), "抓包不显示", font=fsm, fill="#8A5A00")

    # 分组标注
    def span(b0, b1, y, text, col="#233746"):
        xa, xb = x0 + b0 * SCALE, x0 + b1 * SCALE
        dr.line((xa, y, xb, y), fill=col, width=3)
        dr.line((xa, y - 12, xa, y + 12), fill=col, width=3)
        dr.line((xb, y - 12, xb, y + 12), fill=col, width=3)
        bb = dr.textbbox((0, 0), text, font=fmid)
        dr.text(((xa + xb - (bb[2] - bb[0])) / 2, y + 14), text, font=fmid, fill=col)

    span(0, 14, top + hgt + 60, "以太网首部 = 14 B")
    span(14, 74, top + hgt + 60, "以太网有效载荷 = 60 B（IPv4 20 + ICMP 8 + 数据 32）")
    span(0, 74, top + hgt + 150, "抓包记录 Frame Length = 74 B（不含 FCS、前导码与 SFD）")
    span(14, 34, top + hgt + 235, "IP 数据报 Total Length = 60 B")
    dr.text((40, H - 46), "实线框为 Wireshark 实际显示的字段；FCS 用虚线框表示其存在但抓包中通常不可见。",
            font=fsm, fill="#666666")
    out = EV / "fig4_frame_structure.png"
    im.save(out)
    return out


# --------------------------------------------------------------------------
# 图 2：地址作用范围拓扑图（填入实测地址）
# --------------------------------------------------------------------------
def fig_address_scope():
    W, H = 2100, 720
    im = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(im)
    fbig = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 34)
    fmid = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 24)
    fsm = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 21)

    dr.text((40, 24), "以太网地址（MAC）与 IP 地址的作用范围（实测地址）", font=fbig, fill="#111111")

    def box(x0, y0, x1, y1, lines, col="#F4F7FA"):
        dr.rectangle((x0, y0, x1, y1), fill=col, outline="#657383", width=2)
        th = sum(dr.textbbox((0, 0), l, font=fmid)[3] for l in lines) + 10 * (len(lines) - 1)
        y = y0 + (y1 - y0 - th) / 2
        for l in lines:
            bb = dr.textbbox((0, 0), l, font=fmid)
            dr.text(((x0 + x1 - (bb[2] - bb[0])) / 2, y - bb[1]), l, font=fmid, fill="#12212F")
            y += (bb[3] - bb[1]) + 10

    box(50, 200, 560, 430, [
        "本机（WLAN 接口）",
        f"IP  {C['host_ip']}",
        f"MAC {C['host_mac']}",
    ], "#E8F0E4")
    box(770, 200, 1280, 430, [
        "默认网关 / 路由器",
        f"IP  {C['gw_ip']}",
        f"MAC {C['gw_mac']}",
    ], "#E6EDF6")
    box(1490, 200, 2050, 430, [
        "远程 Web 服务器",
        f"IP  {C['remote_ip']}",
        "MAC  本链路不可知",
    ], "#F6EFE6")

    def arrow(x0, x1, y, text, col="#2E4A63"):
        dr.line((x0, y, x1, y), fill=col, width=5)
        dr.polygon([(x1, y), (x1 - 18, y - 10), (x1 - 18, y + 10)], fill=col)
        bb = dr.textbbox((0, 0), text, font=fmid)
        dr.text(((x0 + x1 - (bb[2] - bb[0])) / 2, y - 48), text, font=fmid, fill=col)

    arrow(570, 760, 315, "本地链路（以太网 / 802.11）")
    arrow(1290, 1480, 315, "Internet")

    dr.text((50, 470), f"本机发出的请求帧：Ethernet  {C['host_mac']} → {C['gw_mac']}"
                       f"      IPv4  {C['host_ip']} → {C['remote_ip']}", font=fmid, fill="#12212F")
    dr.text((50, 520), f"网关返回的回复帧：Ethernet  {C['gw_mac']} → {C['host_mac']}"
                       f"      IPv4  {C['remote_ip']} → {C['host_ip']}", font=fmid, fill="#12212F")
    dr.text((50, 585), "MAC 地址只在当前链路内有意义，目的 MAC 指向下一跳（网关）而不是远程服务器；",
            font=fsm, fill="#555555")
    dr.text((50, 620), "IP 地址跨网段标识通信的两端，因此 IPv4 的目的地址才是远程服务器的地址。",
            font=fsm, fill="#555555")
    out = EV / "fig5_address_scope.png"
    im.save(out)
    return out


def fig_ig_bit():
    """I/G 位与 U/L 位在首字节中的位置图（实测地址标注）。"""
    W, H = 2100, 800
    im = Image.new("RGB", (W, H), "white")
    dr = ImageDraw.Draw(im)
    fbig = ImageFont.truetype(r"C:\Windows\Fonts\msyhbd.ttc", 32)
    fmid = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 24)
    fsm = ImageFont.truetype(r"C:\Windows\Fonts\msyh.ttc", 21)

    dr.text((40, 22), "目的 MAC 第一个字节中的 I/G 位（bit 0）与 U/L 位（bit 1）", font=fbig, fill="#111111")
    dr.text((40, 72), "以太网每个字节先发送最低位（LSB first），因此手册所说的「线上先发送的第一位」就是 bit 0",
            font=fsm, fill="#555555")

    left, top, cw, ch = 120, 150, 130, 110
    bits = ["b7", "b6", "b5", "b4", "b3", "b2", "b1", "b0"]
    for i, b in enumerate(bits):
        x = left + i * cw
        col = "#FBEEDA" if b in ("b1", "b0") else "#F2F4F7"
        dr.rectangle((x, top, x + cw, top + ch), fill=col, outline="#5A6B7C", width=2)
        bb = dr.textbbox((0, 0), b, font=fmid)
        dr.text((x + (cw - (bb[2] - bb[0])) / 2, top + (ch - (bb[3] - bb[1])) / 2 - bb[1]),
                b, font=fmid, fill="#12212F")
    dr.text((left - 112, top + 40), "第一个字节", font=fmid, fill="#12212F")

    def note(idx, text, col="#8A4B00"):
        x = left + idx * cw
        dr.line((x + cw / 2, top + ch, x + cw / 2, top + ch + 30), fill=col, width=2)
        for i, line in enumerate(text.split("\n")):
            bb = dr.textbbox((0, 0), line, font=fsm)
            dr.text((x + cw / 2 - (bb[2] - bb[0]) / 2, top + ch + 36 + i * 26),
                    line, font=fsm, fill=col)

    note(7, "b1 = U/L\n0 全局唯一 / 1 本地管理")
    note(6, "b0 = I/G\n0 单播 / 1 组播·广播", "#1F5C33")

    rows = [
        ("ff:ff:ff:ff:ff:ff", "FF", "1111 1111", "1", "1", "广播"),
        ("01:00:5e:00:00:fb", "01", "0000 0001", "1", "0", "IPv4 组播（mDNS）"),
        ("33:33:00:00:00:fb", "33", "0011 0011", "1", "1", "IPv6 组播（mDNS）"),
        ("28:d1:27:df:d4:95", "28", "0010 1000", "0", "0", "单播（网关）"),
        ("14:ac:60:56:df:85", "AC", "1010 1100", "0", "0", "单播（本机）"),
    ]
    y = 495
    dr.text((left, y - 38), "本次实测抓到的目的地址：", font=fmid, fill="#12212F")
    heads = ["目的 MAC", "首字节", "二进制", "I/G", "U/L", "类型"]
    xs = [left, left + 470, left + 620, left + 860, left + 960, left + 1080]
    for x, h in zip(xs, heads):
        dr.text((x, y), h, font=fsm, fill="#555555")
    for i, r in enumerate(rows):
        yy = y + 36 + i * 34
        for x, v in zip(xs, r):
            dr.text((x, yy), v, font=fsm, fill="#12212F")
    out = EV / "fig6_ig_bit.png"
    im.save(out)
    return out


# --------------------------------------------------------------------------
# 报告正文
# --------------------------------------------------------------------------
def build():
    EV.mkdir(parents=True, exist_ok=True)
    fig4 = fig_frame_structure()
    fig5 = fig_address_scope()
    fig6 = fig_ig_bit()

    d = new_doc("华东师范大学软件学院实验报告", "Lab2  Ethernet 以太网帧的捕获与分析")

    # 封面信息表
    table(d, ["实验信息", "个人信息", "记录信息"], [
        ["实验课程  计算机网络", "姓名  刘小凡", "实验日期  2026-10-02"],
        ["实验编号  Lab2", "学号  10244602411", "实验时间  2 学时"],
        ["实验名称  Ethernet", "年级  2024 级", "实验成绩  __________"],
    ], [5.5, 5.4, 5.5], header=False)

    # ---------------- 一、实验目的 ----------------
    head(d, "一、实验目的")
    para(d, "本实验以 ICMP Echo 流量为切入点，用 Wireshark 捕获并逐字段拆解以太网帧，"
            "掌握 DIX Ethernet（Ethernet II）的帧格式与地址作用范围，并回答广播地址与"
            "IEEE 802.3 的相关问题。具体目标如下：")
    for t in [
        "1. 掌握在 Wireshark 中选择捕获接口、设置捕获过滤器、关闭混杂模式以及开启 "
        "MAC 地址解析的方法，并能保存可复核的 pcapng 迹线。",
        "2. 依据协议详情面板与原始字节，确认目的 MAC、源 MAC 和 Type 字段的偏移与长度，"
        "并由实测长度验证帧结构与理论模型的差异（FCS、填充、前导码为何不可见）。",
        "3. 结合本机 IP、默认网关与 ARP 缓存，解释访问远程主机时目的 MAC 为什么指向下一跳，"
        "并区分 MAC 地址与 IP 地址的作用范围。",
        "4. 捕获广播与组播流量，写出以太网广播地址的标准形式，并明确指出判断单播/组播的"
        "究竟是以太网地址的哪一位（本次实测以字节级证据纠正了常见的 MSB 误判）。",
        "5. 分析 IEEE 802.3 与 Ethernet II 的格式差异，理解 LLC 在上层协议解复用中的作用。",
    ]:
        para(d, t, indent=False)

    # ---------------- 二、实验内容与实验步骤 ----------------
    head(d, "二、实验内容与实验步骤")
    para(d, "实验按实验手册的五个 Step 推进：先用 ping 产生单播 ICMP 流量并捕获，"
            "再检查帧内各字段；其次绘制帧结构图与地址范围图；随后用 ether multicast "
            "过滤器捕获广播/组播背景流量；最后完成手册的 Turn-in 题与 IEEE 802.3 拓展题。")
    para(d, "需要特别区分两种过滤器：捕获过滤器（capture filter）在开始抓包前决定记录哪些帧，"
            "使用 BPF 语法，例如 icmp、ether multicast；显示过滤器（display filter）在抓包后"
            "筛选已记录的帧，使用 Wireshark 语法，例如 eth.dst == ff:ff:ff:ff:ff:ff、"
            "eth.dst.ig == 1。把 ether multicast 填进显示过滤器是常见错误，它不是显示过滤器语法。")
    para(d, "本实验的三次抓包及其用途如下表。前两次为本机实测数据，第三次是为回答"
            "IEEE 802.3 拓展题而构造的样例（原因见 4.5 节）。")
    table(d, ["迹线文件", "捕获过滤器", "时长 / 帧数", "用途"], [
        ["Lab2_刘小凡_单播.pcapng", "icmp", "约 4 s / 8 帧", "单播帧结构与地址对应"],
        ["Lab2_刘小凡_广播组播.pcapng", "ether multicast", "60 s / 110 帧", "广播与组播地址、I/G 位"],
        ["Lab2_LLC_构造样例.pcapng", "—（构造）", "4 帧", "IEEE 802.3 + LLC 格式对照"],
    ], [5.0, 3.0, 3.2, 5.2])

    # ---------------- 三、实验环境 ----------------
    head(d, "三、实验环境")
    table(d, ["项目", "实测配置"], [
        ["操作系统", "Windows 11，版本 NT 10.0.26200，64 位"],
        ["抓包工具", "Wireshark 4.6.8（含 tshark / dumpcap），Npcap 1.88"],
        ["网络工具", "Windows CMD 的 ping、ipconfig /all、arp -a"],
        ["捕获接口", f"{C['iface_alias']}（{C['iface']}）"],
        ["接口地址", f"IPv4 {C['host_ip']}/24，MAC {C['host_mac']}，默认网关 {C['gw_ip']}"],
        ["链路层类型", "Ethernet（DIX / Ethernet II）"],
        ["ping 目标", f"{C['remote_name']} → {C['remote_ip']}"],
        ["分辨率设置", "2880×1800，200% 缩放（截图坐标按物理像素记录，故界面文字较大）"],
    ], [4.0, 12.4])

    # ---------------- 四、实验过程与分析 ----------------
    head(d, "四、实验过程与分析")

    # 4.1
    head(d, "4.1  单播迹线的获取与定位", 2)
    para(d, "先用 ping 验证目标可达，再开始抓包，可以避免把网络不通误判为抓包失败。"
            f"本次 ping {C['remote_name']}，解析到 IPv4 地址 {C['remote_ip']}，"
            f"4 次请求全部收到回复，丢失 0%，往返时间约 14–180 ms。")
    cmd(d, "ping -4 -n 4 www.baidu.com")
    para(d, "参数 -4 把查询固定在 IPv4。若不加 -4，域名可能先解析出 IPv6 地址，"
            "此时用 icmp 作为捕获过滤器将抓不到任何帧，这是初学者最常见的空迹线原因之一。")
    para(d, "抓包参数按手册要求设置：捕获接口选实际的联网物理接口 WLAN，"
            "链路层类型为 Ethernet，捕获过滤器为 icmp，关闭混杂模式（只记录本机收发的帧），"
            "并开启 MAC 地址解析以便识别厂商。随后在捕获过程中重新执行上面的 ping 命令，"
            "结束后停止捕获并保存为 pcapng。")
    para(d, "本次捕获共 8 帧，恰好对应 4 个 Echo Request 与 4 个 Echo Reply。"
            "Wireshark 中显示过滤器 icmp 生效后（绿色表示语法有效），"
            "列表、协议详情与原始字节三个面板的关系如图 1 所示。"
            "图中帧 1 为请求帧，源 IP 为本机、目的 IP 为远程服务器，长度均为 74 字节。")
    figure(d, EV / "fig1_unicast_icmp_list.png",
           "图 1  单播迹线（Lab2_刘小凡_单播.pcapng）：显示过滤器 icmp 生效，"
           "共 8 帧，Frame 1 为 Echo (ping) request，长度 74 B")
    table(d, ["观测项目", "实测值"], [
        ["迹线总帧数", f"{C['n_req'] + C['n_rep']} 帧（请求 {C['n_req']} + 回复 {C['n_rep']}）"],
        ["选取的请求帧 / 回复帧", "帧 1（序号 6）/ 帧 2（序号 6）"],
        ["Frame Length 与 Capture Length", f"{C['frame_len']} B / {C['frame_len']} B（未截断）"],
        ["EtherType", "0x0800（IPv4）"],
        ["IPv4 首部长度 / 总长度", f"{C['ip_hdr_len']} B / {C['ip_total_len']} B"],
        ["IPv4 Protocol", "1（ICMP）"],
        ["ICMP Identifier / Sequence", f"{C['icmp_id']} / {C['seqs']}（4 次依次递增）"],
        ["ICMP Type 与 Code", "请求 8/0；回复 0/0"],
        ["ICMP 数据长度", f"{C['icmp_data_len']} B（Windows ping 默认填充 32 B 字母序列）"],
        ["TTL", f"请求 {C['ttl_req']}；回复 {C['ttl_rep']}"],
    ], [6.0, 10.4])
    para(d, "关于请求与回复的配对：ICMP 的 Identifier 在本次抓包中恒为 1，"
            "而 Sequence Number 依次为 6、7、8、9，恰好与 ping 的 4 次请求一一对应，"
            "因此可以通过这两个字段确认请求与回复属于同一次 ping 过程。"
            "TTL 的差异也值得注意：本机发出的请求 TTL 为 128（Windows 默认值），"
            "而回复的 TTL 为 52，说明服务器端以 64 起跳、报文经过约 12 跳到达本机，"
            "这一差值本身不参与以太网帧结构分析，但它证明回复确实来自远端而不是本地伪造。")

    # 4.2
    head(d, "4.2  Ethernet II 的字段与长度（逐字节验证）", 2)
    para(d, "下面以帧 1 为例逐字节核对。Wireshark 导出的原始字节如下，"
            "每行左侧为帧内偏移（十六进制），右侧为该偏移起的 16 个字节：")
    mono_lines(d, FRAME1_HEX)
    para(d, "对照字节可以逐项确认字段位置：偏移 0–5 是目的 MAC（28 d1 27 df d4 95），"
            "偏移 6–11 是源 MAC（14 ac 60 56 df 85），偏移 12–13 是类型字段（08 00 = 0x0800），"
            "偏移 14 起是 IPv4 首部（首字节 45 表示版本 4、首部长度 5 个 4 字节即 20 B），"
            "偏移 34 起是 ICMP 首部（08 00 即 Type=8、Code=0），偏移 42 起是 32 字节数据。"
            "全部字段及长度见下表。")
    table(d, ["字段", "偏移", "长度", "实测值（帧 1）", "含义"], [
        ["目的 MAC", "0–5", "6 B", f"{C['gw_mac']}（{C['gw_mac_oui']}）", "本地下一跳（默认网关）"],
        ["源 MAC", "6–11", "6 B", f"{C['host_mac']}（{C['host_mac_oui']}）", "本机 WLAN 接口"],
        ["Type", "12–13", "2 B", "0x0800", "载荷为 IPv4"],
        ["IPv4 首部", "14–33", "20 B", "版本 4，首部长度 5×4=20", "无选项"],
        ["IPv4 总长度", "16–17", "2 B", f"{C['ip_total_len']} B", "IP 首部 20 + ICMP 40"],
        ["IPv4 Protocol", "23", "1 B", "1", "载荷为 ICMP"],
        ["IPv4 源/目的", "26–33", "8 B", f"{C['host_ip']} / {C['remote_ip']}", "通信两端主机"],
        ["ICMP 首部", "34–41", "8 B", "Type=8, Code=0, Checksum=0x4d55", "Identifier=1"],
        ["ICMP 数据", "42–73", "32 B", "abcdefghij…wabcdefghi", "Windows ping 默认填充"],
        ["—（记录结束）", "74", "—", f"Frame Length = {C['frame_len']} B", "与上面各项之和一致"],
    ], [2.6, 1.9, 1.5, 5.6, 4.8], size=9)
    para(d, f"长度核对：以太网首部 {C['eth_hdr']} B + IPv4 首部 {C['ip_hdr_len']} B + "
            f"ICMP 首部 8 B + ICMP 数据 {C['icmp_data_len']} B = {C['frame_len']} B，"
            f"与 Wireshark 报告的 Frame Length = {C['frame_len']} B 完全一致（592 bits）。"
            f"IPv4 的 Total Length 字段为 {C['ip_total_len']} B，即 20 + 40，"
            "它只统计 IP 数据报本身，不包含以太网首部，两个数字相差正好 14 B。")
    figure(d, fig4, "图 2  帧 1 的字节布局（按字节数等比绘制，附实测偏移与长度）")

    head(d, "4.3  与教材帧格式的差异及原因", 3)
    para(d, "教材图 4-14 中的完整以太网帧与 Wireshark 显示的内容存在若干差异，"
            "原因是抓包位置位于网络层之上，物理层与网卡的一部分工作对操作系统不可见：")
    table(d, ["教材中的字段", "抓包是否可见", "原因"], [
        ["前导码 + SFD（8 B）", "不可见", "物理层用于比特同步与帧起始定界，由网卡硬件处理，不上交操作系统"],
        ["目的 / 源 / 类型（14 B）", "可见", "属于 MAC 帧头，操作系统可读"],
        ["数据 + 填充", "数据可见；填充取决于帧长", "填充只在负载不足 46 B 时出现，本次 ICMP 负载 60 B 无需填充"],
        ["FCS（4 B）", "通常不可见", "由发送/接收网卡计算与校验后被剥离，故 Wireshark 看不到"],
        ["VLAN 标签", "不可见", "VLAN 标签一般由交换机端口添加和移除，主机侧看不到"],
    ], [4.2, 3.6, 8.6])
    para(d, "本次抓包中所有帧的长度都是 74 B，负载 60 B 远大于未标记以太网要求的"
            "最小负载 46 B，因此没有填充。相反，4.4 节捕捉到的 ARP 帧在 Wireshark 中只有 "
            "42 B，低于标准以太网最小帧长 64 B —— 这并不是帧不合规，而是抓包位置在网卡剥离"
            "填充与 FCS 之后；标准要求的最小 64 B 依然成立。这一点在解读广播帧长度时很重要。")

    # 4.4
    head(d, "4.4  MAC 地址的作用范围", 2)
    para(d, "要判断目的 MAC 到底属于谁，必须把抓包结果与本机接口配置、ARP 缓存对照起来。"
            "本机 WLAN 接口的配置如下（ipconfig /all 实测）：")
    cmd(d, "ipconfig /all")
    table(d, ["接口属性", "实测值"], [
        ["适配器", f"{C['iface_alias']}：{C['iface']}"],
        ["物理地址（MAC）", C["host_mac"]],
        ["IPv4 地址 / 子网掩码", f"{C['host_ip']} / 255.255.255.0"],
        ["默认网关 / DHCP 服务器", C["gw_ip"]],
    ], [5.5, 10.9])
    para(d, "再用 arp -a 查询同一接口下默认网关对应的 MAC。关键在于要选择"
            "「接口」地址与本机 WLAN IPv4 相同的那一组，否则会读到 VMware、WSL 等虚拟网卡的记录。"
            "实测结果如下：")
    cmd(d, "arp -a")
    table(d, ["接口", "Internet 地址", "物理地址", "类型"], [
        [C["host_ip"], C["gw_ip"], C["gw_mac"].replace(":", "-"), "dynamic"],
    ], [4.0, 4.0, 4.8, 3.6])
    para(d, f"ARP 缓存中网关 {C['gw_ip']} 的物理地址 {C['gw_mac']} 与帧 1 的"
            f"目的 MAC 字段完全一致，这就从两个独立来源证明了：请求帧的二层目的地址"
            f"是本机所在链路的下一跳（默认网关），而不是远程服务器的网卡地址。"
            f"相对地，帧内的 IPv4 目的地址 {C['remote_ip']} 才是通信对端。"
            f"把三项信息汇总如下表。")
    table(d, ["对象", "IP 地址", "MAC 地址", "是否在本链路"], [
        ["本机 WLAN 接口", C["host_ip"], C["host_mac"], "是"],
        ["默认网关（路由器）", C["gw_ip"], C["gw_mac"], "是（同一网段）"],
        ["远程 Web 服务器", C["remote_ip"], "本迹线无法获知", "否（经 Internet 多跳）"],
    ], [4.4, 4.0, 4.6, 3.4])
    figure(d, fig5, "图 3  本机经默认网关访问远程主机时的地址作用范围（实测地址）")
    para(d, "结论：MAC 地址标识的是「当前这条链路两端的接口」，因此每经过一跳路由器就会被"
            "重新封装成新的源/目的 MAC；而 IP 地址标识的是端到端的通信主机，在全过程中保持不变"
            "（不计 NAT 的情形）。远程服务器当然有自己的网卡 MAC，只是本机这份迹线不可能给出它。")

    # 4.5
    head(d, "4.5  广播与组播迹线的实测统计", 2)
    para(d, "第二次抓包在同一个物理接口上使用捕获过滤器 ether multicast，持续 60 秒记录"
            "自然背景流量（不主动制造测试流量）。实测共捕获 110 帧，总长 8928 字节，"
            "协议分布与地址统计如下。")
    table(d, ["统计项", "实测结果"], [
        ["捕获时长", f"约 {C['duration']} s"],
        ["迹线总帧数", f"{C['frames']} 帧"],
        ["以太网广播帧（目的 MAC ff:ff:ff:ff:ff:ff）", f"{C['broadcast']} 帧"],
        ["普通组播帧（IG=1 且非广播）", f"{C['mcast']} 帧"],
        ["主要上层协议", "ARP 2 帧；NBNS 9 帧；mDNS 72 帧；LLMNR 24 帧；DHCPv6 3 帧"],
    ], [9.0, 7.4])
    para(d, "按目的 MAC 归类，共出现 6 种组地址，全部满足第一个字节最低位为 1：")
    table(d, ["目的 MAC", "帧数", "首字节", "I/G", "U/L", "上层协议与用途"], [
        ["ff:ff:ff:ff:ff:ff", "11", "0xFF", "1", "1", "ARP 请求、NBNS WPAD 名称查询"],
        ["01:00:5e:00:00:fb", "36", "0x01", "1", "0", "IPv4 组播 224.0.0.251，mDNS"],
        ["01:00:5e:00:00:fc", "12", "0x01", "1", "0", "IPv4 组播，LLMNR（UDP 5355）"],
        ["33:33:00:00:00:fb", "36", "0x33", "1", "1", "IPv6 组播 ff02::fb，mDNS"],
        ["33:33:00:01:00:03", "12", "0x33", "1", "1", "IPv6 组播，LLMNR"],
        ["33:33:00:01:00:02", "3", "0x33", "1", "1", "IPv6 组播，DHCPv6"],
    ], [5.4, 1.6, 2.0, 1.4, 1.4, 4.6], size=9)
    para(d, "用显示过滤器 eth.dst == ff:ff:ff:ff:ff:ff 可以得到全部 11 个广播帧，"
            "包含 2 个 ARP 请求和 9 个 NBNS 名称查询（查询 WPAD<00>，即代理自动发现），"
            "如图 4 所示；用 eth.dst.ig == 1 && eth.dst != ff:ff:ff:ff:ff:ff 可以得到"
            "其余 99 个普通组播帧，如图 5 所示。两次筛选的帧数之和 11 + 99 = 110，"
            "与迹线总帧数一致，说明 ether multicast 过滤器恰好把迹线完整划分为广播与普通组播两部分。")
    figure(d, EV / "fig2_broadcast_filtered.png",
           "图 4  显示过滤器 eth.dst == ff:ff:ff:ff:ff:ff 的结果：11 个以太网广播帧，"
           "含 2 个 ARP 请求与 9 个 NBNS WPAD 名称查询")
    figure(d, EV / "fig3_multicast_filtered.png",
           "图 5  显示过滤器 eth.dst.ig == 1 && eth.dst != ff:ff:ff:ff:ff:ff 的结果："
           "99 个普通组播帧（mDNS、LLMNR、DHCPv6）")

    head(d, "4.6  广播帧的地址与 I/G 判断位（重点）", 3)
    para(d, "广播帧的原始字节如下（帧 1，42 B）。可以看到前 6 个字节全为 ff，"
            "紧随其后是源 MAC、类型字段 0x0806（ARP），再往后是 ARP 报文：")
    mono_lines(d, ARP_HEX)
    para(d, "该 ARP 报文的 Opcode 为 1（request），Sender IP 为 "
            f"{C['host_ip']}，Target IP 为 {C['gw_ip']}，Target MAC 为全零，"
            "说明这是本机在询问网关的 MAC 地址，属于普通的地址解析请求，"
            "而不是「免费 ARP（Gratuitous ARP）」。免费 ARP 的特征是发送方通告自己的地址"
            "（Sender IP 等于 Target IP）或目标 MAC 为广播，两者含义不同，"
            "不能仅凭「目的 MAC 是广播」就把所有 ARP 帧都归为免费 ARP。"
            "本机未出现 ARP 冲突检测流量，因为网关的 ARP 记录一直有效。")
    para(d, "以太网广播地址的写法为 ff:ff:ff:ff:ff:ff，即 48 位全为 1。"
            "判断一个以太网地址是单播还是组播/广播，看的是地址第一个字节的"
            "最低有效位（Least Significant Bit，LSB），也就是 bit 0，称为 I/G 位："
            "该位为 0 表示 Individual（单播），为 1 表示 Group（组播，广播是其中的特例）。"
            "紧邻的 bit 1 是 U/L 位，用于区分全球唯一地址与本地管理地址，"
            "它判断的是地址的管理属性，与收发对象无关，两者不可混淆。")
    figure(d, fig6, "图 6  目的 MAC 首字节中 I/G 位（bit 0）与 U/L 位（bit 1）的位置及本次实测地址的取值")
    para(d, "这里需要特别强调一个容易出错的地方：I/G 位是第一个字节的最低有效位，"
            "而不是最高有效位。教材中文译本中曾把该位描述为「最左侧的第一位」，"
            "这容易被理解为 MSB，从而得出相反结论。本次实测给出了直接的字节级反证："
            "广播地址首字节为 0xFF，其二进制为 1111 1111，最低位为 1；"
            "普通组播地址 01:00:5e:00:00:fb 的首字节为 0x01，二进制 0000 0001，"
            "最低位同样为 1；而两个单播地址 28:d1:27:df:d4:95（首字节 0x28 = 0010 1000）"
            "与 14:ac:60:56:df:85（首字节 0xAC = 1010 1100）的最低位都是 0。"
            "若按最高位判断，0xAC 的最高位为 1，就会被错误判为组播地址，"
            "这与实际抓到的单播流量直接矛盾。此外，以太网在发送每个字节时先发送最低位"
            "（LSB first），因此手册所说的「先发送的第一位」与这里的 bit 0 是同一个位。")
    para(d, "补充一点观察：NBNS 的 9 个广播帧源 MAC 都是本机 14:ac:60:56:df:85，"
            "说明这些名称查询是本机发出的（本机设置了系统代理，因而主动查询 WPAD）。"
            "这提醒我们，广播流量并不只来自路由器或其他设备，本机自身也是常见的广播源。")

    # 4.7
    head(d, "4.7  IEEE 802.3 拓展：格式对照与 LLC 解复用", 2)
    para(d, "手册的拓展题要求观察 IEEE 802.3 帧。我在本机全部迹线中用显示过滤器 llc 检索，"
            "结果为零：单播迹线（8 帧）、广播组播迹线（110 帧）以及此前实验累积的"
            "lab1.pcapng（144509 帧）中都没有 LLC 帧。这也符合手册的说明 —— "
            "IEEE 802.3 格式在现代网络中已很少见到，抓不到属于正常现象。"
            "因此在下面的分析中，格式结论给出原理推导，字段数值则用一份按标准构造的"
            "IEEE 802.3 + LLC 样例来验证，该样例文件已在附录中标注来源，"
            "不与本机实测统计混用。")
    para(d, "构造样例的第 1 帧（IEEE 802.3 + LLC，25 B）原始字节如下：")
    mono_lines(d, LLC_HEX)
    para(d, "Wireshark 对该帧的解析为「IEEE 802.3 Ethernet」，"
            "偏移 12–13 的两字节显示为 Length: 11，随后是 Logical-Link Control，"
            "DSAP/SSAP 均为 0x42，Control 为 0x03（无编号信息 UI 帧）。"
            "对照样例的第 2 帧为 Ethernet II，同样的 12–13 偏移处显示 Type: IPv4 (0x0800)。"
            "同一个 16 位字段位置，在两种格式下含义完全不同，这正是区分二者的关键。")
    table(d, ["对照项", "DIX Ethernet（Ethernet II）", "IEEE 802.3"], [
        ["偏移 12–13 字段", "Type（类型）", "Length（长度）"],
        ["字段取值含义", "≥ 0x0600（1536）表示上层协议类型", "≤ 1500（0x05DC）表示后续数据字节数"],
        ["二层首部长度", "14 B（MAC 首部）", "14 B（MAC 首部）"],
        ["上层协议识别", "直接由 Type 字段决定", "由其上的 LLC 字段（DSAP 等）决定"],
        ["LLC 首部", "不存在", "通常 3 B（DSAP/SSAP/Control），SNAP 时再加 5 B"],
        ["合计首部长度", "14 B", "17 B（含 3 B LLC）；SNAP 时为 22 B"],
        ["本次实测", "全部帧均为该格式", "未捕获到（构造样例用于对照）"],
    ], [3.4, 6.6, 6.4])
    para(d, "三个拓展问题的回答如下：")
    para(d, "问题 1：IEEE 802.3 与 LLC 组合的首部比 DIX Ethernet 长多少？"
            "两者的 MAC 首部都是 14 B（6 B 目的地址 + 6 B 源地址 + 2 B 长度/类型）。"
            "IEEE 802.3 在其上还有 LLC 首部：当 Control 字段为单字节的 UI 格式时，"
            "DSAP、SSAP、Control 共 3 B，因此合计 17 B，比 DIX Ethernet 长 3 B。"
            "若 LLC 之上再带 SNAP，则要追加 5 B（3 B OUI + 2 B 协议标识），合计 22 B，"
            "比 DIX Ethernet 长 8 B。样例帧的 Length 字段为 11，"
            "正好等于 LLC 首部 3 B 加上有效数据 8 B，可以直接验证长度字段的含义。"
            "需要注意 Trailer/Padding 与 FCS 位于帧尾，不应计入首部长度。", indent=False)
    para(d, "问题 2：接收方如何判断帧是 DIX Ethernet 还是 IEEE 802.3？"
            "读取源地址之后的 16 位字段：若其值不小于 1536（0x0600），"
            "则按 EtherType 解释，属于 DIX Ethernet；若其值不大于 1500（0x05DC），"
            "则按长度解释，其后跟随 LLC，属于 IEEE 802.3。"
            "1501–1535 这一段两个标准都不使用，因此不可能出现。"
            "样例中 0x000B 落在长度区间，Ethernet II 样例中 0x0800 落在类型区间，"
            "Wireshark 也正是据此把两帧分别标注为 IEEE 802.3 和 Ethernet II。", indent=False)
    para(d, "问题 3：IEEE 802.3 没有 Type 字段，上层协议是如何确定的？"
            "由 LLC 首部中的服务访问点字段解复用，接收端主要看 DSAP。"
            "DSAP 指明上层协议或协议族，SSAP 指明发送方，Control 指明 LLC 帧类型"
            "（0x03 为无编号信息的 UI 帧，常用于承载上层协议数据）。"
            "当 DSAP 与 SSAP 均为 0xAA 时表示使用 SNAP 扩展："
            "Control 通常为 0x03，其后 3 B 为 OUI、2 B 为协议标识；"
            "当 OUI 为 0x000000 时，该 2 B 协议标识沿用 EtherType 的编号，"
            "例如 IPv4 为 0x0800，从而实现与 DIX Ethernet 的兼容。"
            "在构造样例中 DSAP=0x42，Wireshark 据 SAP 值将其识别为生成树 BPDU，"
            "这就是「用 DSAP 作为解复用键」的直接体现。", indent=False)

    head(d, "4.8  实验过程中遇到的问题与处理", 3)
    para(d, "本次实验过程中遇到并处理了以下问题，记录于此以便复核：")
    table(d, ["现象", "原因分析", "处理方式与结果"], [
        ["以 icmp 为捕获过滤器时迹线为空",
         "本机存在系统代理（127.0.0.1:10808）且域名可能优先解析为 IPv6，"
         "ICMP 虽不经代理，但目标地址族不对时过滤器不匹配任何帧",
         "改为 ping -4 强制 IPv4 并先确认目标可回复，随后抓到 8 帧"],
        ["捕获过滤器填在显示过滤器位置报语法错误",
         "ether multicast 是 BPF 捕获过滤器语法，不是 Wireshark 显示过滤器语法",
         "捕获阶段使用 ether multicast，分析阶段改用 eth.dst.ig == 1 等显示过滤器"],
        ["arp -a 输出中有多组接口记录，易读错",
         "本机同时存在 VMware、WSL 等虚拟网卡及各自的 ARP 缓存",
         "只取「接口」地址与本机 WLAN IPv4 相同的那一组，再与帧内目的 MAC 比对"],
        ["迹线中检索不到 LLC 帧",
         "IEEE 802.3 在现代网络中极少见，本机三段迹线均为 DIX Ethernet",
         "据实记录为未观察到，并用构造的 IEEE 802.3 + LLC 样例完成字段级验证"],
        ["广播/组播帧数量受环境影响",
         "无线网络会抑制广播，背景流量随设备数量与时间变化",
         "延长观测至 60 秒并记录时长，报告按实测 110 帧统计，不硬凑固定数量"],
    ], [4.2, 6.2, 6.0], size=9)

    # ---------------- 五、实验结果总结 ----------------
    head(d, "五、实验结果总结")
    head(d, "5.1  Turn-in 题回答", 2)
    para(d, "题目 1：绘制 ping 报文以太网帧结构图。见 4.2 节图 2。"
            "目的 MAC、源 MAC 与 Type 字段的长度分别为 6 B、6 B、2 B，"
            "以太网首部共 14 B；IPv4 数据报与 ICMP 报文整体作为它的有效载荷，"
            "实测载荷为 60 B，抓包记录总长 74 B。标准帧末尾另有 4 B FCS，"
            "由网卡处理，抓包中通常不可见，图中以虚线框表示其存在。")
    para(d, "题目 2：绘制地址范围图。见 4.4 节图 3。本机 "
            f"（{C['host_ip']}，{C['host_mac']}）与默认网关（{C['gw_ip']}，{C['gw_mac']}）"
            f"处于同一链路，远程服务器（{C['remote_ip']}）经 Internet 到达。"
            "请求帧的以太网目的地址是下一跳网关的 MAC，"
            "而 IPv4 的目的地址才是远程服务器；回复帧在本地链路上以网关为源 MAC、"
            "以本机为目的 MAC。")
    para(d, "题目 3：以太网广播地址是什么？判断位是哪一位？"
            "广播地址为 ff:ff:ff:ff:ff:ff，即 48 位全为 1。"
            "判断单播与组播/广播的位是目的 MAC 第一个字节的最低有效位（bit 0），"
            "称为 I/G 位：0 表示单播，1 表示组播或广播。"
            "本次实测的字节证据为：广播 0xFF（最低位 1）、组播 0x01 与 0x33（最低位 1）、"
            "单播 0x28 与 0xAC（最低位 0）。需要强调的是该位不是最高有效位，"
            "若按最高位判断，首字节 0xAC 的本机单播地址会被误判为组播，与实测矛盾。")

    head(d, "5.2  实测结果汇总", 2)
    table(d, ["项目", "实测结论"], [
        ["单播迹线", f"{C['n_req'] + C['n_rep']} 帧，每帧 {C['frame_len']} B，"
                     f"EtherType 0x0800，IPv4 总长 {C['ip_total_len']} B，ICMP 请求 8/回复 0"],
        ["帧长核对", f"14（以太网）+ 20（IPv4）+ 8（ICMP）+ {C['icmp_data_len']}（数据）"
                     f"= {C['frame_len']} B，与 Frame Length 一致"],
        ["地址对应", f"目的 MAC {C['gw_mac']} = ARP 缓存中网关 {C['gw_ip']} 的 MAC；"
                     f"目的 IP {C['remote_ip']} 为远程服务器"],
        ["广播组播迹线", f"{C['duration']} s 共 {C['frames']} 帧 = 广播 {C['broadcast']} + "
                         f"普通组播 {C['mcast']}"],
        ["广播帧构成", "2 个 ARP 地址解析请求（非免费 ARP）+ 9 个 NBNS WPAD 名称查询"],
        ["组播地址", "01:00:5e:00:00:fb / fc（IPv4）与 33:33:…（IPv6），对应 mDNS、LLMNR、DHCPv6"],
        ["I/G 位", "目的 MAC 首字节 bit 0；组播与广播为 1，单播为 0"],
        ["LLC / IEEE 802.3", "本机三段迹线均为 0 帧，未观察到；已用构造样例完成格式对照"],
    ], [3.6, 12.8])

    head(d, "5.3  实验体会", 2)
    para(d, "这次实验最大的收获是「用字节说话」。教材与网络资料对判断单播/组播的位位置"
            "存在不一致的说法，有的写「最左侧第一位」容易被读成最高位。"
            "只要把原始字节调出来逐位核对 —— 广播 0xFF、组播 0x01、单播 0xAC —— "
            "结论就没有歧义。这也说明抓包实验的价值不仅在于验证理论，"
            "更在于当资料表述含糊时能够自己取得判据。")
    para(d, "其次是理解了「观测位置决定观测结果」。同一个以太网帧，"
            "在主机上抓到的是 74 B 而没有 FCS 和填充；ARP 帧只有 42 B，"
            "低于标准最小帧长 64 B。如果不知道 FCS 由网卡剥离、填充在抓包点之前已经完成，"
            "很容易误判为帧不符合标准。抓包看到的是「操作系统能看到的那一部分」，"
            "而不是线上传输的全部比特，这一点对后续分析无线帧和隧道流量同样重要。")
    para(d, "最后是抓包口径要一致。广播/组播数量完全取决于网络环境和观测时长，"
            "本次 60 秒得到 110 帧，其中广播 11 帧。报告如实记录时长与数量，"
            "并注明本机因配置系统代理而主动发送 NBNS WPAD 查询，"
            "而不是照搬他人报告的数值。这样得到的数据才能经得起复核。")

    # ---------------- 六、附录 ----------------
    d.add_page_break()
    head(d, "六、附录")
    head(d, "6.1  关键命令与过滤器", 2)
    table(d, ["用途", "表达式或命令"], [
        ["生成 IPv4 Echo 流量", "ping -4 -n 4 www.baidu.com"],
        ["查看接口与网关", "ipconfig /all"],
        ["查看 IPv4 到 MAC 映射", "arp -a"],
        ["单播捕获过滤器", "icmp"],
        ["广播组播捕获过滤器", "ether multicast"],
        ["仅显示 Echo 请求 / 回复", "icmp.type == 8  /  icmp.type == 0"],
        ["仅显示以太网广播", "eth.dst == ff:ff:ff:ff:ff:ff"],
        ["仅显示普通以太网组播", "eth.dst.ig == 1 && eth.dst != ff:ff:ff:ff:ff:ff"],
        ["按 I/G 位筛选全部组地址", "eth.dst.ig == 1"],
        ["检索 LLC / IEEE 802.3", "llc"],
        ["导出字段用于复核", "tshark -r <文件> -T fields -e frame.len -e eth.dst -e ip.src"],
    ], [5.4, 11.0])
    head(d, "6.2  数据与资料来源", 2)
    para(d, "实测数据文件（均位于 _lab2_工作\\captures）："
            "Lab2_刘小凡_单播.pcapng（8 帧，2026-10-02）、"
            "Lab2_刘小凡_广播组播.pcapng（110 帧，60 s，2026-10-02）；"
            "Lab2_LLC_构造样例.pcapng 为回答 IEEE 802.3 拓展题而按标准构造的对照样例，"
            "不与本机实测统计混用。报告中的图 1、图 4、图 5 为 Wireshark 4.6.8 "
            "实际界面截图，图 2、图 3、图 6 为依据实测数据绘制的示意图。")
    for t in [
        "［1］课程资料：计算机网络实验手册（Ethernet）；计算机网络实验报告模板。",
        "［2］Wireshark Foundation. Ethernet 与 Ethernet Display Filter Reference. "
        "https://wiki.wireshark.org/Ethernet  https://www.wireshark.org/docs/dfref/e/eth.html",
        "［3］RFC 1042. A Standard for the Transmission of IP Datagrams over IEEE 802 Networks. "
        "https://www.rfc-editor.org/rfc/rfc1042.html",
        "［4］IEEE 802-2014. IEEE Standard for Local and Metropolitan Area Networks: "
        "Overview and Architecture（I/G 位与 U/L 位的定义）。",
        "［5］IANA. IEEE 802 Numbers. https://www.iana.org/assignments/ieee-802-numbers",
    ]:
        p = para(d, t, indent=False)
        for r in p.runs:
            cn(r, 9)

    d.save(OUT)
    print(f"SAVED {OUT}")
    print(f"figures: {fig4.name}, {fig5.name}, {fig6.name}")


if __name__ == "__main__":
    build()
