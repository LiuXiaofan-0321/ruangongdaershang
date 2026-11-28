# -*- coding: utf-8 -*-
"""package_lab5.py - build Lab5_实测数据与截图.zip with strict manifest & integrity check."""
import json
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab5_work"
EV = WORK / "evidence"
OUT = ROOT / "Lab5_实测数据与截图.zip"
F = json.loads((WORK / "facts.json").read_text(encoding="utf-8"))

SHOTS = [
    "01_ipconfig.png", "01b_route_udp.png", "02_workload.png",
    "03_capture_options.png", "04_trace_overview.png",
    "05_frame10_ntp_fields.png", "06_frame7_dns_fields.png",
    "07_udp_bytes_highlight.png", "08_ip_protocol_17.png",
    "09_checksum_zero.png", "10_udp_preferences.png",
    "11_mdns_multicast.png", "12_quic_large.png",
]
DIAGRAMS = ["fig_udp_message_structure.png", "fig_udp_traffic_analysis.png"]
SCRIPTS = ["analyze.py", "make_diagrams.py", "build_lab5.py", "check_lab5.py"]
MISC = ["facts.json", "workload_log.txt"]

README = f"""Lab5 UDP 实验 —— 实测数据与截图
==================================

学生：刘小凡  学号：10244602411  年级：2025 级  实验日期：2026-11-28

目录
----
captures/   原始抓包 Lab5_UDP.pcapng（{F['frame_count']} 帧，时长 {F['duration_s']} s）
evidence/   报告中使用的 13 张真实软件截图与 2 张原创绘制示意图（已剔除中间探测截图）
scripts/    分析、绘图、生成与验收脚本
facts.json  analyze.py 从 pcapng 原始字节解析与校验和验算产生的全量统计数据
workload_log.txt  捕获期间 nslookup、w32tm 与浏览器工作负载原始记录

实测结论摘要（均可在 facts.json 与迹线中复核）
----------------------------------------------
接口构成      singbox_tun {F['interfaces']['singbox_tun']} 帧（Raw IP，无以太网首部）+ WLAN {F['interfaces']['WLAN']} 帧（Ethernet II 14 B）
协议构成      DNS {F['protocols']['DNS']}、UDP {F['protocols']['UDP']}、QUIC {F['protocols']['QUIC']}、MDNS {F['protocols']['MDNS']}、NTP {F['protocols']['NTP']}
IP Protocol   全部 {F['frame_count']} 帧均为 17（0x11）
UDP 首部      固定 8 B（4 个 16 位字段：源端口、目的端口、Length、Checksum）
Length 口径   UDP 首部 8 B + UDP 载荷（第 10 帧 56 = 8 + 48；第 7 帧 39 = 8 + 31）
零校验和      {F['checksum']['zero_total']} 帧（43.5%）为 0x0000，全部为 singbox_tun 接收方向注入报文；WLAN 28 帧均非零且 RFC 768 验算通过
报文长度分布  Min={F['udp_length_stats']['min']} B，Median={F['udp_length_stats']['median']} B，P90={F['udp_length_stats']['p90']} B，Max={F['udp_length_stats']['max']} B（QUIC 1258 B）；{F['udp_length_stats']['le_400_pct']}% <= 400 B
多播与偏差    实测 mDNS 目的地址 224.0.0.251（9 帧）；严格双非本机 IP 筛选为 0 帧（无混杂模式、NetBIOS 已禁用且无线局域网未收到他机广播）

复核方法
--------
python scripts/analyze.py
"""


def main():
    if OUT.exists():
        OUT.unlink()
    n = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Lab5_实测数据与截图_说明.txt", README)
        n += 1
        cap = WORK / "Lab5_UDP.pcapng"
        z.write(cap, "captures/Lab5_UDP.pcapng")
        n += 1
        for name in SHOTS + DIAGRAMS:
            p = EV / name
            if not p.is_file():
                raise SystemExit(f"Missing evidence file: {p}")
            z.write(p, f"evidence/{name}")
            n += 1
        for name in SCRIPTS:
            p = WORK / name
            if not p.is_file():
                raise SystemExit(f"Missing script: {p}")
            z.write(p, f"scripts/{name}")
            n += 1
        for name in MISC:
            p = WORK / name
            if not p.is_file():
                raise SystemExit(f"Missing misc file: {p}")
            z.write(p, name)
            n += 1

    size_mb = OUT.stat().st_size / 1024 / 1024
    print(f"WROTE {OUT}  {size_mb:.2f} MB  files={n}")
    with zipfile.ZipFile(OUT) as z:
        bad = z.testzip()
        print("zip integrity:", "OK" if bad is None else f"CORRUPT: {bad}")
        for name in sorted(z.namelist()):
            print("   ", name)


if __name__ == "__main__":
    main()
