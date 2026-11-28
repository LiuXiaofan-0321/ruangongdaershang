# -*- coding: utf-8 -*-
import subprocess
import time
from pathlib import Path

TSHARK = r"C:\Program Files\Wireshark\tshark.exe"
WORK = Path(r"C:\University Courses\计算机网络lab\_lab5_work")
WLAN_IF = r"\Device\NPF_{C59C96C9-17AD-4F4E-ADD7-2E166380D039}"
TUN_IF = r"\Device\NPF_{B738A021-9842-444C-10B0-A4E3F65AB5B6}"

out = WORK / "probe_both.pcapng"
if out.exists():
    out.unlink()

p = subprocess.Popen([
    TSHARK, "-i", WLAN_IF, "-i", TUN_IF, "-f", "udp", "-p",
    "-a", "duration:25", "-w", str(out)
], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

time.sleep(2)
# Launch Edge briefly to browse real sites (Baidu, ECNU, Bilibili)
subprocess.Popen([
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    "--headless=new", "--dump-dom", "https://www.bilibili.com"
], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
subprocess.run(["nslookup", "www.baidu.com"], capture_output=True)
subprocess.run(["nslookup", "www.ecnu.edu.cn"], capture_output=True)
subprocess.run(["nslookup", "www.pku.edu.cn", "223.5.5.5"], capture_output=True)

stdout, stderr = p.communicate(timeout=35)
print("rc:", p.returncode, "stderr:", stderr.strip())

res = subprocess.run([
    TSHARK, "-r", str(out), "-T", "fields",
    "-e", "frame.number", "-e", "frame.interface_name",
    "-e", "ip.src", "-e", "ip.dst",
    "-e", "_ws.col.Protocol", "-e", "udp.srcport", "-e", "udp.dstport",
    "-e", "udp.length", "-e", "udp.checksum", "-e", "_ws.col.Info"
], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()
print(f"Captured {len(lines)} frames:")
from collections import Counter
protos = Counter()
ifaces = Counter()
for ln in lines:
    cols = ln.split("\t")
    if len(cols) >= 5:
        ifaces[cols[1]] += 1
        protos[cols[4]] += 1
print("Interfaces:", dict(ifaces))
print("Protocols:", dict(protos))
for ln in lines[:40]:
    print(" ", ln)
