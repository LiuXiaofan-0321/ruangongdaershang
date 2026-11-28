# -*- coding: utf-8 -*-
"""capture_lab5.py - capture live UDP traffic on WLAN + singbox_tun for Lab 5."""
import subprocess
import time
from collections import Counter
from pathlib import Path

TSHARK = r"C:\Program Files\Wireshark\tshark.exe"
WORK = Path(r"C:\University Courses\计算机网络lab\_lab5_work")
CAP = WORK / "Lab5_UDP.pcapng"
LOG = WORK / "workload_log.txt"

WLAN_IF = r"\Device\NPF_{C59C96C9-17AD-4F4E-ADD7-2E166380D039}"
TUN_IF = r"\Device\NPF_{B738A021-9842-444C-10B0-A4E3F65AB5B6}"

def main():
    if CAP.exists():
        CAP.unlink()

    print("Starting 75s tshark UDP capture (promiscuous OFF)...")
    t0 = time.time()
    p = subprocess.Popen([
        TSHARK,
        "-i", WLAN_IF, "-f", "udp", "-p",
        "-i", TUN_IF, "-f", "udp", "-p",
        "-a", "duration:75",
        "-w", str(CAP),
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")

    time.sleep(2.5)
    logs = []

    def run_cmd(label, cmd, timeout=15):
        logs.append(f"=== {label} (t={time.time()-t0:.1f}s) ===")
        logs.append("$ " + " ".join(cmd))
        try:
            r = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=timeout)
            if r.stdout.strip():
                logs.append(r.stdout.strip())
            if r.stderr.strip():
                logs.append("[stderr] " + r.stderr.strip())
        except Exception as e:
            logs.append(f"[error] {e}")
        logs.append("")

    run_cmd("DNS lookup 1", ["nslookup", "www.baidu.com"])
    run_cmd("DNS lookup 2", ["nslookup", "www.ecnu.edu.cn"])
    run_cmd("DNS lookup 3 (AliDNS)", ["nslookup", "www.tsinghua.edu.cn", "223.5.5.5"])
    run_cmd("NTP stripchart", ["w32tm", "/stripchart", "/computer:ntp.aliyun.com", "/samples:2", "/dataonly"])

    # Trigger browser QUIC / DNS / SSDP / mDNS activity
    edge = r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
    for url in ["https://www.baidu.com", "https://www.bilibili.com"]:
        logs.append(f"=== Edge browse {url} (t={time.time()-t0:.1f}s) ===")
        try:
            subprocess.run([edge, "--headless=new", "--dump-dom", url],
                           capture_output=True, timeout=10)
            logs.append("OK")
        except Exception as e:
            logs.append(f"[done/timeout] {e}")
        logs.append("")

    logs.append(f"=== Activity stopped at t={time.time()-t0:.1f}s; waiting for background UDP traffic until 75s ===")
    stdout, stderr = p.communicate(timeout=90)
    logs.append(f"tshark rc={p.returncode}, stderr={stderr.strip()}")

    LOG.write_text("\n".join(logs), encoding="utf-8")

    # Quick summary
    res = subprocess.run([
        TSHARK, "-r", str(CAP), "-T", "fields",
        "-e", "frame.interface_name", "-e", "_ws.col.Protocol",
        "-e", "ip.src", "-e", "ip.dst"
    ], capture_output=True, text=True, encoding="utf-8", errors="replace")
    ifaces = Counter()
    protos = Counter()
    non_self = []
    self_ips = {"192.168.31.134", "172.18.0.1", ""}
    for i, ln in enumerate(res.stdout.splitlines(), 1):
        cols = ln.split("\t")
        if len(cols) >= 4:
            ifaces[cols[0]] += 1
            protos[cols[1]] += 1
            if cols[2] not in self_ips and cols[3] not in self_ips:
                non_self.append((i, cols[1], cols[2], cols[3]))
    print("Interfaces:", dict(ifaces))
    print("Protocols:", dict(protos))
    print("Non-self IPv4 packets:", len(non_self), non_self[:10])

if __name__ == "__main__":
    main()
