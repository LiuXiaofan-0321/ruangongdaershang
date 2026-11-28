# -*- coding: utf-8 -*-
import subprocess
import time
from pathlib import Path

TSHARK = r"C:\Program Files\Wireshark\tshark.exe"
WORK = Path(r"C:\University Courses\计算机网络lab\_lab5_work")
WLAN_IF = r"\Device\NPF_{C59C96C9-17AD-4F4E-ADD7-2E166380D039}"
TUN_IF = r"\Device\NPF_{B738A021-9842-444C-10B0-A4E3F65AB5B6}"

def probe_iface(iface, out_name, dur=12):
    out = WORK / out_name
    if out.exists():
        out.unlink()
    p = subprocess.Popen([
        TSHARK, "-i", iface, "-f", "udp", "-p", "-a", f"duration:{dur}", "-w", str(out)
    ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    time.sleep(1.5)
    # Trigger DNS + web requests
    subprocess.run(["nslookup", "www.baidu.com"], capture_output=True)
    subprocess.run(["nslookup", "www.ecnu.edu.cn"], capture_output=True)
    subprocess.run(["nslookup", "www.tsinghua.edu.cn", "223.5.5.5"], capture_output=True)
    subprocess.run(["curl.exe", "-s", "-I", "--max-time", "4", "https://www.baidu.com"], capture_output=True)
    stdout, stderr = p.communicate(timeout=dur + 10)
    print(f"=== {out_name} (rc={p.returncode}) ===")
    if stderr.strip():
        print("stderr:", stderr.strip())
    if out.exists():
        res = subprocess.run([
            TSHARK, "-r", str(out), "-T", "fields",
            "-e", "frame.number", "-e", "ip.src", "-e", "ip.dst",
            "-e", "_ws.col.Protocol", "-e", "udp.srcport", "-e", "udp.dstport",
            "-e", "udp.length", "-e", "udp.checksum", "-e", "_ws.col.Info"
        ], capture_output=True, text=True, encoding="utf-8", errors="replace")
        lines = res.stdout.splitlines()
        print(f"Captured {len(lines)} frames:")
        for ln in lines[:40]:
            print(" ", ln)

if __name__ == "__main__":
    probe_iface(WLAN_IF, "probe_wlan.pcapng", 15)
    probe_iface(TUN_IF, "probe_tun.pcapng", 10)
