# -*- coding: utf-8 -*-
"""package_lab3.py - build the "实测数据与截图.zip" deliverable.

Contains the evidence that supports the report: the target HTTP trace, the
verified path trace, the native (tunnel-affected) trace kept as failure evidence,
the 8 Wireshark screenshots actually used, the 2 original diagrams, the analysis
and diagram scripts, and the key logs.

Deliberately EXCLUDED: unrelated background HTTP from the raw 108-frame capture,
QA page renders/PDF, and the ~40 intermediate obs_* observation screenshots.

Usage: python package_lab3.py
"""
import sys
import zipfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab3_work"
EV = WORK / "evidence"
LOGS = WORK / "logs"
OUT = ROOT / "实测数据与截图.zip"

EVIDENCE = [
    "01_capture_options.png",
    "02_name_resolution.png",
    "04_outgoing_ipv4.png",
    "05_incoming_checksum.png",
    "06_http_200_stream.png",
    "07_id_ttl_fragmentation.png",
    "08_path_status.png",
    "08_path_ttl_probes.png",
    "09_icmp_time_exceeded.png",
    "fig_A_ipv4_structure.png",
    "fig_B_path.png",
]
CAPTURES = [
    "Lab3_HTTP_target.pcapng",
    "Lab3_Path_WLAN.pcapng",
    "Lab3_Traceroute.pcapng",
]
SCRIPTS = ["analyze.py", "make_diagrams.py", "source_trace.py"]
LOGFILES = [
    "source_trace.json", "source_trace.txt", "tracert.txt", "ptr.json",
    "rdap_summary.json", "rdap_202.120.95.246.json", "rdap_101.4.116.61.json",
    "rdap_219.224.103.65.json", "rdap_182.61.255.32.json",
    "ipconfig.txt", "curl.txt", "http_headers.txt", "wireshark_version.txt",
    "Lab3_HTTP_target.tsv", "Lab3_Path_WLAN.tsv",
]

README = """Lab3 IPv4 实验 —— 实测数据与截图
=====================================

学生：刘小凡  学号：10244602411  实验日期：2026-10-13

目录结构
--------
captures/   原始抓包文件（真实测量结果）
evidence/   报告中使用的 8 张 Wireshark 截图与 2 张绘制示意图
logs/       字段提取、路径结果、地址登记查询与命令输出
scripts/    分析脚本（字段提取与校验和独立验算）
facts.json  脚本从 pcapng 原始字节解析出的全部关键数值

captures 说明
-------------
Lab3_HTTP_target.pcapng   目标 HTTP 连接，19 帧（本机发 10、接收 9），报告主要依据
Lab3_Path_WLAN.pcapng     绑定 WLAN 源地址的逐跳探测，76 帧（51 请求 + 23 Time
                          Exceeded + 2 Echo Reply），TTL 1–17 每跳 3 次
Lab3_Traceroute.pcapng    普通 tracert 的 WLAN 迹线，用作隧道干扰的故障证据：
                          其 Echo 请求 TTL 全为 128 而非逐跳递增，故不能作为路径依据

未包含的内容
------------
- 抓包原始迹线 Lab3_HTTP.pcapng（108 帧）含其他应用的背景 HTTP 流量，与本次
  实验无关，故未纳入交付包；如需可向作者索取。
- 中间过程的观察截图（obs_*）与渲染检查用 PDF/页面图，均不属于证据。

关于数值的可复核性
------------------
report 中的字段、计数与校验和不是从截图抄录，而是由 scripts/analyze.py 直接读取
pcapng 原始字节重新解析并断言得到，结果写入 facts.json，可与 Wireshark 界面
显示互相验证。

IPv4 首部校验和（第 5 帧）复核要点
----------------------------------
首部 45 00 00 28 b7 3c 40 00 28 06 cb 73 b6 3d c8 6c ac 1f a5 56
10 个 16 位字普通累加得 0x4fffb，回卷（高 16 位 0x0004 + 低 16 位 0xfffb）
得 0xffff，即 1 的补码负零；把校验和字段置零后其余 9 字累加得 0x43488，
回卷得 0x348c，取反得 0xcb73，与实收校验和及 Wireshark 的 [correct] 一致。
"""


def main():
    if OUT.exists():
        OUT.unlink()
    added = 0
    with zipfile.ZipFile(OUT, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("Lab3_实测数据与截图_说明.txt", README)
        for name in EVIDENCE:
            p = EV / name
            if p.is_file():
                z.write(p, f"evidence/{name}")
                added += 1
        for name in CAPTURES:
            p = WORK / "captures" / name
            if p.is_file():
                z.write(p, f"captures/{name}")
                added += 1
        for name in SCRIPTS:
            p = WORK / name
            if p.is_file():
                z.write(p, f"scripts/{name}")
                added += 1
        for name in LOGFILES:
            p = LOGS / name
            if p.is_file():
                z.write(p, f"logs/{name}")
                added += 1
        fj = WORK / "facts.json"
        if fj.is_file():
            z.write(fj, "facts.json")
            added += 1
    print(f"WROTE {OUT}  {OUT.stat().st_size/1024/1024:.2f} MB  files={added + 1}")
    with zipfile.ZipFile(OUT) as z:
        bad = z.testzip()
        print("zip integrity:", "OK" if bad is None else f"CORRUPT at {bad}")
        for n in sorted(z.namelist()):
            print("   ", n)


if __name__ == "__main__":
    main()
