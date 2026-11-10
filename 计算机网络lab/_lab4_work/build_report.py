# -*- coding: utf-8 -*-
"""Build the Lab4 report from the retained school template and the real trace."""
from pathlib import Path
import sys
from zipfile import ZipFile
from lxml import etree
from PIL import Image, ImageDraw, ImageFont
from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.shared import Cm, Pt, RGBColor
from docx.oxml import OxmlElement
from docx.oxml.ns import qn

sys.stdout.reconfigure(encoding='utf-8', errors='replace')
ROOT = Path(r'C:\University Courses\计算机网络lab')
WORK = ROOT / '_lab4_work'
TEMPLATE = ROOT / '_lab3_work' / 'template.docx'
OUT = ROOT / '10244602411_刘小凡_Lab4_ARP.docx'
DIAGRAM = WORK / 'ARP交换示意图.png'
BLACK = RGBColor(0,0,0)

def draw_exchange():
    im = Image.new('RGB', (1900, 920), 'white')
    d = ImageDraw.Draw(im)
    regular = r'C:\Windows\Fonts\msyh.ttc'
    bold = r'C:\Windows\Fonts\msyhbd.ttc'
    f = ImageFont.truetype(regular, 33)
    small = ImageFont.truetype(regular, 29)
    head = ImageFont.truetype(bold, 37)
    ink = '#202a35'; blue = '#245376'; gray = '#5a6771'; red = '#a33a36'
    d.rounded_rectangle((55,35,840,187),radius=17,fill='#f2f5f7',outline='#8093a1',width=3)
    d.rounded_rectangle((1060,35,1845,187),radius=17,fill='#f2f5f7',outline='#8093a1',width=3)
    d.text((85,53),'本机  WLAN',font=head,fill=ink)
    d.text((85,111),'172.31.240.50    14:ac:60:56:df:85',font=f,fill=ink)
    d.text((1090,53),'WLAN 默认网关',font=head,fill=ink)
    d.text((1090,111),'172.31.0.1    54:c6:ff:7b:38:02',font=f,fill=ink)
    d.line((430,187,430,905),fill='#a4b0b8',width=3)
    d.line((1470,187,1470,905),fill='#a4b0b8',width=3)
    def arrow(x1,x2,y,color):
        d.line((x1,y,x2,y),fill=color,width=7)
        s=1 if x2>x1 else -1
        d.polygon([(x2,y),(x2-s*25,y-14),(x2-s*25,y+14)],fill=color)
    d.text((650,215),'第 5 帧  ARP 请求',font=head,fill=blue)
    arrow(445,1455,285,blue)
    d.text((510,310),'以太网目的 MAC：ff:ff:ff:ff:ff:ff（广播）',font=small,fill=ink)
    d.text((510,358),'发送方：172.31.240.50 / 14:ac:60:56:df:85',font=small,fill=ink)
    d.text((510,406),'目标：172.31.0.1 / 00:00:00:00:00:00（未知）',font=small,fill=ink)
    d.text((655,497),'第 6 帧  ARP 应答',font=head,fill=blue)
    arrow(1455,445,567,blue)
    d.text((510,591),'以太网目的 MAC：14:ac:60:56:df:85（单播）',font=small,fill=ink)
    d.text((510,639),'发送方：172.31.0.1 /',font=small,fill=ink)
    d.text((880,639),'54:c6:ff:7b:38:02',font=small,fill=red)
    d.ellipse((862,627,1190,690),outline=red,width=4)
    d.text((510,706),'目标：172.31.240.50 / 14:ac:60:56:df:85',font=small,fill=ink)
    d.text((510,810),'圈出的是从应答的发送方 MAC 字段学到的网关地址。',font=small,fill=gray)
    d.text((510,858),'说明：同一时段存在重复请求，图中按地址与时间选取相邻帧。',font=small,fill=gray)
    im.save(DIAGRAM, dpi=(180,180))

def font(run, size=10.5, bold=False, mono=False):
    run.font.name = 'Consolas' if mono else 'Times New Roman'
    run.font.size = Pt(size); run.font.bold = bold; run.font.color.rgb = BLACK
    run._element.get_or_add_rPr().rFonts.set(qn('w:eastAsia'), 'Microsoft YaHei' if bold else 'SimSun')

def para(doc, text, indent=True, size=10.5, bold=False, after=3):
    p = doc.add_paragraph(style='中文首行缩进')
    p.paragraph_format.first_line_indent = Cm(.7 if indent else 0)
    p.paragraph_format.line_spacing = 1.25
    p.paragraph_format.space_before = Pt(0); p.paragraph_format.space_after = Pt(after)
    p.paragraph_format.widow_control = True
    font(p.add_run(text), size, bold)
    return p._p

def head(doc, text):
    p=doc.add_paragraph(style='Normal')
    p.paragraph_format.first_line_indent=Cm(0)
    p.paragraph_format.space_before=Pt(7); p.paragraph_format.space_after=Pt(3)
    p.paragraph_format.keep_with_next=True
    font(p.add_run(text),11,True)
    return p._p

def table(doc, headers, rows, widths, size=9):
    t=doc.add_table(rows=1, cols=len(headers)); t.autofit=False
    t.alignment=WD_TABLE_ALIGNMENT.CENTER
    for i,w in enumerate(widths): t.columns[i].width=Cm(w)
    for i,s in enumerate(headers): t.rows[0].cells[i].text=str(s)
    for row in rows:
        cells=t.add_row().cells
        for i,s in enumerate(row): cells[i].text=str(s)
    borders=OxmlElement('w:tblBorders')
    for edge in ('top','left','bottom','right','insideH','insideV'):
        e=OxmlElement('w:'+edge); e.set(qn('w:val'),'single'); e.set(qn('w:sz'),'4'); e.set(qn('w:color'),'A0A0A0'); borders.append(e)
    t._tbl.tblPr.append(borders)
    for ri,row in enumerate(t.rows):
        trpr=row._tr.get_or_add_trPr(); trpr.append(OxmlElement('w:cantSplit'))
        if ri==0: trpr.append(OxmlElement('w:tblHeader'))
        for ci,cell in enumerate(row.cells):
            cell.width=Cm(widths[ci]); cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcpr=cell._tc.get_or_add_tcPr()
            mar=OxmlElement('w:tcMar')
            for edge in ('top','bottom','left','right'):
                e=OxmlElement('w:'+edge); e.set(qn('w:w'),'65'); e.set(qn('w:type'),'dxa'); mar.append(e)
            tcpr.append(mar)
            if ri==0:
                sh=OxmlElement('w:shd'); sh.set(qn('w:fill'),'EDEFF0'); tcpr.append(sh)
            for p in cell.paragraphs:
                p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.line_spacing=1.1
                p.paragraph_format.space_before=Pt(1); p.paragraph_format.space_after=Pt(1)
                for r in p.runs: font(r,size,ri==0)
    return t._tbl

def figure(doc, caption):
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.space_before=Pt(4)
    p.paragraph_format.space_after=Pt(1); p.paragraph_format.keep_with_next=True
    p.add_run().add_picture(str(DIAGRAM),width=Cm(16))
    c=doc.add_paragraph(); c.alignment=WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.first_line_indent=Cm(0); c.paragraph_format.space_after=Pt(6)
    font(c.add_run(caption),9)
    return [p._p,c._p]

def screenshot(doc):
    # Keep the original screenshot intact; crop its empty lower part only in
    # Word's picture layout. The display filter and both packet rows remain.
    p=doc.add_paragraph(); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
    p.paragraph_format.first_line_indent=Cm(0); p.paragraph_format.keep_with_next=True
    p.paragraph_format.space_before=Pt(4); p.paragraph_format.space_after=Pt(1)
    pic=p.add_run().add_picture(str(WORK / 'Wireshark_请求应答.png'),width=Cm(16))
    fill=pic._inline.xpath('.//pic:blipFill')[0]
    crop=OxmlElement('a:srcRect'); crop.set('b','75000'); fill.insert(1,crop)
    pic.height=int(pic.height*.25)
    c=doc.add_paragraph(); c.alignment=WD_ALIGN_PARAGRAPH.CENTER
    c.paragraph_format.first_line_indent=Cm(0); c.paragraph_format.space_after=Pt(5)
    font(c.add_run('图 1  Wireshark 显示第 5 帧请求和第 6 帧应答（界面截图）'),9)
    return [p._p,c._p]

def mono(doc, lines):
    result=[]
    for line in lines:
        p=doc.add_paragraph(); p.paragraph_format.first_line_indent=Cm(0)
        p.paragraph_format.left_indent=Cm(.3); p.paragraph_format.line_spacing=1.05
        p.paragraph_format.space_after=Pt(0)
        font(p.add_run(line),8.5,mono=True); result.append(p._p)
    return result

def add_after(anchor, elements):
    for e in reversed(elements): anchor.addnext(e)

def main():
    draw_exchange()
    doc=Document(str(TEMPLATE))
    children=list(doc.element.body.iterchildren())
    # Keep the school's six headings and replace only the instructional slots.
    for idx in (4,7,10,13,17,20):
        for r in doc.paragraphs:
            if r._p is children[idx]:
                r.paragraph_format.keep_with_next=True
                for run in r.runs: font(run,12,True)
    meta=doc.tables[0]
    # Floating placement can overlap a populated report; keep table inline.
    fl=meta._tbl.tblPr.find(qn('w:tblpPr'))
    if fl is not None: meta._tbl.tblPr.remove(fl)
    # The school's horizontal rule is a floating VML shape. Once the metadata
    # table is inline, its original 75 pt offset would cross the first section.
    for line in children[3].iter('{urn:schemas-microsoft-com:vml}line'):
        line.set('from','-4.15pt,9pt'); line.set('to','492.35pt,9pt')
    vals={(0,0):'实验课程：计算机网络',(0,1):'年级：2024 级',(0,2):'实验成绩：',
          (1,0):'实验名称：ARP',(1,1):'姓名：刘小凡',(1,2):'实验日期：2026-11-10',
          (2,0):'实验编号：Lab4',(2,1):'学号：10244602411',(2,2):'实验时间：2 学时'}
    for (i,j),value in vals.items():
        cell=meta.cell(i,j); cell.text=value
        for p in cell.paragraphs:
            p.paragraph_format.first_line_indent=Cm(0)
            for r in p.runs: font(r,10.5)
    blocks={5:[],8:[],11:[],14:[],18:[],21:[]}
    def P(k,s,**kw): blocks[k].append(para(doc,s,**kw))
    def H(k,s): blocks[k].append(head(doc,s))
    def T(k,h,r,w,size=9): blocks[k].append(table(doc,h,r,w,size))
    def M(k,lines): blocks[k].extend(mono(doc,lines))

    P(5,'通过捕获和分析真实 ARP 流量，理解 IPv4 地址如何解析为本链路的 MAC 地址；掌握请求、应答的字段及以太网封装，并能够用报文证据解释地址解析、地址探测和地址声明。')
    P(8,'先核对 WLAN 的 IP、MAC、网关及路由；以 arp 为捕获过滤器、关闭混杂模式，记录 WLAN 报文，并用绑定 WLAN 源地址的 ping 访问网关。随后检查第 5、6 帧，绘制交换图，回答手册问题，再分析其他可见 ARP 行为。')
    P(11,'Windows 11；Wireshark / TShark 4.6.8 与 Npcap；WLAN 网卡 MediaTek Wi-Fi 6E MT7922；使用系统网络配置、路由与邻居表、ping 和 TShark 核对。抓包时间为 2026 年 11 月 10 日 15:05 左右（北京时间）。')

    H(14,'4.1  网络环境与捕获方法')
    T(14,['项目','本次观测'],[
      ['本机 WLAN IPv4 / 前缀','172.31.240.50 / 16'],
      ['本机 WLAN MAC','14:ac:60:56:df:85'],
      ['WLAN 默认网关 / MAC','172.31.0.1 / 54:c6:ff:7b:38:02'],
      ['捕获配置','接口 WLAN；捕获过滤器 arp；非混杂模式；45 秒'],
      ['迹线','Lab4_ARP.pcapng：53 帧，40 个请求、13 个应答']],[5.0,11.7])
    P(14,'系统同时存在 singbox_tun 的默认路由，因此不能把系统所有流量都假定为经过 WLAN。本实验直接在 WLAN 接口捕获，并将 ping 的源地址指定为 172.31.240.50；这里讨论的是 WLAN 对应的网关，不据此推断其他流量的路径。')
    P(14,'捕获期间未清空 ARP 缓存，也未以网页请求作为工作负载。迹线中已自然出现对 WLAN 网关的请求和应答，足以完成字段与交换分析；不能证明第 5 帧一定由 ping 触发。网关地址与邻居表中相同映射交叉核对。')
    H(14,'4.2  请求与应答的字段比较')
    P(14,'在 Wireshark 中显示过滤器输入 frame.number == 5 || frame.number == 6，可并排定位两帧。第 5 帧询问 172.31.0.1 的 MAC，第 6 帧在 7.697 ms 后通告该映射；同一时段已有重复请求，ARP 无事务编号，因此将两帧作为时间与地址相符的一组分析，不断言应答只对应某一次请求。')
    blocks[14].extend(screenshot(doc))
    T(14,['字段','第 5 帧 请求','第 6 帧 应答'],[
      ['Ethernet 源 MAC','14:ac:60:56:df:85','54:c6:ff:7b:38:02'],
      ['Ethernet 目的 MAC','ff:ff:ff:ff:ff:ff（广播）','14:ac:60:56:df:85（单播）'],
      ['EtherType','0x0806（ARP）','0x0806（ARP）'],
      ['硬件类型 / 协议类型','1（Ethernet）/ 0x0800（IPv4）','1（Ethernet）/ 0x0800（IPv4）'],
      ['硬件长度 / 协议长度','6 B / 4 B','6 B / 4 B'],
      ['Opcode','1（request）','2（reply）'],
      ['发送方 IP / MAC','172.31.240.50\n14:ac:60:56:df:85','172.31.0.1\n54:c6:ff:7b:38:02'],
      ['目标 IP / MAC','172.31.0.1\n00:00:00:00:00:00','172.31.240.50\n14:ac:60:56:df:85']],[4.25,6.2,6.25],8.8)
    P(14,'请求中未知的是 ARP 目标 MAC，故该字段填零；外层 Ethernet 的目的 MAC 则为全 1 广播。应答中网关作为新的发送方，给出自己的 IP/MAC，本机作为目标；这两个不同层次的地址不能混为一谈。')
    P(14,'第 5 帧的 Ethernet Type 字节为 08 06，之后的 ARP 前 8 字节为 00 01 08 00 06 04 00 01，依次对应硬件类型、协议类型、两种地址长度和请求操作码。这些原始字节可以独立核对字段显示。')
    H(14,'4.3  ARP 交换示意图')
    blocks[14].extend(figure(doc,'图 2  本机解析 WLAN 网关地址的请求与应答（依据第 5、6 帧绘制）'))
    H(14,'4.4  报文字节结构与长度核对')
    P(14,'下面偏移以 ARP 报文起始处为 0，而非 Ethernet 帧起始处。Ethernet 首部的 14 字节位于 ARP 报文之前；硬件和协议地址长度分别为 6 和 4，因此本例 ARP 报文长度为 8 + 2×6 + 2×4 = 28 B。')
    T(14,['ARP 字节偏移','长度','字段','第 5 帧取值'],[
      ['0–1','2 B','硬件类型','00 01'],['2–3','2 B','协议类型','08 00'],
      ['4 / 5','各 1 B','硬件 / 协议地址长度','06 / 04'],['6–7','2 B','操作码','00 01'],
      ['8–13','6 B','发送方 MAC','14 ac 60 56 df 85'],['14–17','4 B','发送方 IPv4','ac 1f f0 32'],
      ['18–23','6 B','目标 MAC','00 00 00 00 00 00'],['24–27','4 B','目标 IPv4','ac 1f 00 01']],[3.1,2.0,5.0,6.6],8.8)
    P(14,'抓包中第 5 帧记录长度为 42 B，即 14 B Ethernet 首部 + 28 B ARP；第 6 帧记录 60 B，其中后 18 B 为 Ethernet padding，而非 ARP 首部。发送侧是否在抓包点之后补齐、无线链路的实际帧格式及 FCS 不可由这 42 B 直接推断。')
    H(14,'4.5  手册必答题')
    P(14,'（1）操作码：请求为 1，应答为 2。第 5、6 帧分别为 00 01、00 02。',indent=False)
    P(14,'（2）ARP 首部多大：本实验 Ethernet/IPv4 请求和应答均为 28 B；ARP 使用可变长地址，不能把 28 B 推广为所有硬件和协议的固定长度。',indent=False)
    P(14,'（3）未知目标 MAC 的值：本次请求的 ARP Target MAC 为 00:00:00:00:00:00；以太网目的地址为 ff:ff:ff:ff:ff:ff，两者含义不同。',indent=False)
    P(14,'（4）以太网类型：Ethernet II 的 Type 为 0x0806，表示载荷是 ARP；ARP 内部的 Protocol type 0x0800 则表示待解析的协议地址类型为 IPv4。',indent=False)
    P(14,'（5）应答是否广播：本次第 6 帧的目的 MAC 是本机 MAC，属于单播。普通地址解析通常单播应答，但 ARP 也存在广播应答等特殊用法，不能笼统断言所有应答均非广播。',indent=False)
    H(14,'4.6  拓展：探测、声明与单播请求')
    T(14,['帧号','可见事实','分析'],[
      ['4、7、8','发送方 IP 为 0.0.0.0；目标 IP 为 172.31.240.50','Wireshark 标为 ARP Probe；这与 RFC 5227 地址冲突探测报文格式一致。'],
      ['9、10','发送方和目标 IP 均为 172.31.240.50','Wireshark 标为 ARP Announcement / gratuitous；可向链路声明地址映射。'],
      ['11–13','请求的 Ethernet 目的和 ARP 目标 MAC 均为 54:c6:ff:7b:38:02','出现单播请求，说明“请求一定广播”并非普遍规律；仅凭迹线不能确定系统内部状态。']],[2.0,7.0,7.7],8.8)
    P(14,'本次未观察到其他主机发出的广播请求或本机发出的应答，不能由此断言网络中不存在这些活动。第 4 帧源 IP 为 0.0.0.0，也不应错误地归类为“发送方和目标 IP 相同”的地址声明。')
    P(18,'本次获得了网关请求、应答及地址声明的真实迹线。网关映射由第 6 帧的发送方 IP/MAC 及邻居表共同支持；第 5 帧的目标硬件地址为零，而外层广播地址全为 ff。以太网类型 0x0806 与 ARP 内部 IPv4 类型 0x0800 的作用不同。')
    P(18,'通过区分 28 B ARP 报文、Ethernet 首部、填充和抓包点记录长度，避免把链路层填充算进协议报文；第 11–13 帧的单播请求也说明结论必须保留适用条件。')
    P(21,'附录 A  复核文件与命令',indent=False,bold=True)
    P(21,'随报告提供的 Lab4_ARP.pcapng 为本次原始 53 帧迹线，可用 Wireshark 打开；过滤 frame.number == 5 || frame.number == 6 查看主要证据。',indent=False)
    M(21,['tshark -r Lab4_ARP.pcapng -Y "frame.number == 5 || frame.number == 6" -V',
          'tshark -r Lab4_ARP.pcapng -Y "arp.isprobe || arp.isannouncement"',
          'ping -S 172.31.240.50 172.31.0.1'])
    P(21,'附录 B  参考资料',indent=False,bold=True)
    P(21,'[1] 计算机网络实验手册，实验四 ARP。',indent=False,size=9)
    P(21,'[2] RFC 826, An Ethernet Address Resolution Protocol. https://www.rfc-editor.org/rfc/rfc826',indent=False,size=9)
    P(21,'[3] RFC 5227, IPv4 Address Conflict Detection. https://www.rfc-editor.org/rfc/rfc5227',indent=False,size=9)

    for idx,elements in blocks.items(): add_after(children[idx],elements)
    for idx in (5,8,11,14,15,18,21):
        el=children[idx]; el.getparent().remove(el)
    doc.core_properties.author='刘小凡'; doc.core_properties.title='Lab4 ARP 实验报告'
    doc.save(str(OUT))
    # Preserve template-only parts byte-for-byte. python-docx otherwise
    # reserializes untouched headers, footers, styles, and numbering.
    preserved={'_rels/.rels','word/header1.xml','word/footer1.xml',
               'word/header2.xml','word/_rels/header2.xml.rels',
               'word/numbering.xml','word/styles.xml'}
    with ZipFile(TEMPLATE) as src, ZipFile(OUT) as edited:
        parts=[(info, src.read(info.filename) if info.filename in preserved else edited.read(info.filename))
               for info in edited.infolist()]
        settings=etree.fromstring(src.read('word/settings.xml'))
        tag='{http://schemas.openxmlformats.org/wordprocessingml/2006/main}updateFields'
        node=settings.find(tag)
        if node is None:
            node=etree.SubElement(settings,tag)
        node.set('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}val','true')
        settings_bytes=etree.tostring(settings,xml_declaration=True,encoding='UTF-8',standalone=True)
    tmp=WORK / 'report_repacked.docx'
    with ZipFile(tmp,'w') as dst:
        for info,data in parts:
            dst.writestr(info, settings_bytes if info.filename=='word/settings.xml' else data)
    tmp.replace(OUT)
    print('SAVED',OUT)

if __name__=='__main__': main()
