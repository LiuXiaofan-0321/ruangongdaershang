# -*- coding: utf-8 -*-
"""probe_ws.py - open Lab5_UDP.pcapng in Wireshark, wait until loaded, grab full-res overview."""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\University Courses\计算机网络lab\_lab5_work")
import win_cap

CAP = r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"
OUT = r"C:\University Courses\计算机网络lab\_lab5_work\evidence\04_trace_overview.png"

p = subprocess.Popen([r"C:\Program Files\Wireshark\Wireshark.exe", "-r", CAP, "-g", "1"])
hwnd = None
for _ in range(30):
    time.sleep(0.5)
    wins = win_cap.find_windows()
    for w in wins:
        if "Lab5_UDP" in w["title"]:
            hwnd = w["hwnd"]
            break
    if hwnd:
        break

if not hwnd:
    p.terminate()
    raise RuntimeError(f"Wireshark capture window not found: {win_cap.find_windows()}")

time.sleep(2.0)
win_cap.focus_hwnd(hwnd)
res = win_cap.capture_hwnd(hwnd, OUT, max_width=None, maximize=True)
print("Overview:", res)
p.terminate()
