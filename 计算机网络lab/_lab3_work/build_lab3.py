# -*- coding: utf-8 -*-
r"""build_lab3.py - build 10244602411_刘小凡_IPv4.docx from the school template.

Fills the six school sections of the template copy, embeds 8 Wireshark evidence
screenshots plus 2 original diagrams, and preserves the template's header/footer,
metadata block, geometry and section order.

Numbers come from facts.json / logs\source_trace.json, which the handoff's
analyze.py produced by parsing the pcapng directly (not from prose or screenshots).

Usage: python build_lab3.py
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
WORK = ROOT / "_lab3_work"
EV = WORK / "evidence"
LOGS = WORK / "logs"
OUT = ROOT / "10244602411_刘小凡_IPv4.docx"
TEMPLATE = WORK / "template.docx"

FACTS = json.loads((WORK / "facts.json").read_text(encoding="utf-8"))

LATIN = "Times New Roman"
CJK = "SimSun"
CJK_BOLD = "Microsoft YaHei"
BODY_PT = 10.5

SLOT_PURPOSE = 5
SLOT_CONTENT = 8
SLOT_ENV = 11
SLOT_ANALYSIS = 14
SLOT_CONCLUSION = 18
SLOT_APPENDIX = 21


# --------------------------------------------------------------------------
# element builders
# --------------------------------------------------------------------------
def body_children(doc):
    return list(doc.element.body.iterchildren())


def set_run(run, size=BODY_PT, bold=False, latin=LATIN, ea=CJK, color=None):
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.name = latin
    run.font.color.rgb = (RGBColor.from_string(color) if color
                          else RGBColor(0, 0, 0))
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


def new_figure(doc, img, caption, width_cm=16.0):
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
# content
# --------------------------------------------------------------------------
def build_content(doc):
    """Create all content in reading order and return the element list.

    A single run is inserted after the 四 placeholder in main(), in reverse, which
    reproduces this exact order. (The earlier per-slot placement reversed individual
    sections, and a scratch-document transfer emptied the tables, so this is the
    one-pass form that has been verified to keep tables and image relationships.)
    """
    F = FACTS
    out = []

    def put(els):
        out.extend(els if isinstance(els, list) else [els])

    def para(text, **kw):
        put(new_para(doc, text, **kw))

    def heading(text, size=12):
        put(new_heading(doc, text, size))

    def mono(lines, size=9):
        put(new_mono(doc, lines, size))

    def table(heads, rows, widths, size=9):
        put(new_table(doc, heads, rows, widths, size))

    def figure(img, caption, width_cm=16.0):
        put(new_figure(doc, img, caption, width_cm))

    # ---------------- 一、实验目的 ----------------
    for t in [
        "本次实验围绕 IPv4 协议展开，目的是通过抓取并逐字段检查真实的 IPv4 数据报，"
        "掌握 IP 首部的结构与各字段含义，并学会用抓包证据回答关于寻址、长度、标识、"
        "生存时间与分片的问题。具体目标如下：",
        "1. 掌握在 Wireshark 中选择联网接口、设置 tcp port 80 捕获过滤器、开启网络"
        "名称解析并关闭混杂模式的完整抓包流程，能够保存可复核的 pcapng 迹线；",
        "2. 能够把 IPv4 首部各字段与被高亮的原始字节逐一对应，理解哪些字段共享同一个"
        "字节，并据此还原首部长度字段 IHL 的编码方式；",
        "3. 通过实测数据总结 Total Length、Identification、TTL 以及分片标志的变化规律，"
        "并区分“未分片”的判据与 IP 校验和卸载等容易误判的现象；",
        "4. 使用 traceroute 类探测发现从本机到远端服务器的路由器级路径，理解星号跳的"
        "含义，并能借助地址登记信息为每一跳标注归属组织；",
        "5. 独立完成一次 IPv4 首部校验和的 1 的补码求和验算，把 10 个 16 位字与对应"
        "字段一一列出，验证结果等于 0xffff。",
    ]:
        para(t)

    # ---------------- 二、实验内容与实验步骤 ----------------
    para(
         "实验按手册的五个 Step 推进：先用 curl 抓取同一远端服务器的网页并用 "
         "tcp port 80 过滤器捕获，再做 traceroute 探测路径；随后在 Wireshark 中展开 "
         "IPv4 首部逐字段核对；接着绘制 IP 包结构图并回答六道问题；之后依据路径探测"
         "结果绘制网络路径图；最后选取一个接收方向、非零校验和、20 字节首部的包"
         "完整验算 IP 首部校验和。")
    para(
         "本次实测使用 curl 代替手册中的 wget，两者都是命令行取回工具，作用等价。"
         "为避免域名解析或代理影响结果，抓包时用 --resolve 把目标域名固定到一个已知的"
         "服务器地址，并显式指定出口接口、禁用代理、强制 IPv4：")
    mono([
        "curl -4 --noproxy \"*\" --interface 172.31.165.86 \\",
        "     --resolve www.baidu.com:80:182.61.200.108 \\",
        "     -o baidu.html -w \"%{http_code} %{size_download} %{time_total}\\n\" \\",
        "     http://www.baidu.com/",
    ])
    para(
         "命令返回 HTTP 200，Content-Length 2381 字节，实际下载 2381 字节，"
         "全程耗时约 0.855 秒，与抓到的报文长度一致。抓包参数按手册设置：接口选实际"
         "联网的 WLAN，链路层 Ethernet，捕获过滤器 tcp port 80，关闭混杂模式，"
         "勾选网络名称解析。这一步对应手册的 Turn-in 第 1 项。")
    para(
         "需要说明的是，原始迹线 Lab3_HTTP.pcapng 共 108 帧，其中包含其他应用程序的"
         "背景 HTTP 流量。为避免把无关连接混入分析，本次按 tcp.stream == 0 导出目标"
         "连接为 Lab3_HTTP_target.pcapng（19 帧：本机发送 10 帧、接收 9 帧）。导出过程"
         "未改写任何报文，帧号仍为 1–19，后续分析均以该文件为准。")

    # ---------------- 三、实验环境 ----------------
    table(
          ["项目", "实测配置"],
          [
              ["操作系统", "Windows 11 25H2（build 26200），64 位"],
              ["抓包与分析", "Wireshark / TShark 4.6.8，Npcap 1.88"],
              ["命令行工具", "curl 8.21.0；Windows tracert；系统 ICMP API"],
              ["捕获接口", "WLAN：MediaTek Wi-Fi 6E MT7922 (RZ616) 160MHz Wireless LAN Card"],
              ["接口地址", "IPv4 172.31.165.86；网关 172.31.0.1；本机 MAC 14:ac:60:56:df:85"],
              ["链路下一跳 MAC", "54:c6:ff:7b:38:02"],
              ["目标服务器", "www.baidu.com → 182.61.200.108（用 --resolve 固定）"],
              ["链路层类型", "Ethernet（关闭混杂模式，启用网络名称解析）"],
          ], [3.4, 13.6])
    para(
         "本轮实验没有修改任何路由表、VPN 或系统网络配置；路径探测只在应用层指定"
         "源地址，属于普通用户态操作。")

    # ---------------- 四、实验过程与分析（步骤与实测记录） ----------------
    S = SLOT_ANALYSIS
    para("本节只记录实验过程与实测现象：每一步做了什么、看到什么结果、"
            "出现什么异常以及如何排查。手册要求提交的题目与答案统一放在第五节，"
            "便于对照评分。")
    heading("4.1  单播 HTTP 流量的获取与定位", 11.5)
    para("按手册要求选择实际联网的 WLAN 接口，链路层为 Ethernet，捕获过滤器填 "
            "tcp port 80，关闭混杂模式，并勾选网络名称解析，如图 1 与图 2 所示。"
            "过滤器的作用是把迹线限制在标准 Web 流量上，避免无关协议干扰；"
            "关闭混杂模式则只记录本机收发的帧。")
    figure("01_capture_options.png",
           "图 1  捕获选项：接口 WLAN、链路层 Ethernet、捕获过滤器 tcp port 80、"
           "混杂模式未勾选（来源：Lab3_HTTP.pcapng 抓包前的实际设置）", 15.5)
    figure("02_name_resolution.png",
           "图 2  网络名称解析已启用，地址列可显示可识别的主机名"
           "（来源：同一次抓包设置）", 15.0)
    para("开始捕获后重新执行 curl，命令成功后停止捕获。原始迹线共 108 帧，包含背景"
            "流量；按 tcp.stream == 0 导出目标连接后得到 19 帧，构成一次完整的 HTTP "
            "交互：TCP 三次握手、HTTP 请求与响应、四次挥手，如表 1 所示。"
            "图 3 为导出后的目标连接列表，图 4 为跟随该 TCP 流看到的实际内容，"
            "可以看到 GET / HTTP/1.1、200 OK 与 Content-Length: 2381，"
            "与 curl 的输出互相印证。")
    table(
          ["阶段", "帧号", "方向", "IP Total Length", "说明"],
          [
              ["握手", "1–3", "本机 ⇄ 服务器", "52 / 52 / 40", "SYN、SYN/ACK、ACK"],
              ["请求", "4", "本机 → 服务器", "117", "HTTP GET（含 77 B 请求）"],
              ["响应", "5–9, 14", "服务器 → 本机",
               "40 / 1400 / 216 / 373 / 373 / 829", "ACK 与数据段，含一次重传"],
              ["确认与挥手", "10–13, 15–19", "双向", "52 / 40 / 60",
               "Dup ACK、FIN/ACK、ACK"],
          ], [2.4, 2.6, 2.8, 3.6, 5.6])
    figure("03_target_connection.png",
           "图 3  目标连接列表与显示过滤器 tcp.stream == 0：19 帧全部属于本次 HTTP "
           "交互（来源：Lab3_HTTP_target.pcapng）", 15.5)
    figure("06_http_200_stream.png",
           "图 4  跟随 TCP 流的实际内容：GET / HTTP/1.1 与 HTTP/1.1 200 OK、"
           "Content-Length 2381（来源：Lab3_HTTP_target.pcapng 第 4 帧与第 14 帧所在流）",
           14.5)

    heading("4.2  IPv4 首部的逐字段检查", 11.5)
    para("选取本机发出的 HTTP GET 报文（第 4 帧）展开 IPv4 首部，如图 5 所示。"
            "该帧的 IP 首部为最小长度 20 字节，没有选项字段，因此可以直接与原始字节"
            "逐一对照。首部原始字节为 45 00 00 75 ed c0 40 00 80 06 00 00 ac 1f a5 56 "
            "b6 3d c8 6c，各字段对应关系如表 2。")
    figure("04_outgoing_ipv4.png",
           "图 5  第 4 帧（HTTP GET）的 IPv4 首部各字段与对应的原始字节高亮，"
           "TTL = 128、Total Length = 117、首部校验和为 0x0000"
           "（来源：Lab3_HTTP_target.pcapng 第 4 帧）", 15.5)
    table(
          ["字段", "字节", "长度", "实测值", "说明"],
          [
              ["Version + IHL", "0", "1 B", "0x45", "Version=4，IHL=5"],
              ["Differentiated Services", "1", "1 B", "0x00", "DSCP CS0，ECN Not-ECT"],
              ["Total Length", "2–3", "2 B", "0x0075 = 117", "首部 20 + 载荷 97"],
              ["Identification", "4–5", "2 B", "0xedc0", "分片重组时用于归组"],
              ["Flags + Fragment Offset", "6–7", "2 B", "0x4000",
               "DF=1，MF=0，Offset=0"],
              ["Time To Live", "8", "1 B", "128", "本机 IPv4 默认值"],
              ["Protocol", "9", "1 B", "6", "上层为 TCP"],
              ["Header Checksum", "10–11", "2 B", "0x0000", "抓包点为网卡卸载，未填值"],
              ["Source Address", "12–15", "4 B", "172.31.165.86", "本机 WLAN"],
              ["Destination Address", "16–19", "4 B", "182.61.200.108", "远端服务器"],
          ], [4.0, 1.5, 1.2, 3.0, 5.0])
    para("关于首部校验和为 0 的现象需要谨慎解读：本机发出的所有 IP 报文在抓包点校验和"
            "都是 0x0000，Wireshark 因此把它们标为校验和有误。手册对此已有说明——"
            "这是校验和卸载（checksum offload），操作系统把计算与填写交给网卡在发出时"
            "完成，而抓包发生在网卡处理之前。因此不能据此断言线上首部真的错误；"
            "接收方向的报文校验和非零且被判定为正确，第 5.4 节将用它来做验算。")

    # 以下四项是手册要求提交的题目与答案，统一放到第五节，不夹在实验步骤里
    heading("五、必做题目与解答", 12)
    para("本节集中列出手册要求提交的题目与本次作答结果。题目原文以「题目原文」标出，"
         "答案紧接其后；涉及的图、表编号与第五节内部编号一致。")
    heading("5.1  必做题目一：绘制 IP 包结构图", 11.5)
    para("题目原文（Step 3）：绘出所研究 IP 包的示意图，显示 IP 首部各字段的位置与"
            "字节长度；由于无法轻易判定字节内部的位宽，把占用同一字节的字段合并表示；"
            "并标出以太网首部与 IP 载荷的范围。")
    para("依据第 4 帧的实测字段绘制 IP 数据报结构图，如图 6。图中矩形按字节等比绘制，"
            "把无法再分的字段（如 Version 与 IHL 共用第 0 字节、Flags 与 Fragment "
            "Offset 共用第 6、7 字节）合并为一格；下方表格给出每格的长度与实测取值。"
            "本图为依据实测数据绘制的示意图，不是软件截图。")
    figure("fig_A_ipv4_structure.png",
           "图 6  IPv4 数据报结构（依据 Lab3_HTTP_target.pcapng 第 4 帧实测，"
           "IP 首部 20 B；本图为绘制示意图）", 16.0)
    para("与教材的 IPv4 首部图对照后没有发现结构差异，但有两处值得记录：一是"
            "首部长度并不是独立字段，而是与版本号共享同一个字节，只能以 4 字节为单位"
            "表示；二是校验和在抓包点为空，这属于实现细节而非协议本身的差异。")

    heading("5.2  必做题目二：IPv4 六道问题", 11.5)
    para("题目原文（Step 3）：结合迹线中的 IP 包回答以下六个问题。逐题作答如下。")
    para("问题 1：本机与远端服务器的 IP 地址是什么？本机 WLAN 接口地址为 "
            "172.31.165.86，远端服务器为 182.61.200.108。这两个地址可以从迹线中任一"
            "收发方向报文的 Source Address 与 Destination Address 字段直接读出，"
            "方向由地址顺序即可区分。")
    para("问题 2：Total Length 包含 IP 首部还是仅包含 IP 载荷？两者都包含，即 "
            "IP 首部长度加上 IP 载荷长度，但不包含以太网首部。以第 4 帧为例，"
            "Total Length = 117 B，而首部为 20 B、TCP 首部 20 B、HTTP 请求 77 B，"
            "20 + 20 + 77 = 117，正好吻合。该帧的以太网帧长为 131 B，"
            "131 − 117 = 14 B 恰好是以太网首部，可见链路层首部不计入 Total Length。")
    para("问题 3：Identification 字段如何变化？本机发送方向按顺序为 0xedbe、"
            "0xedbf、0xedc0、0xedc1、0xedc2、0xedc3、0xedc4、0xedc5、0xedc6、0xedc7，"
            "逐包递增 1；接收方向依次为 0xedbe（第 2 帧）、0xb73c、0xb73e、0xb73f、"
            "0xb740、0xb741、0xb744、0xb745、0xb746，存在跳号。因此可以说：同一方向、"
            "由同一台主机产生的报文其 Identification 常呈递增趋势，但两方向的取值互相"
            "独立，且接收方向出现跳号，所以既不能说它在整个 TCP 连接中保持不变，"
            "也不能断言两方向绝无重复。需要强调的是 Identification 不是 TCP 连接号，"
            "它服务于分片重组：同一原始数据报拆成的多个分片共享该值，接收端依据"
            "源/目的地址、Protocol 与 Identification 等把它们归到一组。对未分片的 "
            "atomic datagram，RFC 6864 并不要求每个包的取值都不相同。")
    para("问题 4：本机发出的报文 TTL 初值是多少？是最大值吗？本机发送的所有报文 "
            "TTL 均为 128，不是 8 位字段的最大值 255。这说明发送方主动选择了一个较低的"
            "初值（Windows 的 IPv4 默认值）。需要与路径探测区分：在绑定源地址的 "
            "traceroute 中，探测报文被故意设置成 TTL = 1、2、3……17，那是为了实现逐跳"
            "探测，与本机普通数据流的 TTL 初值不是一回事，两者不能混为一谈。")
    para("问题 5：如何判断一个包没有被分片？关键在于 Fragmentation 相关的三个信息："
            "MF（More Fragments）标志为 0 且 Fragment Offset 为 0。本迹线 19 个包"
            "全部满足 MF=0、Offset=0。需要注意 DF（Don't Fragment）位在本迹线中虽然"
            "都是 1，但 DF=1 并不是“未分片”的必要条件：一个报文完全可以是 DF=0 "
            "却因为长度未超过 MTU 而没有分片。反过来，若 MF=0 但 Offset>0，"
            "则说明它是某个已分片数据报的最后一片。因此判据应是 MF=0 且 Offset=0。"
            "另外 Fragment Offset 的单位是 8 字节而不是 1 字节。")
    para("问题 6：IP 首部长度是多少，在首部长度字段中如何编码？本次所有报文的首部"
            "长度都是 20 B，即不含选项的最小首部。首部的第 0 字节为 0x45，高 4 位是"
            "版本号（0100 = 4），低 4 位是 IHL（0101 = 5）。IHL 表示的是“以 4 字节为"
            "单位的首部长度”，因此实际字节数 = IHL × 4 = 5 × 4 = 20 B。正因为只有 "
            "4 位，IHL 的最大值为 15，对应首部最长 60 B，这既是选项字段长度受限的原因，"
            "也是首部长度必须以 4 字节对齐的原因。")

    heading("5.3  必做题目三：Internet 路径图与组织标注", 11.5)
    para("题目原文（Step 4）：依据 traceroute 输出绘制网络路径示意图，标明本机与"
            "远端服务器的 IP 地址，以及路径上路由器的跳数编号；并利用域名信息标注"
            "每一跳所属的真实组织；无法解析的跳留空。")
    para("手册用 traceroute 发现源到目的之间的路由器级路径，其原理是让探测报文"
            "以递增的 TTL 发出，第 1 台路由器把 TTL 减到 0 后回送 ICMP Time Exceeded，"
            "据此逐个暴露路径上的路由器。图 7 为迹线中 ICMP Time Exceeded 报文的实际"
            "内容：外层源地址 10.100.4.1、目的为本机，ICMP Type=11、Code=0，"
            "报文内部还引用了被丢弃的那个 Echo 请求的 IP 首部与原始数据。")
    figure("09_icmp_time_exceeded.png",
           "图 7  ICMP Time Exceeded（Type 11 / Code 0）：外层源地址 10.100.4.1，"
           "内部引用本机发往 182.61.200.108 的原始 Echo 请求"
           "（来源：Lab3_Path_WLAN.pcapng 第 5 帧）", 15.5)
    para("本次路径测量遇到一个必须交代的异常。直接执行 Windows 自带的 "
            "tracert -4 -h 30 -w 700 182.61.200.108，得到的输出只有两跳：")
    mono([
        "1    *        62 ms    *        182.61.200.108",
        "2    33 ms    32 ms    33 ms    182.61.200.108",
    ])
    para("这显然不是真实的物理路径——不可能第 1 跳就到达终点。检查发现本机启用了 "
            "singbox_tun，系统默认 IPv4 路由指向 172.18.0.2，因此该命令发出的 Echo "
            "请求在 WLAN 接口处被捕获时 TTL 全部是 128，并没有逐跳递增，"
            "说明探测流量被本机隧道接管后由隧道重新封装，不能反映 WLAN 上的真实路径。"
            "整个排查过程中没有修改路由表、VPN 或任何系统网络设置。")
    para("为绕开隧道，改用微软文档记载的 IcmpSendEcho2Ex 接口，在调用时把源地址"
            "显式绑定为 WLAN 的 172.31.165.86，并以 900 ms 超时、每跳 3 次的方式"
            "发送逐 TTL 的 ICMP 探测。这样探测报文直接以 WLAN 地址发出，"
            "同时在 WLAN 上抓包交叉验证。因此下面给出的结果应准确称为"
            "“绑定 WLAN 源地址的 traceroute”，而不是 Windows tracert.exe 的输出。")
    para(f"本次共探测 17 跳，捕获到 {F['path_probe_count']} 个 Echo 请求、"
            f"{F['path_time_exceeded']} 个 Time Exceeded 与 {F['path_echo_reply']} 个"
            f"终点 Echo Reply，TTL 从 1 到 17 每个值恰好 3 个真实探测。"
            f"图 8 为其中 TTL = 1、2、3 的三次探测及其应答，可看到过滤器已排除 "
            f"ICMP 引用包中的内层 IP，避免把内层地址误当成外层源地址；"
            f"图 9 为同一视图的状态栏计数。")
    figure("08_path_ttl_probes.png",
           "图 8  TTL = 1、2、3 的逐跳探测及其应答，过滤器排除了 ICMP 引用包的内层 IP"
           "（来源：Lab3_Path_WLAN.pcapng）", 15.5)
    figure("08_path_status.png",
           "图 9  同一路径窗口底部状态栏：合计 76 帧，当前显示 51 帧"
           "（来源：Lab3_Path_WLAN.pcapng 的同一视图局部）", 9.5)
    figure("fig_B_path.png",
           "图 10  到 182.61.200.108 的 Internet 路径，共 17 跳，“无应答”为 900 ms 内"
           "未收到回复（本图为依据 source_trace.json 绘制的示意图）", 16.0)
    para("关于组织标注的来源必须说明清楚：本次所有路由器的反向域名（PTR）解析均未"
            "成功，因此组织名称不是来自域名反解，而是查询 APNIC 的地址登记信息得到。"
            "具体为 RDAP 服务：202.120.95.246 属于 CERNET-CN（202.112.0.0/13 段）、"
            "101.4.116.61 属于 BJR-CERNET（101.4.0.0/14 段）、219.224.103.65 属于 "
            "BJR-CERNET（219.224.0.0/15 段）、182.61.255.32 属于 Baidu"
            "（182.61.0.0/16 段）。这类标签说明的是地址的登记归属，既不等于设备的"
            "物理位置，也不是域名反解的结果。第 2 跳 10.100.4.1 属于私网地址，"
            "没有公开登记信息，只能标注为未知。")
    para("路径图中的星号只表示在规定的 900 ms 内没有收到对应回复。它不能证明该跳"
            "不存在，也不能仅凭它断言那台路由器关闭了 ICMP；常见原因还包括路由器"
            "限速 ICMP、回复走了不同路径或优先级较低而被丢弃。另外，ICMP 探测出来的"
            "路径不保证与 TCP 数据实际走的路径完全相同，反向路径也可能不同，"
            "所以这张图描述的是本次测量条件下的转发路径。")
    para("路径整体呈现清晰的层次：出口经 10.100.4.1 进入校园网，第 4–5 跳为"
            "上海交通大学相关的 CERNET 节点，第 7–11 跳进入北京 CERNET 骨干，"
            "第 12–13 跳进入百度网络，第 17 跳到达目标服务器。这与"
            "“先出校园网、再上教育网骨干、最后进入目标运营商”的一般规律一致。")

    heading("5.4  必做题目四：IP 首部校验和验算", 11.5)
    para("按手册要求选取接收方向、首部 20 字节且校验和非零的报文。本次选用第 5 帧，"
            "它是服务器对本机 HTTP 请求的确认，源地址 182.61.200.108、目的地址 "
            "172.31.165.86，Wireshark 给出的首部校验和为 0xcb73 并标记 [correct]，"
            "如图 11 所示。该帧首部原始字节为：")
    mono(["45 00 00 28 b7 3c 40 00 28 06 cb 73 b6 3d c8 6c ac 1f a5 56"])
    para("把首部按 16 位切成 10 个字，用普通加法累计，并在每一步标注对应的 IPv4 "
            "字段，结果如表 3。")
    W = F["words"]
    ACC = F["accum"]
    LABELS = ["Version、IHL、DS", "Total Length", "Identification",
              "Flags、Fragment Offset", "TTL、Protocol", "首部校验和（实收值）",
              "源地址前半", "源地址后半", "目的地址前半", "目的地址后半"]
    table(["序号", "16 位字", "对应 IPv4 字段", "累计和"],
          [[str(i + 1), "0x" + W[i], LABELS[i], "0x" + ACC[i]] for i in range(10)],
          [1.2, 2.0, 6.4, 2.6])
    para(f"普通累加的结果为 0x{F['sum']}，已经超过 16 位。按 1 的补码运算规则，"
            f"把最高位溢出的部分回卷加回低 16 位：0x{F['sum']} → 高 16 位 0x0004 "
            f"加上低 16 位 0xfffb，得到 0x{F['fold']}。这正是 1 的补码形式的"
            f"“负零”，说明校验和自洽。")
    para(f"为了进一步确认，再把校验和字段本身置零后重新计算一遍：其余 9 个字的和"
            f"为 0x{F['zero_sum']}，回卷后为 0x{F['zero_fold']}，按位取反得到 "
            f"0x{F['checksum']}，与报文里实际携带的 0xcb73 以及 Wireshark 的 "
            f"[correct] 判定完全一致。两次计算分别从“包含校验和应收敛到 0xffff”"
            f"和“置零后取反应等于校验和”两个方向验证了同一结果。")
    para("上述数值不是从截图上抄录的，而是 analyze.py 直接读取 pcapng 的原始字节，"
            "按同样的 1 的补码规则重新计算并断言得到的，因此与界面显示互为独立验证。")
    figure("05_incoming_checksum.png",
           "图 11  第 5 帧接收方向 IPv4 首部的 20 B 高亮，校验和 0xcb73 标记为 "
           "[correct]（来源：Lab3_HTTP_target.pcapng 第 5 帧）", 15.5)
    figure("07_id_ttl_fragmentation.png",
           "图 12  19 帧的源/目的地址、Identification、TTL、IP Length、DF、MF、"
           "Offset 全列表，用于核对分片标志与标识变化"
           "（来源：Lab3_HTTP_target.pcapng）", 16.0)

    # ---------------- 五、必做题目索引 / 六、实验结果总结 ----------------
    # 五 is headed below; 六's heading is inserted just before 6.1.
    C = SLOT_CONCLUSION
    para("手册要求提交的题目均已单独作答，位置如下，便于对照评分：")
    heading("必做题目索引", 11.5)
    table(
          ["手册要求", "作答位置"],
          [
              ["1. 成功获取同一远端服务器的 HTTP 网页，捕获 tcp port 80 流量；"
               "记录 traceroute",
               "实测过程见 4.1 节；curl 取得 HTTP 200，Content-Length 2381；"
               "路径结果见 5.3 节图 10"],
              ["2. 检查 IPv4 首部全部字段及字节",
               "实测过程与原始字节见 4.2 节，字段逐项对应见该节表 2"],
              ["3. 绘制 IP 包结构图，回答六题",
               "结构图见 5.1 节图 6；六题答案见 5.2 节"],
              ["4. 绘制按跳编号的路径图并标注组织",
               "见图 10（5.3 节），共 17 跳；组织标注来自 APNIC 登记信息"],
              ["5. 选取接收方向、非零校验和、20 B 首部的包，把 10 个 16 位字对应到"
               "字段并验证 0xffff",
               "见 5.4 节表 3：回卷后得 0xffff；置零复算得 0xcb73，双向一致"],
          ], [6.0, 11.0])
    heading("六、实验结果总结", 12)
    heading("6.1  实验结论", 11.5)
    para("关于 IPv4 首部：本次所有报文首部长度均为 20 B，无选项字段；"
            "首字节 0x45 同时编码版本号与首部长度，IHL 以 4 字节为单位，"
            "最大值 15 对应 60 B。Total Length 统计 IP 首部与载荷之和，不含链路层首部。")
    para("关于标识与分片：本机方向 Identification 逐包递增，接收方向存在跳号，"
            "说明它只是分片重组时用于归组同一数据报的标识，并非连接号；"
            "19 个包全部满足 MF=0 且 Offset=0，因此都未分片，"
            "其中 DF=1 是发送方的策略选择而不是未分片的判据。")
    para("关于 TTL：本机普通数据流的 TTL 初值为 128，低于 8 位字段上限 255；"
            "接收方向报文 TTL 为 40，首个响应为 45。这里只报告观测值——"
            "由 64 减 TTL 直接推算跳数是不严谨的，因为无法确认对端的初始 TTL 一定是 "
            "64，而且双向路由可能不同。")
    para("关于校验和：接收方向首部校验和经两次独立计算确认正确；"
            "本机方向校验和为 0 是校验和卸载造成的观测现象，不代表线上首部有误。")
    para("关于与教材的差异：结构上没有发现差异，但有一处实现层面的现象值得记住——"
            "协议规定的字段未必在抓包点就已填好，校验和卸载就是典型例子。"
            "这提醒我们在用抓包结论判断“对错”之前，要先确认抓包位置相对于协议栈"
            "处理的位置。")
    heading("6.2  实验体会", 11.5)
    para("这次实验最主要的收获是意识到“看到的”和“实际发出的”可能不是一回事。"
            "本机 IP 校验和全为 0，如果只看抓包就下结论，会误判为协议实现错误；"
            "同样，直接运行 tracert 得到“两跳到达”，如果照抄就成了错误结论，"
            "实际原因是隧道接管了探测流量。两处都说明：异常现象要先定位到观测位置和"
            "处理时序，再谈结论。")
    para("另一处体会是描述数据时要留有余地。Identification 在本机方向确实逐包递增，"
            "但接收方向有跳号，因此报告里只写“呈递增趋势”而不断言每包加一；"
            "星号跳也只写“规定时间内无应答”，不推断该路由器关闭了 ICMP。"
            "把结论限制在证据支持的范围内，比给出一个漂亮但过度的断言更可靠。")
    para("最后是独立复核的价值。校验和既可以让 Wireshark 判定，也可以自己按 1 的"
            "补码算一遍；两条路径得到同一个结果，才算真正验证。"
            "本报告的字段与统计量均由脚本从 pcapng 原始字节重新解析，"
            "与界面显示互为交叉验证，而不是从截图抄写。")

    # ---------------- 七、附录 ----------------
    heading("七、附录", 12)
    para("附录 A  迹线与日志文件", indent=False, bold=True)
    table(
          ["文件", "说明"],
          [
              ["Lab3_HTTP_target.pcapng", "目标 HTTP 连接，19 帧，报告主要依据"],
              ["Lab3_HTTP.pcapng", "抓包原始迹线 108 帧（含背景流量），仅作留存"],
              ["Lab3_Path_WLAN.pcapng", "绑定 WLAN 源地址的路径探测，76 帧"],
              ["Lab3_Traceroute.pcapng", "普通 tracert 的 WLAN 迹线，隧道干扰证据"],
              ["logs/Lab3_HTTP_target.tsv", "逐帧字段提取结果"],
              ["logs/Lab3_Path_WLAN.tsv", "路径探测字段提取（-E occurrence=f）"],
              ["logs/source_trace.json", "17 跳路径结构，图 10 的数据来源"],
              ["logs/rdap_*.json", "APNIC 地址登记查询原始结果"],
              ["facts.json / analyze.py", "字段提取与校验和独立验算脚本及结果"],
          ], [5.4, 11.6])
    para("附录 B  关键命令", indent=False, bold=True)
    mono([
        "# 抓取目标网页（固定服务器地址、指定接口、禁用代理、强制 IPv4）",
        "curl -4 --noproxy \"*\" --interface 172.31.165.86 \\",
        "     --resolve www.baidu.com:80:182.61.200.108 -o baidu.html http://www.baidu.com/",
        "",
        "# 导出目标 TCP 连接",
        "tshark -r Lab3_HTTP.pcapng -Y \"tcp.stream == 0\" -w Lab3_HTTP_target.pcapng",
        "",
        "# 提取 IPv4 字段用于核对（避免把 ICMP 引用包的内层 IP 当成外层）",
        "tshark -r Lab3_HTTP_target.pcapng -T fields -E occurrence=f \\",
        "       -e frame.number -e ip.src -e ip.dst -e ip.len -e ip.id -e ip.ttl \\",
        "       -e ip.flags.df -e ip.flags.mf -e ip.frag_offset -e ip.checksum",
    ])
    para("附录 C  参考资料", indent=False, bold=True)
    for t in [
        "[1] RFC 791: Internet Protocol. https://www.rfc-editor.org/rfc/rfc791.html"
        "（IPv4 首部格式与首部校验和算法）",
        "[2] RFC 6864: Updated Specification for the IPv4 ID Field. "
        "https://www.rfc-editor.org/rfc/rfc6864.html"
        "（atomic datagram 的 Identification 不要求逐包唯一）",
        "[3] RFC 792: Internet Control Message Protocol. "
        "https://www.rfc-editor.org/rfc/rfc792.html（Time Exceeded 报文格式）",
        "[4] Microsoft Learn: IcmpSendEcho2Ex function. "
        "https://learn.microsoft.com/windows/win32/api/icmpapi/nf-icmpapi-icmpsendecho2ex"
        "（绑定源地址的 ICMP 探测接口）",
        "[5] Wireshark Foundation: IPv4 display filter reference. "
        "https://www.wireshark.org/docs/dfref/i/ip.html",
    ]:
        para(t, size=8.5)

    return out


# --------------------------------------------------------------------------
def main():
    doc = docx.Document(str(TEMPLATE))

    # metadata block
    tbl = doc.tables[0]
    vals = {
        (0, 0): "实验课程：计算机网络", (0, 1): "年级：2024 级", (0, 2): "实验成绩：",
        (1, 0): "实验名称: IPv4", (1, 1): "姓名：刘小凡",
        (1, 2): "实验日期：2026-10-13",
        (2, 0): "实验编号：Lab3", (2, 1): "学号：10244602411",
        (2, 2): "实验时间：2学时",
    }
    for (r, c), v in vals.items():
        cell = tbl.rows[r].cells[c]
        cell.text = v
        for pp in cell.paragraphs:
            pp.paragraph_format.first_line_indent = Cm(0)
            for rr in pp.runs:
                set_run(rr, 10.5, False)

    # Capture the placeholder anchors BEFORE adding content, then place content.
    # Template body indices:
    #   5      red placeholder under 一
    #   8      red placeholder under 二
    #   11     red placeholder under 三
    #   14,15  the two red instructions under 四
    #   17,20  the school's 五/六 headings (replaced by ours: 五 = 必做题目与解答,
    #          六 = 实验结果总结)
    #   18,19  the red instruction under 五 and the empty paragraph after it
    #   21     empty paragraph after 六
    # Final layout: 一..四(过程与分析) | 五(必做题目与解答) | 六(结果总结) | 七(附录).
    children = body_children(doc)
    insert_anchor = children[14]                 # start of section 四
    drop = [children[i] for i in (5, 8, 11, 14, 15, 17, 18, 19, 20, 21)]
    elements = build_content(doc)

    # one pass, reversed, so `elements` ends up in reading order after the anchor
    for el in reversed(elements):
        insert_anchor.addnext(el)

    # drop the template's own placeholders (the anchor is removed LAST so the
    # inserted block stays put)
    for el in drop[1:] + drop[:1]:
        el.getparent().remove(el)

    # integrity: no table may be an empty shell
    bad = []
    for el in body_children(doc):
        if el.tag.split("}")[-1] == "tbl":
            if el.find(qn("w:tblGrid")) is None or not el.findall(qn("w:tr")):
                bad.append(el)
    if bad:
        print(f"  !! {len(bad)} table(s) are empty shells")

    doc.core_properties.author = "刘小凡"
    doc.core_properties.title = "Lab3 IPv4 实验报告"
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
    imgs = sum(1 for el in body_children(d2)
               if el.tag.split("}")[-1] == "p"
               and el.findall(".//{http://schemas.openxmlformats.org/"
                              "drawingml/2006/main}blip"))
    print(f"  tables={len(d2.tables)} (unreadable={unreadable}) images={imgs} "
          f"media={len(media)} red-runs={reds}")


if __name__ == "__main__":
    main()
