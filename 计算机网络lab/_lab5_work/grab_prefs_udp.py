# -*- coding: utf-8 -*-
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
WM_LBUTTONDBLCLK = 0x0203
WM_MOUSEMOVE = 0x0200
WM_CHAR = 0x0102
MK_LBUTTON = 0x0001

def post_click(hwnd, cx, cy, double=False):
    lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
    u.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.03)
    u.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(0.03)
    u.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    if double:
        time.sleep(0.05)
        u.PostMessageW(hwnd, WM_LBUTTONDBLCLK, MK_LBUTTON, lp)
        time.sleep(0.03)
        u.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(0.45)

WS = r"C:\Program Files\Wireshark\Wireshark.exe"
CAP = r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"
EV = Path(r"C:\University Courses\计算机网络lab\_lab5_work\evidence")

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

post_click(hwnd, 135, 22)
menu_w = [w for w in win_cap.find_windows() if w["hwnd"] != hwnd][0]
u.PostMessageW(menu_w["hwnd"], 0x0100, 0x26, 0x01480001)  # VK_UP
time.sleep(0.1)
u.PostMessageW(menu_w["hwnd"], 0x0101, 0x26, 0xC1480001)
time.sleep(0.15)
u.PostMessageW(menu_w["hwnd"], 0x0100, 0x0D, 0x001C0001)  # VK_RETURN
time.sleep(0.1)
u.PostMessageW(menu_w["hwnd"], 0x0101, 0x0D, 0xC01C0001)
time.sleep(0.8)

pref_w = [w for w in win_cap.find_windows() if "首选项" in w["title"] or "Preferences" in w["title"]][0]
phwnd = pref_w["hwnd"]
wr = wintypes.RECT(); u.GetWindowRect(phwnd, ctypes.byref(wr))
pt = wintypes.POINT(0, 0); u.ClientToScreen(phwnd, ctypes.byref(pt))
dx, dy = pt.x - wr.left, pt.y - wr.top

# Double-click Protocols at img (90, 118)
post_click(phwnd, 90 - dx, 118 - dy, double=True)
time.sleep(0.4)
# Type "udp" into the focused tree view to jump directly to UDP!
for ch in "udp":
    u.PostMessageW(phwnd, WM_CHAR, ord(ch), 0)
    time.sleep(0.06)
time.sleep(0.5)
print("10_udp_preferences:", win_cap.capture_hwnd(phwnd, EV / "10_udp_preferences.png", max_width=2000))
p.terminate()
