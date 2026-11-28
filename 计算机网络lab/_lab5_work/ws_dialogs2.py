# -*- coding: utf-8 -*-
"""ws_dialogs2.py - capture 03_capture_options.png and probe Edit->Preferences."""
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
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
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
        time.sleep(0.04)

WS = r"C:\Program Files\Wireshark\Wireshark.exe"
CAP = r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"
EV = Path(r"C:\University Courses\计算机网络lab\_lab5_work\evidence")

# 1. Capture Options -> select WLAN + type udp
p = subprocess.Popen([WS])
time.sleep(9.0)
main_w = [w for w in win_cap.find_windows() if "Wireshark" in w["title"]][0]
u.ShowWindow(main_w["hwnd"], 3)
time.sleep(0.6)
post_click(main_w["hwnd"], 165, 67)
time.sleep(0.8)
dlg = [w for w in win_cap.find_windows() if "捕获选项" in w["title"] or "Capture Options" in w["title"]][0]
dhwnd = dlg["hwnd"]
wr = wintypes.RECT(); u.GetWindowRect(dhwnd, ctypes.byref(wr))
pt = wintypes.POINT(0, 0); u.ClientToScreen(dhwnd, ctypes.byref(pt))
dx = pt.x - wr.left
dy = pt.y - wr.top
print(f"Dialog offset dx={dx}, dy={dy}")
# Click WLAN row (img x=260, y=392)
post_click(dhwnd, 260 - dx, 392 - dy)
time.sleep(0.3)
# Click Capture filter box (img x=650, y=855)
post_click(dhwnd, 650 - dx, 855 - dy)
time.sleep(0.3)
post_text(dhwnd, "udp")
time.sleep(0.4)
print("03_capture_options:", win_cap.capture_hwnd(dhwnd, EV / "03_capture_options.png", max_width=2000))
p.terminate()
time.sleep(1.0)

# 2. Preferences: click 编辑(E) at (135, 22) or Alt+E
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
u.PostMessageW(hwnd, WM_SYSKEYDOWN, 0x45, 0x20000001)  # Alt+E
time.sleep(0.15)
u.PostMessageW(hwnd, WM_SYSKEYUP, 0x45, 0xE0000001)
time.sleep(0.5)
print("After Alt+E wins:", win_cap.find_windows())
# Also press 'P' (0x50) to open Preferences if Edit menu is open
u.PostMessageW(hwnd, 0x0100, 0x50, 0)
time.sleep(0.1)
u.PostMessageW(hwnd, 0x0101, 0x50, 0)
time.sleep(0.8)
print("After P wins:", win_cap.find_windows())
for w in win_cap.find_windows():
    if "首选项" in w["title"] or "Preferences" in w["title"]:
        win_cap.capture_hwnd(w["hwnd"], EV / "_probe_prefs.png", max_width=None)
p.terminate()
