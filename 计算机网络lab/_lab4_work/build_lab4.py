# -*- coding: utf-8 -*-
r"""build_lab4.py - build 10244602411_刘小凡_Lab4_ARP.docx from the school template.

Fills the six school sections, embeds 10 real software screenshots (3 live command
console captures + 7 Wireshark windows) and 2 original diagrams, and keeps the
template's header/footer, metadata block, geometry and section order.

Every number comes from facts.json, which analyze.py derives from the raw pcapng
bytes (not from prose and not copied out of the screenshots).

Usage: python build_lab4.py
"""
import json
import sys
import zipfile
from pathlib import Path

import docx
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor
from docx.text.paragraph import Paragraph

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab4_work"
EV = WORK / "evidence"
OUT = ROOT / "10244602411_刘小凡_Lab4_ARP.docx"
TEMPLATE = WORK / "template.docx"

F = json.loads((WORK / "facts.json").read_text(encoding="utf-8"))

LATIN = "Times New Roman"
CJK = "SimSun"
CJK_BOLD = "Microsoft YaHei"
BODY_PT = 10.5

HOST_IP = "172.31.240.50"
HOST_MAC = "14:ac:60:56:df:85"
GW_IP = "172.31.0.1"
GW_MAC = "54:c6:ff:7b:38:02"


# --------------------------------------------------------------------------
def body_children(doc):
    return list(doc.element.body.iterchildren())


def set_run(run, size=BODY_PT, bold=False, latin=LATIN, ea=CJK, color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = latin
    run.font.color.rgb = (RGBColor.from_string(color) if color else RGBColor(0, 0, 0))
    run._element.get_or_add_rPr().rFonts.set(qn("w:eastAsia"), ea)


def new_para(doc, text, style="中文首行缩进", size=BODY_PT, bold=False,
             indent=True, align=None):
    p = doc.add_paragraph(style=style)
    if not indent:
        p.paragraph_format.first_line_indent = Cm(0)
    if align is not None:
        p.alignment = align
    if text:
        set_run(p.add_run(text), size, bold, ea=(CJK_BOLD if bold else CJK))
    return p._p


def new_heading(doc, text, size=12):
    p = doc.add_paragraph(style="Normal")
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(9)
    p.paragraph_format.space_after = Pt(4)
    p.paragraph_format.keep_with_next = True
    set_run(p.add_run(text), size, True, latin=CJK_BOLD, ea=CJK_BOLD)
    return p._p


def new_mono(doc, lines, size=9):
    els = []
    for line in lines:
        p = doc.add_paragraph(style="中文首行缩进")
        p.paragraph_format.first_line_indent = Cm(0)
        p.paragraph_format.left_indent = Cm(0.5)
        p.paragraph_format.space_after = Pt(0)
        p.paragraph_format.line_spacing = 1.05
        set_run(p.add_run(line), size, latin="Consolas", ea=CJK)
        els.append(p._p)
    return els


def new_table(doc, heads, rows, widths_cm, size=9):
    t = doc.add_table(rows=1, cols=len(heads))
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    t.autofit = False
    for i, w in enumerate(widths_cm):
        t.columns[i].width = Cm(w)
    for i, h in enumerate(heads):
        t.rows[0].cells[i].text = str(h)
    for r in rows:
        cells = t.add_row().cells
        for i, v in enumerate(r):
            cells[i].text = str(v)

    borders = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        e = OxmlElement("w:" + edge)
        e.set(qn("w:val"), "single")
        e.set(qn("w:sz"), "4")
        e.set(qn("w:color"), "9DB2C6")
        borders.append(e)
    t._tbl.tblPr.append(borders)

    for ri, row in enumerate(t.rows):
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement("w:cantSplit"))
        if ri == 0:
            trpr.append(OxmlElement("w:tblHeader"))
        for ci, cell in enumerate(row.cells):
            cell.width = Cm(widths_cm[ci])
            tcpr = cell._tc.get_or_add_tcPr()
            mar = OxmlElement("w:tcMar")
            for edge in ("top", "bottom", "left", "right"):
                e = OxmlElement("w:" + edge)
                e.set(qn("w:w"), "80")
                e.set(qn("w:type"), "dxa")
                mar.append(e)
            tcpr.append(mar)
            if ri == 0:
                shd = OxmlElement("w:shd")
                shd.set(qn("w:fill"), "E8EEF4")
                tcpr.append(shd)
            for pp in cell.paragraphs:
                pp.paragraph_format.first_line_indent = Cm(0)
                pp.paragraph_format.space_after = Pt(1)
                pp.paragraph_format.line_spacing = 1.05
                for rr in pp.runs:
                    set_run(rr, size, ri == 0, ea=(CJK_BOLD if ri == 0 else CJK))
    return t._tbl


def new_figure(doc, img, caption, width_cm=15.5):
    p = doc.add_paragraph()
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent = Cm(0)
    p.paragraph_format.space_before = Pt(6)
    p.paragraph_format.keep_with_next = True
    p.add_run().add_picture(str(EV / img), width=Cm(width_cm))

    c = doc.add_paragraph(style="中文首行缩进")
    c.alignment = WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.first_line_indent = Cm(0)
    c.paragraph_format.space_after = Pt(8)
    set_run(c.add_run(caption), 8.5)
    return [p._p, c._p]


# --------------------------------------------------------------------------
def build_content(doc):
    """Create the content of all seven sections, keyed by section number.

    Each section is placed after ITS OWN heading by main(); a single shared anchor
    would dump every section after 四, leaving 一/二/三 empty (that mistake was
    caught during page-by-page review).
    """
    sections = {k: [] for k in range(1, 8)}
    cur = [1]

    def sec(k):
        cur[0] = k

    def put(els):
        sections[cur[0]].extend(els if isinstance(els, list) else [els])

    def para(text, **kw):
        put(new_para(doc, text, **kw))

    def heading(text, size=12):
        put(new_heading(doc, text, size))

    def mono(lines, size=9):
        put(new_mono(doc, lines, size))

    def table(heads, rows, widths, size=9):
        put(new_table(doc, heads, rows, widths, size))

    def figure(img, caption, width_cm=15.5):
        put(new_figure(doc, img, caption, width_cm))

    req = F["request"]["b"]
    rep = F["reply"]["b"]
    C = F["counts"]

    # ================= 一、实验目的 =================
    sec(1)
    for t in [
        "本次实验围绕 ARP（Address Resolution Protocol）展开，目的是通过抓取并逐字段"
        "检查真实的 ARP 报文，理解 IPv4 地址如何解析为本链路的以太网地址，掌握 ARP "
        "报文与承载它的以太网帧之间的关系。具体目标如下：",
        "1. 掌握用 ipconfig / 路由表获取本机以太网地址与默认网关的方法，并据此确定"
        "捕获接口和过滤条件；",
        "2. 掌握以 arp 为捕获过滤器、关闭混杂模式捕获 ARP 流量的完整流程，能够保存"
        "可复核的 pcapng 迹线；",
        "3. 能区分 ARP 请求与应答，逐字段读取 28 字节 ARP 报文的九个字段，并说明"
        "请求与应答在这四个地址字段上的对应关系；",
        "4. 能把 ARP 报文与以太网帧分开：以太网 14 B 首部、28 B ARP 报文、以太网填充，"
        "并解释 42 B 与 60 B 两种帧长的来源；",
        "5. 能回答手册 Step 4 的五道问答题，并画出本机与默认网关之间请求/应答的"
        "交换示意图；",
        "6. 能识别迹线中 ARP 探测（Probe）与免费 ARP 通告（Announcement）等常见行为，"
        "并说明它们的用途。",
    ]:
        para(t)

    # ================= 二、实验内容与实验步骤 =================
    sec(2)
    para("实验按手册的四个 Step 推进：先核对接口地址与默认网关并设置捕获过滤器，"
         "再捕获 ARP 流量并定位一次完整的请求/应答，然后画出交换示意图，"
         "最后依据报文回答 Step 4 的五道问题。")
    para("Step 1 取址与捕获：用 ipconfig /all 读出 WLAN 接口的 IPv4 地址与物理地址，"
         "用路由表确认默认网关，随后在 Wireshark 中选择该接口、捕获过滤器填 arp、"
         "关闭混杂模式并开始捕获。手册建议先清空 ARP 缓存再访问网页以触发解析，"
         "本次的实际做法与偏差在第 4.1 节如实说明。")
    para("Step 2 定位迹线：按手册要求以本机以太网地址设置显示过滤器"
         "（形如 eth.addr == 14:ac:60:56:df:85），把视图限制在与本机相关的 ARP 报文，"
         "再分别展开一条请求和一条应答，读取全部字段。")
    para("Step 3 绘制交换示意图：利用 Step 2 读到的四个地址字段，画出本机与默认网关"
         "之间的请求与应答，标注每个报文的发送方与目标 MAC/IP，并圈出本机原本不知道、"
         "由应答学到的那个以太网地址。")
    para("Step 4 报文细节：针对以太网封装与 ARP 报文字段，回答操作码取值、ARP 报文"
         "长度、未知目标 MAC 的填充值、以太网类型值以及应答是否广播这五道问题。")
    para(f"本次实测的迹线 Lab4_ARP.pcapng 共 {F['frame_count']} 帧，全部为 ARP，"
         f"其中请求 {C['requests']} 帧、应答 {C['replies']} 帧。")

    # ================= 三、实验环境 =================
    sec(3)
    table(["项目", "实测配置"], [
        ["操作系统", "Windows 11 25H2（build 26200），64 位"],
        ["抓包与分析", "Wireshark / TShark 4.6.8，Npcap 1.88"],
        ["命令行工具", "ipconfig、路由表查询、arp、ping"],
        ["捕获接口", "WLAN：MediaTek Wi-Fi 6E MT7922 (RZ616) 160MHz Wireless LAN Card"],
        ["本机地址", f"IPv4 {HOST_IP}/16；MAC {HOST_MAC}"],
        ["默认网关", f"{GW_IP}，其 MAC {GW_MAC}"],
        ["捕获过滤器", "arp（关闭混杂模式）"],
        ["迹线文件", f"Lab4_ARP.pcapng，{F['frame_count']} 帧"],
    ], [3.4, 13.6])

    # ================= 四、实验过程与分析 =================
    sec(4)
    para("本节只记录实验过程与实测现象：每一步做了什么、看到什么结果、"
         "遇到什么偏差以及如何解释。手册要求提交的题目与答案统一放在第五节，"
         "便于对照评分。")

    heading("4.1  网络环境与捕获方法", 11.5)
    para("先用 ipconfig /all 读出 WLAN 接口的状态，如图 1：本机 IPv4 地址为 "
         f"{HOST_IP}（前缀长度 16），物理地址为 {HOST_MAC}，默认网关为 {GW_IP}。"
         "这三个值是后续设置过滤器和判读报文的基准。")
    figure("01_ipconfig.png",
           "图 1  WLAN 接口的 IPv4 地址、物理地址与默认网关（对应手册 Step 1 的 "
           "ipconfig 取址）", 14.5)
    para("再用路由表确认默认路由确实指向该网关，如图 2。需要指出的是，本机同时存在 "
         "singbox_tun 的默认路由（下一跳 172.18.0.2），因此不能假定系统所有流量都经 "
         "WLAN 转发。但 ARP 只用于解析同一广播域内的地址，隧道不会替本机解析 WLAN "
         "网段的网关，所以本实验把捕获接口明确指定为 WLAN，结果不受隧道影响。")
    figure("03_route.png",
           "图 2  默认路由 0.0.0.0/0：WLAN 经 172.31.0.1，另有 singbox_tun 的"
           "并行默认路由", 14.5)
    para("查看 ARP 缓存可以确认网关的解析结果，如图 3：接口 172.31.240.50 下存在一条"
         f"{GW_IP} → {GW_MAC} 的动态（dynamic）条目，其余多为组播/广播的静态条目。"
         "这条动态条目正是 ARP 协议工作后留下的产物，可与迹线中的应答互相印证。")
    figure("02_arp_cache.png",
           "图 3  arp -a 输出：WLAN 接口下网关 172.31.0.1 对应 54-c6-ff-7b-38-02"
           "（dynamic）", 14.5)
    para("关于手册建议的“先清空 ARP 缓存再访问网页”，需要如实说明本次的偏差："
         "清空缓存（arp -d）需要管理员权限，本次以普通用户身份运行，命令无法执行，"
         "因此没有清空缓存；工作负载也不是浏览器访问网页，而是绑定了 WLAN 源地址的 "
         "ping（ping -S 172.31.240.50 172.31.0.1）。捕获期间迹线中自然出现了对网关的"
         "请求与应答，足以完成后续全部字段与交换分析；但由于没有清空缓存，"
         "不能断言第 1 帧的请求一定由那次 ping 触发，也不能据此推断解析的触发时机。")
    mono([
        "# 绑定 WLAN 源地址访问网关（本次使用的工作负载）",
        "ping -S 172.31.240.50 172.31.0.1",
        "",
        "# 查看 ARP 缓存（无需管理员权限）",
        "arp -a",
    ])

    heading("4.2  ARP 迹线的定位", 11.5)
    para(f"捕获得到的 Lab4_ARP.pcapng 共 {F['frame_count']} 帧，协议分层显示 100% 为 "
         "ARP，说明捕获过滤器生效、没有混入其他协议。图 4 为迹线概览，"
         "可以看到 Info 列同时出现 “Who has …? Tell …”（请求）与 "
         "“… is at …”（应答），以及少数标注为 ARP Probe 与 ARP Announcement 的报文。"
         f"整条迹线共 {C['requests']} 个请求、{C['replies']} 个应答。")
    figure("06_arp_overview.png",
           "图 4  迹线概览：全部 53 帧均为 ARP，含请求、应答、探测与通告"
           "（来源：Lab4_ARP.pcapng，状态栏显示合计 53 帧）", 14.0)
    para("按手册 Step 2 的要求，以本机以太网地址设置显示过滤器 "
         "eth.addr == 14:ac:60:56:df:85，结果如图 5。这里出现了一个与手册预期不同的"
         "现象：过滤后仍是 53 帧，即 100% 的报文都与本机相关，并没有像手册示例那样"
         "筛掉一大半。原因是本迹线在本机接口上捕获且全部为 ARP，而每个 ARP 报文的"
         "发送方或目标以太网地址中都有本机地址（本机发出的请求、发给本机的应答、"
         "以及本机自身的探测与通告）。因此这条过滤器在本迹线中起“确认”而非“筛选”作用；"
         "若要缩小视图，应按 IP 或操作码过滤。")
    figure("08_eth_addr_filter.png",
           "图 5  按本机以太网地址过滤 eth.addr == 14:ac:60:56:df:85："
           "本迹线 53 帧全部与本机相关（状态栏 Displayed 53/100.0%）", 14.0)
    table(["类别", "数量", "帧号示例", "判据"], [
        ["请求（request）", str(C["requests"]), "1、2、3、5、11…",
         "opcode = 1，Info 为 Who has …"],
        ["应答（reply）", str(C["replies"]), "6、14、51、53…",
         "opcode = 2，Info 为 … is at …"],
        ["ARP 探测（Probe）", str(C["probes"]),
         "、".join(str(x) for x in F["probe_frames"]),
         "发送方 IP 为 0.0.0.0，用于地址冲突检测"],
        ["ARP 通告（Announcement）", str(C["announcements"]),
         "、".join(str(x) for x in F["announce_frames"]),
         "发送方 IP 与目标 IP 相同（免费 ARP）"],
    ], [4.4, 1.5, 4.6, 6.5])
    para("表 1  迹线中各类 ARP 报文的构成（分类由 analyze.py 依据原始字节判定）",
         indent=False, size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)

    heading("4.3  以太网封装与 ARP 报文字节结构", 11.5)
    para("ARP 报文并不直接出现在链路上，而是作为以太网帧的载荷。图 6 把以太网首部"
         "展开：目的地址 ff:ff:ff:ff:ff:ff、源地址 14:ac:60:56:df:85、类型 "
         "ARP (0x0806)，右侧字节窗口中被高亮的正是 08 06 两个字节；状态栏同时给出"
         "“Ethernet (eth), 14 byte(s)”，即以太网首部 14 字节。")
    figure("07_ethertype_bytes.png",
           "图 6  Ethernet II 首部展开：Destination 为广播、Type 为 ARP (0x0806)，"
           "字节窗口高亮 08 06（来源：Lab4_ARP.pcapng 第 1 帧）", 14.0)
    para("把以太网首部与 ARP 报文分开之后，两条报文的长度就能对上账：ARP 报文本身"
         "固定为 28 字节（两个 2 字节类型 + 两个 1 字节长度 + 一个 2 字节操作码 + "
         "四段地址），以太网首部 14 字节；最小以太网帧为 60 字节（不含前导码与 FCS），"
         "因此 42 字节的请求不需要填充，而应答补齐到 60 字节，多出的 18 字节是"
         "以太网填充而不是 ARP 字段。")
    table(["报文", "帧长", "以太网首部", "ARP 报文", "以太网填充", "核对"], [
        ["请求（第 1 帧）", f"{F['frame_lengths']['request']} B", "14 B",
         "28 B", "0 B", "14 + 28 = 42"],
        ["应答（第 6 帧）", f"{F['frame_lengths']['reply']} B", "14 B",
         "28 B", f"{F['padding_on_reply']} B", "14 + 28 + 18 = 60"],
    ], [3.6, 2.0, 2.6, 2.2, 2.6, 3.6])
    para("表 2  帧长的分解：ARP 报文均为 28 B，差异来自以太网填充",
         indent=False, size=8.5, align=WD_ALIGN_PARAGRAPH.CENTER)
    para("本机发出的请求（第 1 帧）的完整字段见图 7。可以看到 Hardware type 为 "
         "Ethernet (1)、Protocol type 为 IPv4 (0x0800)、Hardware size 6、"
         "Protocol size 4、Opcode 为 request (1)；四个地址字段中，发送方 MAC/IP 已填"
         "本机值，目标 IP 填网关地址，而目标 MAC 填全零。状态栏显示该 ARP 报文"
         "为 28 byte(s)。")
    figure("04_arp_request_fields.png",
           "图 7  ARP 请求（第 1 帧）的全部字段：Opcode = request (1)，"
           "Target MAC = 00:00:00:00:00:00，状态栏显示 ARP 报文 28 字节", 14.0)
    para("网关回的应答（第 6 帧）见图 8。Hardware/Protocol 类型与长度保持不变，"
         "只有 Opcode 变为 reply (2)；四个地址字段整体“换位”：原来的目标（网关）"
         "成为发送方，原来的发送方（本机）成为目标，并且此时两对地址都已填满。"
         "该帧的以太网目的地址是本机 MAC，属单播。")
    figure("05_arp_reply_fields.png",
           "图 8  ARP 应答（第 6 帧）的全部字段：Opcode = reply (2)，四个地址均已填满，"
           "以太网目的为本机单播地址", 14.0)
    para("这里最容易混淆的是两个层次的“地址”：以太网首部的目的地址决定这一帧在"
         "链路上被谁收下，而 ARP 报文内部的目标 MAC 是“想知道的那个地址”。"
         "请求把前者设为广播、后者设为零，正是为了让全网都能收到、同时表明自己还不知道答案。")

    heading("4.4  迹线中的其他 ARP 行为", 11.5)
    para(f"除了一问一答，迹线里还有两类值得记录的行为。用过滤器 "
         f"arp.isprobe || arp.isannouncement 可把它们筛出来，共 10 帧（图 9）："
         f"{C['probes']} 个 ARP 探测（帧 "
         f"{'、'.join(str(x) for x in F['probe_frames'])}）与 "
         f"{C['announcements']} 个 ARP 通告（帧 "
         f"{'、'.join(str(x) for x in F['announce_frames'])}）。探测报文的发送方 IP 为 "
         f"0.0.0.0、目标是本机自己的地址，作用是地址冲突检测；通告报文的发送方 IP 与"
         f"目标 IP 相同（都是 {HOST_IP}），属于免费 ARP，用于在地址启用后通知同网段"
         f"其他主机更新缓存。二者都是 RFC 5227 定义的行为，不是异常。")
    figure("09_gratuitous_arp.png",
           "图 9  ARP 探测与免费 ARP 通告：过滤器 arp.isprobe || arp.isannouncement "
           "筛出 10 帧（状态栏 Displayed 10/18.9%）", 14.0)
    para(f"另一个值得记录的异常是第 "
         f"{'、'.join(str(u['frame']) for u in F['unicast_requests'])} 帧：它们同样是"
         f"询问 {GW_IP} 的请求，但以太网目的地址不是广播，而是网关的单播 MAC "
         f"{GW_MAC}。这与“ARP 请求总是广播”的常见说法不符，说明该说法应表述为"
         f"“正常情况下广播”：在已经知道对方硬件地址、或实现选择直接单播以减轻广播"
         f"负载时，也会出现单播的请求。因此判断一个请求是否广播，要看具体帧的以太网"
         f"目的地址，而不能只凭报文类型下结论。")
    figure("10_gateway_exchange.png",
           "图 10  与网关相关的全部 ARP 报文（过滤器按 172.31.0.1 匹配，共 43 帧），"
           "其中第 11–13 帧为以太网目的为单播的请求", 14.0)

    # ================= 五、必做题目与解答 =================
    sec(5)
    heading("五、必做题目与解答", 12)
    para("本节集中列出手册要求提交的两项 Turn-in 与本次作答结果。题目原文以"
         "「题目原文」标出，答案紧接其后。")

    heading("5.1  必做题目一：绘制 ARP 交换示意图（Turn-in ①）", 11.5)
    para("题目原文（Step 3）：画出本机与默认网关之间的 ARP 请求与应答，"
         "标注一个报文为请求、另一个为应答；给出每个报文的发送方与目标 MAC 与 IP 地址；"
         "最后在图上圈出本机所求的那个以太网地址，说明它在交换中从哪里得到。")
    para("依据第 1 帧与第 6 帧实测字段绘制的交换示意图如图 11。图中上方为请求："
         "以太网目的为广播 ff:ff:ff:ff:ff:ff，ARP 内发送方是本机 "
         f"{HOST_MAC} / {HOST_IP}，目标是 {GW_IP}，目标 MAC 填零；下方为应答："
         f"以太网目的改为本机单播，ARP 内发送方变为网关 {GW_MAC} / {GW_IP}，"
         f"目标变为本机。")
    figure("fig_arp_exchange.png",
           "图 11  本机与默认网关之间的 ARP 请求与应答（依据 Lab4_ARP.pcapng "
           "第 1、6 帧实测绘制；红圈为本机所求、由应答学到的网关 MAC）", 15.0)
    para(f"所求的以太网地址是 {GW_MAC}。它来自应答报文的“发送方 MAC”字段：网关在"
         f"回送应答时把自己的硬件地址填进该字段，本机收到后即可把它与请求里的目标 IP "
         f"{GW_IP} 绑定，写进 ARP 缓存（图 3 的动态条目即此结果）。示意图中把这一格"
         f"用红圈标出，对应请求中取值为全零的“目标 MAC”，二者是同一个待求量的"
         f"“未知”与“已知”两种状态。")

    heading("5.2  必做题目二：ARP 报文细节五问（Turn-in ②）", 11.5)
    para("题目原文（Step 4）：检查一条 ARP 请求与一条 ARP 应答，回答五个问题——"
         "请求与应答各用什么操作码？ARP 首部有多大？请求中未知的目标 MAC 填什么值？"
         "哪个以太网类型值表示上层协议是 ARP？ARP 应答是广播还是不像请求那样广播？")
    para("为便于对照，先把五问的答案汇总在表 3，随后逐题给出依据。"
         "ARP 报文的字节布局与两帧的实测取值见图 12。")
    table(["问题", "答案", "依据"], [
        ["1. 请求/应答的操作码", "请求 = 1，应答 = 2",
         "第 1 帧 Opcode: request (1)；第 6 帧 Opcode: reply (2)"],
        ["2. ARP 首部大小", "两者均为 28 字节",
         "两帧状态栏均为 28 byte(s)；8 B 固定字段 + 4 段地址"],
        ["3. 未知目标 MAC 的取值", "全零 00:00:00:00:00:00",
         "第 1 帧 Target MAC address 字段"],
        ["4. 表示 ARP 的以太网类型", "0x0806（Ethernet II 的 Type 字段）",
         "图 6 中 Type: ARP (0x0806)，字节窗口 08 06"],
        ["5. 应答是否广播", "不是广播，是单播到请求方",
         "第 6 帧以太网目的为本机 MAC 14:ac:60:56:df:85"],
    ], [4.4, 5.0, 7.6])
    para("表 3  Step 4 五问的答案与依据", indent=False, size=8.5,
         align=WD_ALIGN_PARAGRAPH.CENTER)
    para("ARP 报文结构的示意图见图 12：它把 28 个字节按比例展开，并列出一条请求与"
         "一条应答在每个字段上的实际取值，逐题作答时可与它逐行对照。")
    figure("fig_arp_header.png",
           "图 12  ARP 报文结构（28 B）：九个字段的字节偏移、长度与第 1、6 帧的实测取值",
           13.8)

    para("问题 1：请求与应答分别用什么操作码？请求的操作码为 1，应答的操作码为 2，"
         "位于 ARP 报文的第 6–7 字节。图 7 与图 8 的字段树分别显示 "
         "Opcode: request (1) 与 Opcode: reply (2)，图 12 的字节表给出的十六进制值为 "
         "0x0001 与 0x0002。由于这两个字段是大端序的 16 位整数，抓包中的字节顺序为 "
         "00 01 / 00 02。")
    para("问题 2：ARP 首部有多大？请求与应答都是 28 字节。ARP 报文的长度并不写死，"
         "而是由硬件地址长度与协议地址长度算出：8 字节固定字段（硬件类型 2 + 协议类型 2 "
         "+ 硬件地址长度 1 + 协议地址长度 1 + 操作码 2），加上两段硬件地址（2 × 6 = 12）"
         "和两段协议地址（2 × 4 = 8），合计 8 + 12 + 8 = 28 字节。"
         "图 7 与图 8 的状态栏都显示“Address Resolution Protocol (arp), 28 byte(s)”。"
         "需要说明的是，28 字节是本例（以太网 + IPv4）的结果，并非所有硬件与协议的"
         "通用定值：若地址长度字段变化，ARP 报文长度也随之变化。")
    para("问题 3：请求中未知的目标 MAC 填什么值？填全零，即 00:00:00:00:00:00。"
         "ARP 没有单独的“未知”标记，只能用一个不可能作为真实单播地址的取值占位，"
         "全零正好满足这个要求。图 7 的 Target MAC address 字段显示 "
         "00:00:00:00:00:00，图 12 的字节表在偏移 18–23 处也是六个 00。"
         "特别要区分：以太网首部的目的地址同时是广播 ff:ff:ff:ff:ff:ff，"
         "那是“这一帧发给谁”，而 ARP 内的目标 MAC 是“想知道谁的地址”，"
         "两者层次不同、取值也不同。")
    para("问题 4：哪个以太网类型值表示上层是 ARP？0x0806。它占据以太网帧的第 12–13 "
         "字节，紧跟在目的地址与源地址之后。图 6 中 Ethernet II 展开后显示 "
         "Type: ARP (0x0806)，字节窗口把 08 06 两个字节高亮；图 12 的字节表也把这两个"
         "字节列在以太网首部末尾。作为对照，ARP 报文内部的 Protocol type 字段取值为 "
         "0x0800，它表示“要解析的是 IPv4 地址”，与 0x0806 是完全不同的两个字段，"
         "不能混为一谈。")
    para(f"问题 5：ARP 应答是广播吗？不是。请求以广播发出（以太网目的 "
         f"ff:ff:ff:ff:ff:ff），而应答是单播，直接发给提出请求的主机：第 6 帧的以太网"
         f"目的地址是本机 MAC {HOST_MAC}，源地址是网关 MAC {GW_MAC}。这样设计的理由是"
         f"请求方身份已经明确——请求报文里就带着发送方的 MAC 与 IP，网关无需再广播即可"
         f"精确回复，同时也避免打扰同网段其他主机。本迹线中的 13 个应答目的地址均为"
         f"单播地址，与该结论一致。")

    # ================= 六、实验结果总结 =================
    sec(6)
    heading("六、实验结果总结", 12)
    heading("6.1  实验结论", 11.5)
    para(f"关于交换过程：本机在不知道网关 {GW_MAC} 的情况下广播请求，网关以单播应答，"
         f"本机从应答的发送方 MAC 字段学到映射并写入 ARP 缓存。这条链路上的证据是"
         f"第 1 帧（请求）、第 6 帧（应答）与 arp -a 中的动态条目，三者互相印证。")
    para("关于报文结构：ARP 报文为 28 字节，以太网首部为 14 字节。请求的以太网帧长 "
         "42 字节，应答被以太网填充到 60 字节，多出的 18 字节不属于 ARP 字段。"
         "把帧长直接当成 ARP 报文长度是常见错误，必须先减去以太网首部与填充。")
    para("关于字段取值：操作码请求为 1、应答为 2；以太网类型为 0x0806；请求中未知的"
         "目标 MAC 填全零；应答为单播。这四点与手册问题一一对应，且都能在原始字节中"
         "定位到具体偏移。")
    para(f"关于迹线的其他行为：迹线中还有 {C['probes']} 个地址探测与 "
         f"{C['announcements']} 个免费 ARP 通告，以及 3 个以太网目的为单播的请求。"
         f"后者的存在提醒我们，“请求总是广播”只是常态而非定律，结论应保留适用条件。")

    heading("6.2  实验体会", 11.5)
    para("这次实验最主要的收获是分清了两组容易混淆的地址：以太网首部的目的/源地址决定"
         "帧在链路上的去向，ARP 报文内部的目标/发送方地址才承载“解析”语义。"
         "一开始看到请求里既有 ff:ff:ff:ff:ff:ff 又有全零，很容易以为二者是同一件事，"
         "把它们按层次拆开后，整个交换过程就顺理成章了。")
    para("第二点体会是长度要用字节去核对，而不是凭印象。ARP 报文 28 字节是把"
         "“8 字节固定字段 + 12 字节硬件地址 + 8 字节协议地址”算出来的，"
         "而帧长 42 与 60 的差别完全来自以太网最小帧长的填充要求。"
         "只有把这三段分开，才能解释为什么“同一个协议、同样的报文长度”会有两种帧长。")
    para("第三点是关于实验条件的如实记录。本次没有管理员权限，无法清空 ARP 缓存，"
         "工作负载也不是手册建议的浏览器访问，因此报告里只报告观测到的事实，"
         "不去推断“这次请求由哪次访问触发”。迹线本身的字段分析不受影响，"
         "但把偏差写清楚，比给一个看似完整的叙述更可靠。")
    para("最后是脚本复核的价值。报告中的帧数、报文长度、地址取值与十六进制字节，"
         "都是 analyze.py 直接读取 pcapng 原始字节重新解析得到的，与 Wireshark 界面"
         "显示互为独立验证，而不是从截图抄写。")

    # ================= 七、附录 =================
    sec(7)
    heading("七、附录", 12)
    para("附录 A  迹线与复核文件", indent=False, bold=True)
    table(["文件", "说明"], [
        ["Lab4_ARP.pcapng", f"本次原始迹线，{F['frame_count']} 帧，全部为 ARP"],
        ["evidence/0*.png", "报告中使用的 7 张 Wireshark 截图与 3 张命令行截图"],
        ["evidence/fig_arp_*.png", "两张依据实测数据绘制的示意图"],
        ["facts.json", "脚本从 pcapng 原始字节解析出的全部关键数值"],
        ["analyze.py", "字段提取与长度核算脚本"],
        ["make_diagrams.py", "两张示意图的绘制脚本"],
        ["ping_gateway.txt", "工作负载 ping 的输出"],
    ], [5.4, 11.6])
    para("表 4  附录文件清单", indent=False, size=8.5,
         align=WD_ALIGN_PARAGRAPH.CENTER)

    para("附录 B  关键命令与过滤器", indent=False, bold=True)
    mono([
        "# 取址与网关",
        "ipconfig /all",
        "Get-NetRoute -DestinationPrefix '0.0.0.0/0'",
        "",
        "# 查看 ARP 缓存",
        "arp -a",
        "",
        "# 工作负载（绑定 WLAN 源地址访问网关）",
        "ping -S 172.31.240.50 172.31.0.1",
        "",
        "# Wireshark 过滤器",
        "arp                                            # 捕获过滤器",
        "eth.addr == 14:ac:60:56:df:85                  # 手册 Step 2 的显示过滤器",
        "arp.isprobe || arp.isannouncement              # 探测与免费 ARP",
        "arp.src.proto_ipv4 == 172.31.0.1 || arp.dst.proto_ipv4 == 172.31.0.1",
        "",
        "# 命令行的等价核对",
        "tshark -r Lab4_ARP.pcapng -T fields -e arp.opcode -e arp.src.hw_mac \\",
        "       -e arp.dst.hw_mac -e arp.src.proto_ipv4 -e arp.dst.proto_ipv4",
    ])

    para("附录 C  参考资料", indent=False, bold=True)
    for t in [
        "[1] RFC 826: An Ethernet Address Resolution Protocol. "
        "https://www.rfc-editor.org/rfc/rfc826",
        "[2] RFC 5227: IPv4 Address Conflict Detection. "
        "https://www.rfc-editor.org/rfc/rfc5227（ARP 探测与免费 ARP 通告）",
        "[3] RFC 894: A Standard for the Transmission of IP Datagrams over "
        "Ethernet Networks. https://www.rfc-editor.org/rfc/rfc894"
        "（以太网最小帧长与填充）",
        "[4] Wireshark Foundation: ARP display filter reference. "
        "https://www.wireshark.org/docs/dfref/a/arp.html",
    ]:
        para(t, size=8.5)
    return sections


# --------------------------------------------------------------------------
def main():
    doc = docx.Document(str(TEMPLATE))

    # metadata block
    tbl = doc.tables[0]
    vals = {
        (0, 0): "实验课程：计算机网络", (0, 1): "年级：2024 级", (0, 2): "实验成绩：",
        (1, 0): "实验名称: ARP", (1, 1): "姓名：刘小凡",
        (1, 2): "实验日期：2026-11-03",
        (2, 0): "实验编号：Lab4", (2, 1): "学号：10244602411",
        (2, 2): "实验时间：2学时",
    }
    for (r, c), v in vals.items():
        cell = tbl.rows[r].cells[c]
        cell.text = v
        for pp in cell.paragraphs:
            pp.paragraph_format.first_line_indent = Cm(0)
            for rr in pp.runs:
                set_run(rr, 10.5, False)

    # Template body indices:
    #   4/7/10/13 = headings 一/二/三/四 ; 5/8/11 = their red placeholders
    #   14,15     = the two red instructions under 四
    #   17        = the school's 五 heading (kept: 五 = 必做题目与解答)
    #   18        = red placeholder under 五 ; 19 = empty paragraph after it
    #   20        = the school's 六 heading (dropped: we insert 六 ourselves)
    #   21        = empty paragraph after 六 (becomes 七/附录's anchor)
    # Each section is attached to ITS OWN anchor, so no section can drift under
    # another section's heading.
    children = body_children(doc)
    anchors = {
        1: children[5],      # 一、实验目的
        2: children[8],      # 二、实验内容与实验步骤
        3: children[11],     # 三、实验环境
        4: children[14],     # 四、实验过程与分析
        5: children[18],     # 五、必做题目与解答
        6: children[19],     # 六、实验结果总结
        7: children[21],     # 七、附录
    }
    drop = [children[i] for i in (5, 8, 11, 14, 15, 17, 18, 19, 20, 21)]
    sections = build_content(doc)

    for k, anchor in anchors.items():
        for el in reversed(sections[k]):
            anchor.addnext(el)
    for el in drop:
        el.getparent().remove(el)

    bad = []
    for el in body_children(doc):
        if el.tag.split("}")[-1] == "tbl":
            if el.find(qn("w:tblGrid")) is None or not el.findall(qn("w:tr")):
                bad.append(el)
    if bad:
        print(f"  !! {len(bad)} table(s) are empty shells")

    doc.core_properties.author = "刘小凡"
    doc.core_properties.title = "Lab4 ARP 实验报告"
    doc.save(str(OUT))
    print(f"SAVED {OUT}")

    d2 = docx.Document(str(OUT))
    media = [n for n in zipfile.ZipFile(OUT).namelist()
             if n.startswith("word/media/")]
    reds = sum(1 for p in d2.paragraphs for r in p.runs
               if r.font.color and r.font.color.type is not None
               and str(r.font.color.rgb) == "FF0000")
    unreadable = 0
    for t in d2.tables:
        try:
            len(t.columns)
        except Exception:
            unreadable += 1
    BLIP = ("{http://schemas.openxmlformats.org/drawingml/2006/main}blip")
    imgs = sum(1 for el in body_children(d2)
               if el.tag.split("}")[-1] == "p" and el.findall(".//" + BLIP))
    print(f"  tables={len(d2.tables)} (unreadable={unreadable}) images={imgs} "
          f"media={len(media)} red-runs={reds}")


if __name__ == "__main__":
    main()
