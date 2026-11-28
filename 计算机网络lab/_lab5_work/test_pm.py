# -*- coding: utf-8 -*-
import ctypes
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\University Courses\计算机网络lab\_lab5_work")
import win_cap

u = ctypes.windll.user32
WM_LBUTTONDOWN = 0x0201
WM_LBUTTONUP = 0x0202
WM_LBUTTONDBLCLK = 0x0203
WM_MOUSEMOVE = 0x0200
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
    time.sleep(0.35)

WS = r"C:\Program Files\Wireshark\Wireshark.exe"
CAP = r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"
EV = Path(r"C:\University Courses\计算机网络lab\_lab5_work\evidence")

p = subprocess.Popen([WS, "-r", CAP, "-g", "10"])
hwnd = None
for _ in range(25):
    time.sleep(0.5)
    for w in win_cap.find_windows():
        if "Lab5_UDP" in w["title"]:
            hwnd = w["hwnd"]
            break
    if hwnd:
        break

time.sleep(2.0)
u.ShowWindow(hwnd, 3)
time.sleep(0.7)

# In window image (2906x1730) with rect (-13,-13), client (cx, cy) = (img_x - 13, img_y - 13)
# Let's click UDP row: img_y ≈ 700 -> cy ≈ 687, cx = 280
post_click(hwnd, 280, 687, double=False)
res1 = win_cap.capture_hwnd(hwnd, EV / "test_pm_click.png", max_width=2000)
print("click:", res1)

post_click(hwnd, 280, 687, double=True)
res2 = win_cap.capture_hwnd(hwnd, EV / "test_pm_dblclick.png", max_width=2000)
print("dblclick:", res2)

p.terminate()
