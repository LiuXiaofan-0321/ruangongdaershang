# -*- coding: utf-8 -*-
"""make_diagrams.py (Lab5) - draw the two original analytical diagrams from facts.json.

1. fig_udp_message_structure.png : Turn-in ① - observed UDP message structure
   showing Ethernet II (WLAN) / IPv4 header (Protocol=17) / UDP header (4 fields,
   8 B) / UDP payload, plus zoomed UDP header and byte-verified comparison of
   Frame 10 (WLAN NTP) and Frame 7 (singbox_tun DNS).
2. fig_udp_traffic_analysis.png  : UDP length distribution histogram, application
   protocol breakdown, and checksum/multicast summary across all 393 frames.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab5_work"
EV = WORK / "evidence"
F = json.loads((WORK / "facts.json").read_text(encoding="utf-8"))

INK = (30, 38, 48)
GREY = (102, 112, 124)
RULE = (172, 184, 198)
BG_HEAD = (232, 238, 245)
ETH_BG = (235, 238, 242)
IP_BG = (224, 236, 250)
UDP_BG = (254, 238, 212)
PAY_BG = (226, 244, 231)
ACCENT_BLUE = (46, 92, 158)
ACCENT_AMBER = (178, 102, 24)
ACCENT_GREEN = (38, 118, 68)
ACCENT_RED = (188, 56, 56)


def font(size, bold=False):
    paths = (
        [r"C:\Windows\Fonts\msyhbd.ttc", r"C:\Windows\Fonts\msyh.ttc"]
        if bold else
        [r"C:\Windows\Fonts\msyh.ttc", r"C:\Windows\Fonts\simsun.ttc"]
    )
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def text(d, xy, s, size=18, bold=False, fill=INK, anchor="la"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def span(d, x0, x1, y, label, col=INK, above=False, size=17):
    d.line((x0, y, x1, y), fill=col, width=3)
    d.line((x0, y - 9, x0, y + 9), fill=col, width=3)
    d.line((x1, y - 9, x1, y + 9), fill=col, width=3)
    if above:
        text(d, ((x0 + x1) // 2, y - 14), label, size=size, bold=True, fill=col, anchor="md")
    else:
        text(d, ((x0 + x1) // 2, y + 12), label, size=size, bold=True, fill=col, anchor="ma")


# --------------------------------------------------------------------------
def fig_udp_message_structure():
    W, H = 1760, 1120
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)

    f10 = F["key_frames"]["10"]["b"]
    f7 = F["key_frames"]["7"]["b"]

    text(d, (W // 2, 34),
         "UDP 报文结构与层级封装（依据 Lab5_UDP.pcapng 第 10、7 帧实测绘制，非软件截图）",
         size=29, bold=True, anchor="ma")
    text(d, (W // 2, 78),
         "上栏按第 10 帧（WLAN · NTP，共 90 B）字节等比绘制；中栏展开 8 B UDP 首部四字段；下表对比两帧实测值",
         size=17, fill=GREY, anchor="ma")

    # ---- Top bar: 90 bytes proportional (17 px per byte -> 1530 px wide) ----
    SCALE = 17
    LEFT = (W - 90 * SCALE) // 2
    TOP = 152
    BAR_H = 74

    # Byte ruler
    for b in (0, 14, 34, 42, 90):
        xx = LEFT + b * SCALE
        d.line((xx, TOP - 8, xx, TOP), fill=GREY, width=2)
        text(d, (xx, TOP - 14), str(b), size=14, fill=GREY, anchor="md")
    text(d, (LEFT - 10, TOP - 14), "帧字节", size=14, fill=GREY, anchor="rd")

    blocks = [
        (0, 14, "Ethernet II 首部\n14 B", ETH_BG, INK),
        (14, 20, "IPv4 首部\n20 B", IP_BG, ACCENT_BLUE),
        (34, 8, "UDP 首部\n8 B", UDP_BG, ACCENT_AMBER),
        (42, 48, f"UDP 有效载荷（NTP 报文）\n{f10['udp_payload_len']} B", PAY_BG, ACCENT_GREEN),
    ]
    for b0, ln, lbl, bg, col in blocks:
        x0 = LEFT + b0 * SCALE
        x1 = LEFT + (b0 + ln) * SCALE
        d.rectangle((x0, TOP, x1, TOP + BAR_H), fill=bg, outline=RULE, width=2)
        lines = lbl.split("\n")
        text(d, ((x0 + x1) // 2, TOP + BAR_H // 2 - 12), lines[0], size=16, bold=True, fill=col, anchor="mm")
        text(d, ((x0 + x1) // 2, TOP + BAR_H // 2 + 13), lines[1], size=15, fill=col, anchor="mm")

    # Subtle bottom strip on byte 23 (IP+9: Proto=17) so it never collides with "IPv4 首部 20 B"
    px0 = LEFT + 23 * SCALE
    px1 = LEFT + 24 * SCALE
    d.rectangle((px0, TOP + BAR_H - 10, px1, TOP + BAR_H), fill=ACCENT_RED, outline=ACCENT_RED)
    d.line(((px0 + px1) // 2, TOP, (px0 + px1) // 2, TOP - 26), fill=ACCENT_RED, width=2)
    text(d, ((px0 + px1) // 2, TOP - 30), "第 23 B (IP+9): Protocol = 17 (0x11)",
         size=14, bold=True, fill=ACCENT_RED, anchor="md")

    # Span brackets below top bar
    span(d, LEFT + 34 * SCALE, LEFT + 90 * SCALE, TOP + BAR_H + 22,
         f"UDP Length = {f10['udp_length']} B（UDP 首部 8 B + UDP 载荷 {f10['udp_payload_len']} B，不含 IP/以太网首部）",
         col=ACCENT_AMBER, size=16)
    span(d, LEFT + 14 * SCALE, LEFT + 90 * SCALE, TOP + BAR_H + 74,
         f"IP Total Length = {f10['ip_total_len']} B（IP 首部 20 B + UDP {f10['udp_length']} B）",
         col=ACCENT_BLUE, size=16)
    span(d, LEFT, LEFT + 90 * SCALE, TOP + BAR_H + 126,
         f"Ethernet II 帧长 = {f10['frame_len']} B（含 14 B 以太网首部；第 7 帧走 TUN 虚拟接口无此 14 B）",
         col=INK, size=16)

    # ---- Middle section: Zoomed UDP Header (8 B) + Payload ----
    Z_TOP = 468
    Z_H = 104
    Z_LEFT = 115
    Z_W = W - 2 * Z_LEFT
    hdr_total_w = 1060
    pay_w = Z_W - hdr_total_w
    fw = hdr_total_w // 4

    text(d, (Z_LEFT, Z_TOP - 16), "▼ UDP 首部放大视图（固定 8 字节 = 4 × 16 位字段）",
         size=18, bold=True, fill=ACCENT_AMBER, anchor="lb")

    udp_fields = [
        ("源端口 Source Port", "偏移 0–1 (2 B / 16 bit)", f"第 10 帧: {f10['udp_src_port']}"),
        ("目的端口 Destination Port", "偏移 2–3 (2 B / 16 bit)", f"第 10 帧: {f10['udp_dst_port']} (NTP)"),
        ("长度 Length", "偏移 4–5 (2 B / 16 bit)", f"第 10 帧: {f10['udp_length']} B"),
        ("校验和 Checksum", "偏移 6–7 (2 B / 16 bit)", f"第 10 帧: {f10['udp_checksum']}"),
    ]
    for i, (name, sz, val) in enumerate(udp_fields):
        x0 = Z_LEFT + i * fw
        x1 = x0 + fw
        d.rectangle((x0, Z_TOP, x1, Z_TOP + Z_H), fill=UDP_BG, outline=ACCENT_AMBER, width=2)
        text(d, ((x0 + x1) // 2, Z_TOP + 22), name, size=16, bold=True, anchor="mm")
        text(d, ((x0 + x1) // 2, Z_TOP + 52), sz, size=14, fill=GREY, anchor="mm")
        text(d, ((x0 + x1) // 2, Z_TOP + 82), val, size=15, bold=True, fill=ACCENT_AMBER, anchor="mm")

    # Payload block to the right
    px_start = Z_LEFT + hdr_total_w
    d.rectangle((px_start, Z_TOP, Z_LEFT + Z_W, Z_TOP + Z_H), fill=PAY_BG, outline=ACCENT_GREEN, width=2)
    text(d, (px_start + pay_w // 2, Z_TOP + 26), "UDP 有效载荷 (UDP Payload)",
         size=17, bold=True, fill=ACCENT_GREEN, anchor="mm")
    text(d, (px_start + pay_w // 2, Z_TOP + 56), "偏移 8 起，长度 = Length - 8",
         size=15, fill=GREY, anchor="mm")
    text(d, (px_start + pay_w // 2, Z_TOP + 84),
         f"第 10 帧: {f10['udp_payload_len']} B (NTP) · 第 7 帧: {f7['udp_payload_len']} B (DNS)",
         size=15, bold=True, fill=ACCENT_GREEN, anchor="mm")

    # ---- Bottom table: exact byte comparison ----
    TY = 608
    TW = Z_W
    cols = [300, 175, 165, 445, TW - 300 - 175 - 165 - 445]
    xs = [Z_LEFT]
    for c in cols[:-1]:
        xs.append(xs[-1] + c)

    heads = ["层级 / 字段", "偏移范围", "字段宽度", "第 10 帧实测 (WLAN · NTP)", "第 7 帧实测 (TUN · DNS)"]
    HH = 44
    d.rectangle((Z_LEFT, TY, Z_LEFT + TW, TY + HH), fill=BG_HEAD, outline=RULE, width=2)
    for i, h in enumerate(heads):
        text(d, (xs[i] + cols[i] // 2, TY + HH // 2), h, size=16, bold=True, anchor="mm")

    rows = [
        ("链路层首部", "帧头 0–13", "14 B / 0 B",
         f"Ethernet II 14 B (type {f10['eth_type']})", "Raw IP 0 B（虚拟 TUN 无以太网头）"),
        ("IPv4 首部 (Proto)", "IP 0–19 (9)", "20 B (1 B)",
         f"Total {f10['ip_total_len']} B, Proto = {f10['ip_proto']} (0x11)",
         f"Total {f7['ip_total_len']} B, Proto = {f7['ip_proto']} (0x11)"),
        ("UDP Source Port", "UDP 0–1", "2 B (16 bit)",
         f"{f10['udp_src_port']} (0x{f10['udp_src_port']:04x})",
         f"{f7['udp_src_port']} (0x{f7['udp_src_port']:04x})"),
        ("UDP Destination Port", "UDP 2–3", "2 B (16 bit)",
         f"{f10['udp_dst_port']} (0x{f10['udp_dst_port']:04x}, NTP)",
         f"{f7['udp_dst_port']} (0x{f7['udp_dst_port']:04x}, DNS)"),
        ("UDP Length", "UDP 4–5", "2 B (16 bit)",
         f"{f10['udp_length']} B (8 B 头 + {f10['udp_payload_len']} B 载荷)",
         f"{f7['udp_length']} B (8 B 头 + {f7['udp_payload_len']} B 载荷)"),
        ("UDP Checksum", "UDP 6–7", "2 B (16 bit)",
         f"{f10['udp_checksum']} (RFC 768 验算={f10['udp_checksum_computed']})",
         f"{f7['udp_checksum']} (RFC 768 验算={f7['udp_checksum_computed']})"),
        ("UDP 有效载荷", "UDP 8 起", "Length - 8",
         f"{f10['udp_payload_len']} B (NTP Client 报文)",
         f"{f7['udp_payload_len']} B (DNS 标准查询 www.baidu.com)"),
    ]
    RH = 46
    for ri, r in enumerate(rows):
        y = TY + HH + ri * RH
        bg = (247, 249, 252) if ri % 2 == 1 else "white"
        d.rectangle((Z_LEFT, y, Z_LEFT + TW, y + RH), fill=bg, outline=RULE, width=1)
        for ci, val in enumerate(r):
            d.rectangle((xs[ci], y, xs[ci] + cols[ci], y + RH), outline=RULE, width=1)
            if ci in (1, 2):
                text(d, (xs[ci] + cols[ci] // 2, y + RH // 2), val, size=15, anchor="mm")
            else:
                text(d, (xs[ci] + 12, y + RH // 2), val, size=15, bold=(ci == 0), anchor="lm")

    text(d, (Z_LEFT, TY + HH + len(rows) * RH + 24),
         "注：本图所有数值由 analyze.py 从 Lab5_UDP.pcapng 原始字节直接解析并经 RFC 768 伪首部校验和验算确认；"
         "接收方向第 8 帧（TUN）校验和为 0x0000（未计算）。",
         size=15, fill=GREY, anchor="la")

    out = EV / "fig_udp_message_structure.png"
    im.save(out)
    print("wrote", out, im.size)


# --------------------------------------------------------------------------
def fig_udp_traffic_analysis():
    W, H = 1760, 960
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)

    ls = F["udp_length_stats"]
    bins = ls["bins"]
    protos = F["protocols"]
    ck = F["checksum"]
    n_total = F["frame_count"]

    text(d, (W // 2, 34),
         f"UDP 迹线统计特征：报文长度分布、协议构成与校验和状态（共 {n_total} 帧，非软件截图）",
         size=28, bold=True, anchor="ma")
    text(d, (W // 2, 76),
         f"依据 Lab5_UDP.pcapng（捕获时长 {F['duration_s']} s）全量帧统计绘制；"
         f"Min = {ls['min']} B，Median = {ls['median']} B，P90 = {ls['p90']} B，Max = {ls['max']} B",
         size=17, fill=GREY, anchor="ma")

    # ---- Left card: UDP Length Distribution Bar Chart ----
    LX, LY, LW, LH = 60, 128, 790, 760
    d.rounded_rectangle((LX, LY, LX + LW, LY + LH), radius=12, fill=(250, 251, 253), outline=RULE, width=2)
    text(d, (LX + 28, LY + 24), "一、UDP Length 分布（含 8 B 首部 + 载荷）", size=21, bold=True, fill=ACCENT_BLUE)
    text(d, (LX + 28, LY + 58),
         f"共 {ls['le_400_count']} 帧（{ls['le_400_pct']}%）≤ 400 B；无 > 1500 B 分片报文",
         size=16, fill=GREY)

    # Bar chart geometry inside left card
    chart_x0 = LX + 130
    chart_x1 = LX + LW - 40
    chart_y0 = LY + 120
    chart_y1 = LY + LH - 150
    max_bar_w = chart_x1 - chart_x0 - 130
    max_cnt = max(c for _, c in bins)

    bar_h = 54
    gap = 28
    for i, (lbl, cnt) in enumerate(bins):
        y0 = chart_y0 + i * (bar_h + gap)
        y1 = y0 + bar_h
        pct = 100.0 * cnt / n_total
        bw = int(max_bar_w * cnt / max_cnt) if cnt > 0 else 4
        col = ACCENT_AMBER if "513" in lbl else (ACCENT_BLUE if cnt > 0 else RULE)
        fill_col = (249, 217, 175) if "513" in lbl else ((196, 219, 245) if cnt > 0 else (235, 238, 242))
        text(d, (chart_x0 - 14, (y0 + y1) // 2), lbl, size=16, bold=True, anchor="rm")
        d.rectangle((chart_x0, y0, chart_x0 + bw, y1), fill=fill_col, outline=col, width=2)
        note = f"{cnt} 帧 ({pct:.1f}%)"
        if "513" in lbl:
            note += " [QUIC 1258 B]"
        text(d, (chart_x0 + bw + 12, (y0 + y1) // 2), note, size=16, bold=(cnt > 0), fill=col, anchor="lm")

    # Summary callout box at bottom of left card
    bx0, by0, bx1, by1 = LX + 28, LY + LH - 120, LX + LW - 28, LY + LH - 24
    d.rounded_rectangle((bx0, by0, bx1, by1), radius=8, fill=IP_BG, outline=ACCENT_BLUE, width=1)
    text(d, (bx0 + 18, by0 + 16),
         f"理论上限 vs 实测：UDP Length 为 16 位字段，理论最大 65535 B（载荷 65527 B）；",
         size=15, bold=True, fill=ACCENT_BLUE)
    text(d, (bx0 + 18, by0 + 48),
         f"实测中位数仅 {ls['median']} B，最大 {ls['max']} B（QUIC 主动控长以适配路径 MTU 避免 IP 分片）。",
         size=15, fill=INK)

    # ---- Right Top card: Application Protocols ----
    RX, RY, RW, RH1 = 885, 128, 815, 420
    d.rounded_rectangle((RX, RY, RX + RW, RY + RH1), radius=12, fill=(250, 251, 253), outline=RULE, width=2)
    text(d, (RX + 28, RY + 24), "二、应用层协议构成（Wireshark 按端口识别）", size=21, bold=True, fill=ACCENT_GREEN)

    proto_meta = [
        ("DNS", "端口 53", ACCENT_BLUE, (196, 219, 245)),
        ("UDP", "未注册/通用端口 (80 等)", GREY, (226, 232, 238)),
        ("QUIC", "端口 443 (HTTP/3)", ACCENT_AMBER, (249, 217, 175)),
        ("MDNS", "端口 5353 (组播 224.0.0.251)", ACCENT_GREEN, (198, 234, 208)),
        ("NTP", "端口 123 (时间同步)", (120, 74, 158), (229, 216, 242)),
    ]
    px0 = RX + 115
    pmax_w = RW - 430
    pmax_c = max(protos.values())
    pbh = 40
    pgap = 22
    for i, (pname, pdesc, col, fcol) in enumerate(proto_meta):
        cnt = protos[pname]
        pstat = ls["by_protocol"][pname]
        y0 = RY + 84 + i * (pbh + pgap)
        y1 = y0 + pbh
        bw = max(14, int(pmax_w * cnt / pmax_c))
        text(d, (px0 - 12, (y0 + y1) // 2), pname, size=17, bold=True, fill=col, anchor="rm")
        d.rectangle((px0, y0, px0 + bw, y1), fill=fcol, outline=col, width=2)
        lbl = f"{cnt} 帧 ({100*cnt/n_total:.1f}%) · {pdesc} · {pstat['min']}–{pstat['max']} B"
        text(d, (px0 + bw + 12, (y0 + y1) // 2), lbl, size=15, fill=INK, anchor="lm")

    # ---- Right Bottom card: Checksum & Addressing ----
    RY2, RH2 = RY + RH1 + 26, LH - RH1 - 26
    d.rounded_rectangle((RX, RY2, RX + RW, RY2 + RH2), radius=12, fill=(250, 251, 253), outline=RULE, width=2)
    text(d, (RX + 28, RY2 + 24), "三、校验和与寻址实测特征", size=21, bold=True, fill=ACCENT_RED)

    items = [
        ("接口分布", f"singbox_tun {F['interfaces']['singbox_tun']} 帧 (Raw IP) · WLAN {F['interfaces']['WLAN']} 帧 (Ethernet II)"),
        ("IP 协议号", f"全部 {n_total} 帧 IPv4 Protocol 字段均为 17 (0x11)"),
        ("零校验和", f"{ck['zero_total']} 帧 (43.5%) Checksum = 0x0000，全部为 TUN 接收方向注入报文"),
        ("非零校验和", f"{ck['nonzero_total']} 帧 (56.5%) 含完整校验和；WLAN 上 28 帧均非零且验算通过"),
        ("组播地址", f"mDNS 目的 IP = {F['addressing']['multicast_dst_ip']}（{F['addressing']['multicast_count']} 帧，MAC 01:00:5e:00:00:fb）"),
        ("双非本机帧", f"筛选双端均非本机 IP 得 {F['addressing']['both_non_host_count']} 帧（无混杂模式且无线局域网未收到他机广播）"),
    ]
    for i, (k, v) in enumerate(items):
        yy = RY2 + 74 + i * 38
        text(d, (RX + 28, yy), k + "：", size=16, bold=True, fill=INK)
        text(d, (RX + 148, yy), v, size=15, fill=GREY)

    text(d, (LX, LY + LH + 22),
         "注：全部统计由 analyze.py 结合 tshark 字段导出与原始字节解析生成，写入 facts.json。",
         size=15, fill=GREY)

    out = EV / "fig_udp_traffic_analysis.png"
    im.save(out)
    print("wrote", out, im.size)


if __name__ == "__main__":
    EV.mkdir(parents=True, exist_ok=True)
    fig_udp_message_structure()
    fig_udp_traffic_analysis()
