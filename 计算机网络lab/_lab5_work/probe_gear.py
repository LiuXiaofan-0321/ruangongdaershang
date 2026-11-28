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
WM_MOUSEMOVE = 0x0200
MK_LBUTTON = 0x0001

def post_click(hwnd, cx, cy):
    lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
    u.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.03)
    u.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
    time.sleep(0.03)
    u.PostMessageW(hwnd, WM_LBUTTONUP, 0, lp)
    time.sleep(0.5)

WS = r"C:\Program Files\Wireshark\Wireshark.exe"
CAP = r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"

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
time.sleep(0.7)

# Test clicking gear icon (x_img=178, y_img=125) with cy offsets
for cy in [125, 145, 165, 182]:
    post_click(hwnd, 165, cy)
    wins = win_cap.find_windows()
    print(f"After gear click cy={cy}:", [w["title"] for w in wins])
    if len(wins) > 1:
        break

p.terminate()
