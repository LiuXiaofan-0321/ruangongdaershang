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
WM_MOUSEMOVE = 0x0200
MK_LBUTTON = 0x0001

def post_click(hwnd, cx, cy):
    lp = (int(cy) << 16) | (int(cx) & 0xFFFF)
    u.PostMessageW(hwnd, WM_MOUSEMOVE, 0, lp)
    time.sleep(0.03)
    u.PostMessageW(hwnd, WM_LBUTTONDOWN, MK_LBUTTON, lp)
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
u.PostMessageW(menu_w["hwnd"], 0x0100, 0x26, 0x01480001)  # VK_UP (extended)
time.sleep(0.1)
u.PostMessageW(menu_w["hwnd"], 0x0101, 0x26, 0xC1480001)
time.sleep(0.2)
u.PostMessageW(menu_w["hwnd"], 0x0100, 0x0D, 0x001C0001)  # VK_RETURN
time.sleep(0.1)
u.PostMessageW(menu_w["hwnd"], 0x0101, 0x0D, 0xC01C0001)
time.sleep(0.8)
wins = win_cap.find_windows()
print("After clicking 首选项:", [(w["hwnd"], w["title"], w["rect"]) for w in wins])
pref_w = [w for w in wins if "首选项" in w["title"] or "Preferences" in w["title"]][0]
win_cap.capture_hwnd(pref_w["hwnd"], EV / "_probe_prefs.png", max_width=None)
p.terminate()
