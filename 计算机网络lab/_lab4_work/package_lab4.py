# -*- coding: utf-8 -*-
"""package_lab4.py - build "Lab4_实测数据与截图.zip" for the ARP report.

Contents: the raw capture, the 10 real screenshots, the 2 original diagrams, the
analysis/diagram/build scripts, and the derived facts. The intermediate _obs*
probe screenshots and the QA renders are deliberately excluded.
"""
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab4_work"
EV = WORK / "evidence"
OUT = ROOT / "Lab4_实测数据与截图.zip"

SHOTS = [
    "01_ipconfig.png", "02_arp_cache.png", "03_route.png",
    "04_arp_request_fields.png", "05_arp_reply_fields.png",
    "06_arp_overview.png", "07_ethertype_bytes.png",
    "08_eth_addr_filter.png", "09_gratuitous_arp.png",
    "10_gateway_exchange.png",
]
DIAGRAMS = ["fig_arp_exchange.png", "fig_arp_header.png"]
SCRIPTS = ["analyze.py", "make_diagrams.py", "build_lab4.py", "check_lab4.py"]
MISC = ["facts.json", "ping_gateway.txt"]

README = """Lab4 ARP 实验 —— 实测数据与截图
==================================

学生：刘小凡  学号：10244602411  实验日期：2026-11-03

目录
----
captures/   原始抓包 Lab4_ARP.pcapng（53 帧，全部为 ARP）
evidence/   报告中使用的 10 张真实软件截图与 2 张绘制示意图
scripts/    分析、绘图与生成脚本
facts.json  脚本从 pcapng 原始字节解析出的全部关键数值
ping_gateway.txt  工作负载 ping 的实际输出

实测结论（均可在 facts.json 与迹线中复核）
------------------------------------------
本机      172.31.240.50   14:ac:60:56:df:85
默认网关  172.31.0.1      54:c6:ff:7b:38:02

帧数构成      53 帧：请求 40、应答 13
请求（第 1 帧） 42 B = 14 B 以太网首部 + 28 B ARP，以太网目的 ff:ff:ff:ff:ff:ff
应答（第 6 帧） 60 B = 14 B 以太网首部 + 28 B ARP + 18 B 以太网填充，
                 以太网目的 14:ac:60:56:df:85（单播）
ARP 报文长度    请求与应答均为 28 B
操作码          请求 1、应答 2
以太网类型      0x0806
请求中的目标 MAC 00:00:00:00:00:00（未知，填零）

其他行为        6 个 ARP 探测（帧 4、7、8、33、35、46，发送方 IP 为 0.0.0.0）
                 4 个免费 ARP 通告（帧 9、10、48、49，发送方 IP 与目标 IP 相同）
                 3 个以太网目的为单播的请求（帧 11、12、13）

需要说明的实验条件
------------------
本次以普通用户身份运行，无法执行 arp -d 清空缓存；工作负载也不是手册建议的浏览器
访问网页，而是绑定了 WLAN 源地址的 ping。因此报告只陈述观测到的事实，不推断这次
请求由哪个操作触发。字段与长度分析不受该偏差影响。

复核方法
--------
python scripts/analyze.py     # 重新解析 pcapng，重算长度与字段，输出 facts.json
tshark -r captures/Lab4_ARP.pcapng -T fields -e arp.opcode \\
       -e arp.src.hw_mac -e arp.dst.hw_mac -e arp.src.proto_ipv4 -e arp.dst.proto_ipv4
"""


def main():
    if OUT.exists():
        OUT.unlink()
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Lab4_实测数据与截图_说明.txt", README)
        n += 1
        cap = WORK / "Lab4_ARP.pcapng"
        if not cap.is_file():
            cap = ROOT / "Lab4_ARP.pcapng"
        z.write(cap, "captures/Lab4_ARP.pcapng")
        n += 1
        for name in SHOTS + DIAGRAMS:
            p = EV / name
            if p.is_file():
                z.write(p, f"evidence/{name}")
                n += 1
            else:
                print("  missing:", name)
        for name in SCRIPTS:
            p = WORK / name
            if p.is_file():
                z.write(p, f"scripts/{name}")
                n += 1
        for name in MISC:
            p = WORK / name
            if p.is_file():
                z.write(p, name)
                n += 1
    size = OUT.stat().st_size / 1024 / 1024
    print(f"WROTE {OUT}  {size:.2f} MB  files={n}")
    with zipfile.ZipFile(OUT) as z:
        print("zip integrity:", "OK" if z.testzip() is None else "CORRUPT")
        for name in sorted(z.namelist()):
            print("   ", name)


if __name__ == "__main__":
    main()
