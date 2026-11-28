# -*- coding: utf-8 -*-
import subprocess
import time
from pathlib import Path

TSHARK = r"C:\Program Files\Wireshark\tshark.exe"
WORK = Path(r"C:\University Courses\计算机网络lab\_lab5_work")
WLAN_IF = r"\Device\NPF_{C59C96C9-17AD-4F4E-ADD7-2E166380D039}"

out = WORK / "probe_wlan40.pcapng"
if out.exists():
    out.unlink()

p = subprocess.Popen([
    TSHARK, "-i", WLAN_IF, "-f", "udp", "-p", "-a", "duration:35", "-w", str(out)
], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

time.sleep(2)
# Open a couple of sites via PowerShell / Edge or curl, and also send a DNS query to 223.5.5.5
subprocess.run(["curl.exe", "-s", "--http3", "-I", "--max-time", "5", "https://quic.nginx.org"], capture_output=True)
subprocess.run(["curl.exe", "-s", "-I", "--max-time", "5", "https://www.bilibili.com"], capture_output=True)
subprocess.run(["nslookup", "www.fudan.edu.cn", "223.5.5.5"], capture_output=True)

stdout, stderr = p.communicate(timeout=45)
print("rc:", p.returncode, "stderr:", stderr.strip())
res = subprocess.run([
    TSHARK, "-r", str(out), "-T", "fields",
    "-e", "frame.number", "-e", "frame.time_relative", "-e", "ip.src", "-e", "ip.dst",
    "-e", "ipv6.src", "-e", "ipv6.dst",
    "-e", "_ws.col.Protocol", "-e", "udp.srcport", "-e", "udp.dstport",
    "-e", "udp.length", "-e", "udp.checksum", "-e", "_ws.col.Info"
], capture_output=True, text=True, encoding="utf-8", errors="replace")
lines = res.stdout.splitlines()
print(f"Captured {len(lines)} frames on WLAN:")
for ln in lines[:60]:
    print(" ", ln)
