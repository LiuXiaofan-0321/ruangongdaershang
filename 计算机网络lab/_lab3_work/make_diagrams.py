# -*- coding: utf-8 -*-
"""make_diagrams.py - draw the two original Lab3 figures.

Fig A: IPv4 packet structure for frame 4, with byte offsets and field lengths,
       grouping fields that share bytes (Version/IHL, Flags/Fragment offset).
Fig B: Internet path with 17 hops from logs/source_trace.json, including unknown
       hops, and the APNIC registry organisation labels.

These are the student's own drawings (not screenshots) and are captioned as such.

Usage: python make_diagrams.py
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

WORK = Path(r"C:\University Courses\计算机网络lab\_lab3_work")
OUT = WORK / "evidence"
CN = r"C:\Windows\Fonts\msyh.ttc"
CNB = r"C:\Windows\Fonts\msyhbd.ttc"


def f(size, bold=False):
    return ImageFont.truetype(CNB if bold else CN, size)


# --------------------------------------------------------------------------
# Figure A: IPv4 packet structure (frame 4, from facts.json)
# --------------------------------------------------------------------------
def fig_ipv4_structure():
    S = 34                      # px per byte
    LEFT = 110
    TOP = 200
    H = 96
    TABLE_W = 1340
    W = max(LEFT + 40 * S + 60, TABLE_W + 80)
    TABLE_H = 40 + 10 * 34
    IM = Image.new("RGB", (W, TOP + H + 250 + TABLE_H + 110), "white")
    d = ImageDraw.Draw(IM)

    d.text((40, 30), "IPv4 数据报结构（依据实测第 4 帧 HTTP GET，IP 首部 20 B）",
           font=f(34, True), fill="#111111")
    d.text((40, 78), "矩形按字节等比绘制；同一字节内无法再分的字段合并为一格，"
                     "下方表列出每格字节数与实测值",
           font=f(21), fill="#555555")

    # top bar: byte boxes with SHORT labels only
    boxes = [
        (0, 1, "Ver\nIHL", "#DCE6F1"),
        (1, 1, "DS", "#DCE6F1"),
        (2, 2, "Total\nLength", "#DCE6F1"),
        (4, 2, "Ident.", "#DCE6F1"),
        (6, 2, "Flags\nFragOff", "#DCE6F1"),
        (8, 1, "TTL", "#DCE6F1"),
        (9, 1, "Proto", "#DCE6F1"),
        (10, 2, "Hdr\nCksum", "#DCE6F1"),
        (12, 4, "Source Address", "#E3EFDA"),
        (16, 4, "Destination Address", "#E3EFDA"),
        (20, 20, "TCP 首部 + HTTP 请求（IP 载荷）", "#FBEEDA"),
    ]
    for start, n, label, col in boxes:
        x0 = LEFT + start * S
        x1 = LEFT + (start + n) * S
        d.rectangle((x0, TOP, x1, TOP + H), fill=col, outline="#5A6B7C", width=2)
        # shrink the font until the text fits the box width
        for size in (18, 16, 14, 12, 10):
            fnt = f(size)
            lines = label.split("\n")
            widest = max(d.textbbox((0, 0), l, font=fnt)[2] - d.textbbox((0, 0), l, font=fnt)[0]
                         for l in lines)
            if widest <= (x1 - x0) - 8 or size == 10:
                break
        th = sum(d.textbbox((0, 0), l, font=fnt)[3] - d.textbbox((0, 0), l, font=fnt)[1]
                 for l in lines) + 5 * (len(lines) - 1)
        y = TOP + (H - th) / 2
        for l in lines:
            bb = d.textbbox((0, 0), l, font=fnt)
            d.text(((x0 + x1 - (bb[2] - bb[0])) / 2, y - bb[1]), l, font=fnt, fill="#12212F")
            y += (bb[3] - bb[1]) + 5

    # byte ruler
    for b in range(0, 41, 2):
        x = LEFT + b * S
        d.line((x, TOP - 8, x, TOP), fill="#999999", width=1)
        if b % 4 == 0:
            bb = d.textbbox((0, 0), str(b), font=f(15))
            d.text((x - (bb[2] - bb[0]) / 2, TOP - 30), str(b), font=f(15), fill="#666666")
    d.text((LEFT - 96, TOP - 30), "字节偏移", font=f(15), fill="#666666")

    # spans
    def span(b0, b1, y, text, col="#233746"):
        xa, xb = LEFT + b0 * S, LEFT + b1 * S
        d.line((xa, y, xb, y), fill=col, width=3)
        d.line((xa, y - 10, xa, y + 10), fill=col, width=3)
        d.line((xb, y - 10, xb, y + 10), fill=col, width=3)
        bb = d.textbbox((0, 0), text, font=f(19))
        d.text(((xa + xb - (bb[2] - bb[0])) / 2, y + 12), text, font=f(19), fill=col)

    span(0, 20, TOP + H + 40, "IP 首部 = 20 B")
    span(20, 40, TOP + H + 40, "IP 载荷（TCP 首部起，不含以太网填充）", "#1F5C33")
    span(0, 37, TOP + H + 110, "IP Total Length = 117 B（IP 首部 20 + 载荷 97）")
    span(0, 37, TOP + H + 180, "Ethernet 帧长 131 B（多出的 14 B 为以太网首部，不计入 Total Length）")

    # field table
    ty = TOP + H + 250
    heads = ["字段（共用字节者合并）", "字节偏移", "长度", "实测值（第 4 帧）"]
    widths = [390, 130, 90, 730]
    total_w = sum(widths)
    d.rectangle((40, ty, 40 + total_w, ty + 40), fill="#E8EEF4", outline="#9DB2C6")
    x = 40
    for h, w in zip(heads, widths):
        d.text((x + 12, ty + 9), h, font=f(19, True), fill="#12212F")
        x += w
    rows = [
        ("Version + IHL", "0", "1 B", "0x45：Version=4，IHL=5"),
        ("Differentiated Services", "1", "1 B", "0x00（DSCP CS0，ECN Not-ECT）"),
        ("Total Length", "2–3", "2 B", "0x0075 = 117 B"),
        ("Identification", "4–5", "2 B", "0xedc0"),
        ("Flags + Fragment Offset", "6–7", "2 B", "0x4000：DF=1，MF=0，Offset=0"),
        ("Time To Live", "8", "1 B", "128"),
        ("Protocol", "9", "1 B", "6（TCP）"),
        ("Header Checksum", "10–11", "2 B", "0x0000（网卡校验和卸载，抓包点尚未填）"),
        ("Source Address", "12–15", "4 B", "172.31.165.86"),
        ("Destination Address", "16–19", "4 B", "182.61.200.108"),
    ]
    ry = ty + 40
    for i, r in enumerate(rows):
        if i % 2 == 0:
            d.rectangle((40, ry, 40 + total_w, ry + 34), fill="#F7F9FB", outline="#D5DEE7")
        else:
            d.rectangle((40, ry, 40 + total_w, ry + 34), outline="#D5DEE7")
        x = 40
        for v, w in zip(r, widths):
            d.text((x + 12, ry + 7), v, font=f(18), fill="#12212F")
            x += w
        ry += 34

    d.text((40, ry + 16), "说明：本图为依据实测字段绘制的示意图，不是 Wireshark 截图；"
                          "“Hdr Cksum = 0x0000”属校验和卸载现象，正文有说明。",
           font=f(19), fill="#777777")
    p = OUT / "fig_A_ipv4_structure.png"
    IM.save(p)
    return p


# --------------------------------------------------------------------------
# Figure B: Internet path (17 hops)
# --------------------------------------------------------------------------
def fig_path():
    hops = json.loads((WORK / "logs" / "source_trace.json").read_text(encoding="utf-8"))
    ORG = {
        "10.100.4.1": "私网地址，无登记信息",
        "202.120.95.246": "CERNET（APNIC）",
        "202.120.95.254": "CERNET（APNIC）",
        "101.4.116.61": "BJR-CERNET（APNIC）",
        "101.4.118.249": "BJR-CERNET（APNIC）",
        "219.224.103.65": "BJR-CERNET（APNIC）",
        "101.4.129.142": "BJR-CERNET（APNIC）",
        "182.61.255.32": "Baidu（APNIC）",
        "182.61.254.169": "Baidu（APNIC）",
        "182.61.200.108": "Baidu 服务器（终点）",
    }
    ROW = 62
    W, Hleft = 1700, 300
    H = Hleft + len(hops) * ROW + 120
    IM = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(IM)

    d.text((40, 26), "到 182.61.200.108 的 Internet 路径（绑定 WLAN 源地址的 ICMP 探测）",
           font=f(32, True), fill="#111111")
    d.text((40, 70), "共 17 跳；每跳 3 次探测，星号表示 900 ms 内无应答，不代表该跳不存在",
           font=f(21), fill="#555555")

    x_hop, x_ip, x_rtt, x_org = 60, 250, 620, 980
    y = Hleft - 60
    d.text((x_hop, y), "跳数", font=f(20, True), fill="#333333")
    d.text((x_ip, y), "IP 地址", font=f(20, True), fill="#333333")
    d.text((x_rtt, y), "三次 RTT (ms)", font=f(20, True), fill="#333333")
    d.text((x_org, y), "组织（来源见正文说明）", font=f(20, True), fill="#333333")
    d.line((40, y + 32, W - 40, y + 32), fill="#999999", width=2)

    y = Hleft
    for h in hops:
        probes = h["probes"]
        addr = next((p["address"] for p in probes if p["address"]), None)
        if addr is None:
            ip_txt, org, col = "— 无应答 —", "未知", "#999999"
        else:
            ip_txt = addr
            org = ORG.get(addr, "未查询")
            col = "#B00020" if addr == "182.61.200.108" else "#12212F"
        rtt = []
        for p in probes:
            rtt.append("—" if p["rtt_ms"] is None else str(p["rtt_ms"]))
        d.text((x_hop, y), str(h["hop"]), font=f(22, True), fill=col)
        d.text((x_ip, y), ip_txt, font=f(21), fill=col)
        d.text((x_rtt, y), " / ".join(rtt), font=f(21), fill="#333333")
        d.text((x_org, y), org, font=f(21), fill=col)
        d.line((40, y + 46, W - 40, y + 46), fill="#E4E4E4", width=1)
        y += ROW

    d.text((40, y + 16), "起点：本机 WLAN 172.31.165.86；终点：182.61.200.108（百度服务器）",
           font=f(21, True), fill="#1F5C33")
    d.text((40, y + 52), "组织名称来自 APNIC RDAP 地址登记查询，是登记归属而非物理位置或域名反解；"
                         "星号跳未做推断。本图为依据 source_trace.json 绘制的示意图。",
           font=f(19), fill="#777777")
    p = OUT / "fig_B_path.png"
    IM.save(p)
    return p


if __name__ == "__main__":
    for p in (fig_ipv4_structure(), fig_path()):
        print(f"WROTE {p}  {p.stat().st_size/1024:.1f} KB")
