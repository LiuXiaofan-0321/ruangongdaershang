# -*- coding: utf-8 -*-
"""ws_dialogs.py - capture 03_capture_options.png and 10_udp_preferences.png via PostMessageW."""
import ctypes
import subprocess
import sys
import time
from ctypes import wintypes
from pathlib import Path

sys.path.insert(0, r"C:\University Courses\计算机网络lab\_lab5_work")
import win_cap

u = ctypes.windll.user32
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_MOUSEMOVE = 0x0200
WM_CHAR = 0x0102
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
MK_LBUTTON = 0x0001

def post_click(hwnd, cx, cy):
    lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
    u.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.03)
    u.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(0.03)
    u.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(0.4)

def post_text(hwnd, text):
    for ch in text:
        u.PostMessageW(hwnd, WM_CHAR, ord(ch), 0)
        time.sleep(0.03)

WS = r"C:\Program Files\Wireshark\Wireshark.exe"
CAP = r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"
EV = Path(r"C:\University Courses\计算机网络lab\_lab5_work\evidence")

# 1. Capture Options dialog
p = subprocess.Popen([WS])
time.sleep(9.0)
main_w = [w for w in win_cap.find_windows() if "Wireshark" in w["title"]][0]
u.ShowWindow(main_w["hwnd"], 3)
time.sleep(0.6)
# Click gear icon (165, 67)
post_click(main_w["hwnd"], 165, 67)
time.sleep(0.8)
dlg = [w for w in win_cap.find_windows() if "捕获选项" in w["title"] or "Capture Options" in w["title"]][0]
print("Capture Options dlg:", dlg)
win_cap.capture_hwnd(dlg["hwnd"], EV / "_probe_capopts.png", max_width=None)
p.terminate()
time.sleep(1.0)

# 2. Preferences dialog: open Lab5_UDP, click 编辑(E) menu at (135, 17)
p = subprocess.Popen([WS, "-r", CAP, "-g", "10"])
hwnd = None
for _ in range(30):
    time.sleep(0.5)
    for w in win_cap.find_windows():
        if "Lab5_UDP" in w["title"]:
            hwnd = w["hwnd"]
            break
    if hwnd:
        break
time.sleep(2.0)
u.ShowWindow(hwnd, 3)
time.sleep(0.6)
# Click 编辑(E) at cx=135, cy=17 -> grab full window to see menu dropdown!
post_click(hwnd, 135, 17)
time.sleep(0.5)
win_cap.capture_hwnd(hwnd, EV / "_probe_editmenu.png", max_width=None)
p.terminate()
