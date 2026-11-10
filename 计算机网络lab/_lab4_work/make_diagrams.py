# -*- coding: utf-8 -*-
"""make_diagrams.py (Lab4) - draw the two original figures for the ARP report.

fig_arp_exchange.png : the ARP request/reply exchange (Turn-in Step 3 / Q1), with
                       sender/target MAC and IP for each packet and the sought-after
                       Ethernet address circled.
fig_arp_header.png   : the 28-byte ARP message laid out byte-proportionally, with
                       offsets and the values actually observed in frames 1 and 6.

Everything is drawn from facts.json, which analyze.py derives from the raw pcapng.
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab4_work"
EV = WORK / "evidence"
F = json.loads((WORK / "facts.json").read_text(encoding="utf-8"))

INK = (34, 40, 49)
GREY = (110, 118, 128)
RULE = (176, 186, 198)
BG_HEAD = (232, 238, 244)
REQ_BG = (232, 240, 250)
REP_BG = (233, 245, 236)
ACCENT_REQ = (52, 96, 158)
ACCENT_REP = (40, 122, 76)
HI = (196, 62, 62)

FONT_PATHS = [
    r"C:\Windows\Fonts\msyh.ttc",
    r"C:\Windows\Fonts\msyhbd.ttc",
    r"C:\Windows\Fonts\simsun.ttc",
    r"C:\Windows\Fonts\times.ttf",
]


def font(size, bold=False):
    names = ([r"C:\Windows\Fonts\msyhbd.ttc"] if bold else []) + FONT_PATHS
    for p in names:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def text(d, xy, s, size=20, bold=False, fill=INK, anchor="la"):
    d.text(xy, s, font=font(size, bold), fill=fill, anchor=anchor)


def box(d, xy, fill=None, outline=RULE, width=2, radius=8):
    d.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


# --------------------------------------------------------------------------
def fig_exchange():
    W, H = 1700, 1040
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)

    text(d, (W // 2, 44), "ARP 请求与应答：本机解析默认网关的以太网地址",
         size=32, bold=True, anchor="ma")
    text(d, (W // 2, 90),
         f"依据 Lab4_ARP.pcapng 第 {F['request_frame']}、{F['reply_frame']} 帧实测绘制"
         "（非软件截图）", size=19, fill=GREY, anchor="ma")

    # ---- the two hosts ----
    L_X, R_X = 310, W - 310
    NODE_W, NODE_H = 330, 130
    NODE_Y = 170

    for cx, title, lines, accent in (
        (L_X, "本机（WLAN）", ["IP  172.31.240.50", "MAC 14:ac:60:56:df:85"], ACCENT_REQ),
        (R_X, "默认网关（路由器）", ["IP  172.31.0.1", "MAC 54:c6:ff:7b:38:02"], ACCENT_REP),
    ):
        box(d, (cx - NODE_W // 2, NODE_Y, cx + NODE_W // 2, NODE_Y + NODE_H),
            fill=BG_HEAD, outline=accent, width=3)
        text(d, (cx, NODE_Y + 24), title, size=23, bold=True, anchor="ma", fill=accent)
        for i, ln in enumerate(lines):
            text(d, (cx, NODE_Y + 60 + i * 30), ln, size=19, anchor="ma")

    # lifelines
    for cx in (L_X, R_X):
        d.line((cx, NODE_Y + NODE_H, cx, 640), fill=(206, 214, 224), width=3)

    # ---- request arrow ----
    y1 = 392
    d.line((L_X, y1, R_X, y1), fill=ACCENT_REQ, width=4)
    d.polygon([(R_X, y1), (R_X - 26, y1 - 11), (R_X - 26, y1 + 11)], fill=ACCENT_REQ)
    text(d, ((L_X + R_X) // 2, y1 - 44),
         "① ARP 请求（广播）  以太网目的 = ff:ff:ff:ff:ff:ff",
         size=21, bold=True, anchor="ma", fill=ACCENT_REQ)
    text(d, (L_X + 14, y1 + 14), f"第 {F['request_frame']} 帧 · opcode = 1 · "
         f"{F['frame_lengths']['request']} B", size=18, fill=GREY)

    # ---- reply arrow ----
    y2 = 556
    d.line((R_X, y2, L_X, y2), fill=ACCENT_REP, width=4)
    d.polygon([(L_X, y2), (L_X + 26, y2 - 11), (L_X + 26, y2 + 11)], fill=ACCENT_REP)
    text(d, ((L_X + R_X) // 2, y2 + 18),
         "② ARP 应答（单播）  以太网目的 = 14:ac:60:56:df:85",
         size=21, bold=True, anchor="ma", fill=ACCENT_REP)
    text(d, (R_X - 14, y2 - 42), f"第 {F['reply_frame']} 帧 · opcode = 2 · "
         f"{F['frame_lengths']['reply']} B", size=18, fill=GREY, anchor="ra")

    # ---- field cards ----
    CARD_W, CARD_H, CARD_Y = 570, 214, 660

    def card(x0, title, rows, accent, bg, circle_last=False):
        y0 = CARD_Y
        box(d, (x0, y0, x0 + CARD_W, y0 + CARD_H), fill=bg, outline=accent, width=3)
        text(d, (x0 + 20, y0 + 14), title, size=20, bold=True, fill=accent)
        yy = y0 + 58
        for name, val in rows:
            text(d, (x0 + 20, yy), name, size=18, fill=GREY)
            text(d, (x0 + CARD_W - 20, yy), val, size=18, bold=True, anchor="ra")
            if circle_last and name == "发送方 MAC":
                tw = d.textlength(val, font=font(18, True))
                d.ellipse((x0 + CARD_W - 26 - tw, yy - 8, x0 + CARD_W - 8, yy + 28),
                          outline=HI, width=3)
            yy += 36

    rb, pb = F["request"]["b"], F["reply"]["b"]
    card(70, "请求报文中的四项地址", [
        ("发送方 MAC", rb["sha"]),
        ("发送方 IP", rb["spa"]),
        ("目标 MAC", rb["tha"] + "（未知，填零）"),
        ("目标 IP", rb["tpa"]),
    ], ACCENT_REQ, REQ_BG)

    card(W - 70 - CARD_W, "应答报文中的四项地址", [
        ("发送方 MAC", pb["sha"]),
        ("发送方 IP", pb["spa"]),
        ("目标 MAC", pb["tha"]),
        ("目标 IP", pb["tpa"]),
    ], ACCENT_REP, REP_BG, circle_last=True)

    # notes
    text(d, (W // 2, 906),
         "红色椭圆圈出的是本机原本不知道、由这条应答学到的网关以太网地址；"
         "它在请求里对应“目标 MAC”，取值为全零。",
         size=18, fill=HI, anchor="ma")
    text(d, (W // 2, 942),
         "请求中“目标 MAC”为零，表示发送方尚不知道该地址；网关在应答中把自己的 MAC 填进"
         "“发送方 MAC”，本机据此学习到映射。",
         size=18, fill=GREY, anchor="ma")
    text(d, (W // 2, 974),
         "以太网目的地址与 ARP 目标 MAC 是两个层次的不同字段，不可混为一谈。",
         size=18, fill=GREY, anchor="ma")

    out = EV / "fig_arp_exchange.png"
    im.save(out)
    print("wrote", out, im.size)


# --------------------------------------------------------------------------
def _vlabel(im, cx, top, s, size=15, color=INK, bold=True):
    """Draw `s` rotated 90° (reading bottom-to-top) centred on cx, starting at top."""
    f = font(size, bold)
    probe = ImageDraw.Draw(Image.new("RGB", (8, 8)))
    tw = int(probe.textlength(s, font=f)) + 12
    th = size + 12
    tmp = Image.new("RGBA", (tw, th), (0, 0, 0, 0))
    ImageDraw.Draw(tmp).text((6, 4), s, font=f, fill=color)
    rot = tmp.rotate(90, expand=True)
    im.paste(rot, (int(cx - rot.width / 2), int(top)), rot)
    return rot.height


def fig_header():
    FIELDS = [
        ("硬件类型", "0x0001", 0, 2),
        ("协议类型", "0x0800", 2, 2),
        ("硬件地址\n长度", "6", 4, 1),
        ("协议地址\n长度", "4", 5, 1),
        ("操作码", "1 / 2", 6, 2),
        ("发送方 MAC", "14:ac:…:df:85", 8, 6),
        ("发送方 IP", "172.31.240.50", 14, 4),
        ("目标 MAC", "00:00:…:00:00", 18, 6),
        ("目标 IP", "172.31.0.1", 24, 4),
    ]

    CELL = 44
    LEFT = 44
    TOP = 214
    BAR = 74
    W = LEFT * 2 + 28 * CELL
    H = 1000
    im = Image.new("RGB", (W, H), "white")
    d = ImageDraw.Draw(im)

    text(d, (W // 2, 40), "ARP 报文结构（共 28 B，位于以太网帧 14 B 首部之后）",
         size=30, bold=True, anchor="ma")
    text(d, (W // 2, 84),
         "字节按比例绘制；竖排为字段名，格内为本次实测取值"
         "（39 字符号处为省略，完整值见下表）", size=17, fill=GREY, anchor="ma")

    # byte ruler
    for i in range(0, 28, 2):
        text(d, (LEFT + i * CELL + CELL, TOP - 26), str(i), size=15, fill=GREY, anchor="ma")

    shades = [(238, 242, 247), (226, 233, 241)]
    for idx, (cn, val, off, ln) in enumerate(FIELDS):
        x0 = LEFT + off * CELL
        x1 = x0 + ln * CELL
        shade = (250, 234, 234) if cn == "目标 MAC" else shades[idx % 2]
        d.rectangle((x0, TOP, x1, TOP + BAR), fill=shade, outline=RULE, width=2)
        # value: only where it fits, else omit (table carries it)
        if ln * CELL >= 110:
            text(d, ((x0 + x1) // 2, TOP + BAR // 2), val, size=15, bold=True,
                 anchor="mm")
        rng = f"{off}–{off + ln - 1}" if ln > 1 else str(off)
        text(d, ((x0 + x1) // 2, TOP + BAR - 14), rng, size=13, fill=GREY, anchor="ma")
        # vertical field name
        _vlabel(im, (x0 + x1) // 2, TOP + BAR + 10, cn.replace("\n", ""), size=15)

    # total length bracket
    ay = TOP + BAR + 132
    d.line((LEFT, ay, LEFT + 28 * CELL, ay), fill=GREY, width=2)
    for xx in (LEFT, LEFT + 28 * CELL):
        d.line((xx, ay - 7, xx, ay + 7), fill=GREY, width=2)
    text(d, (LEFT + 14 * CELL, ay + 8), "ARP 报文 28 B", size=18, bold=True,
         anchor="ma", fill=GREY)

    # ---- table ----
    ty = ay + 56
    TW = W - 2 * LEFT
    cols = [110, 76, 210, TW - 110 - 76 - 210]
    xs = [LEFT]
    for c in cols[:-1]:
        xs.append(xs[-1] + c)

    def cell(x, y, w, h, s, bold=False, size=16, fill=INK, center=True):
        d.rectangle((x, y, x + w, y + h), outline=RULE, width=1)
        if center:
            text(d, (x + w // 2, y + h // 2), s, size=size, bold=bold, fill=fill,
                 anchor="mm")
        else:
            text(d, (x + 12, y + h // 2), s, size=size, bold=bold, fill=fill,
                 anchor="lm")

    heads = ["字节偏移", "长度", "字段", "实测取值（请求 / 应答）"]
    hh = 42
    d.rectangle((xs[0], ty, xs[0] + TW, ty + hh), fill=BG_HEAD, outline=RULE, width=1)
    for i, h in enumerate(heads):
        text(d, (xs[i] + cols[i] // 2, ty + hh // 2), h, size=17, bold=True, anchor="mm")

    rows = [
        ("0–1", "2", "硬件类型", "0x0001 / 0x0001"),
        ("2–3", "2", "协议类型", "0x0800 / 0x0800"),
        ("4", "1", "硬件地址长度", "6 / 6"),
        ("5", "1", "协议地址长度", "4 / 4"),
        ("6–7", "2", "操作码", "0x0001（请求）/ 0x0002（应答）"),
        ("8–13", "6", "发送方 MAC", "14:ac:60:56:df:85 / 54:c6:ff:7b:38:02"),
        ("14–17", "4", "发送方 IP", "172.31.240.50 / 172.31.0.1"),
        ("18–23", "6", "目标 MAC", "00:00:00:00:00:00 / 14:ac:60:56:df:85"),
        ("24–27", "4", "目标 IP", "172.31.0.1 / 172.31.240.50"),
    ]
    rh = 38
    for i, r in enumerate(rows):
        y = ty + hh + i * rh
        if i % 2 == 1:
            d.rectangle((xs[0], y, xs[0] + TW, y + rh), fill=(247, 249, 251),
                        outline=None)
        cell(xs[0], y, cols[0], rh, r[0])
        cell(xs[1], y, cols[1], rh, r[1])
        cell(xs[2], y, cols[2], rh, r[2], center=False)
        cell(xs[3], y, cols[3], rh, r[3], center=False)

    out = EV / "fig_arp_header.png"
    im.save(out)
    print("wrote", out, im.size)


if __name__ == "__main__":
    EV.mkdir(parents=True, exist_ok=True)
    fig_exchange()
    fig_header()
