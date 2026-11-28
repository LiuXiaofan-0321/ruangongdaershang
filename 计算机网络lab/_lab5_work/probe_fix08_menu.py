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
WM_SYSKEYDOWN = 0x0104
WM_SYSKEYUP = 0x0105
WM_KEYDOWN = 0x0100
WM_KEYUP = 0x0101
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

# 1. Fix 08_ip_protocol_17.png
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

post_click(hwnd, 280, 722, double=True)
# Test Protocol: UDP (17) -> 1 row below 1028
post_click(hwnd, 280, 1058, double=False)
print("08_fixed:", win_cap.capture_hwnd(hwnd, EV / "08_ip_protocol_17.png", max_width=2000))

# 2. Test opening Capture Options via gear icon cy=67 (y_img=125 - 58 = 67) or menu cy=17
for label, cx, cy in [("gear_67", 165, 67), ("gear_75", 165, 75), ("menu_cap", 499, 17)]:
    post_click(hwnd, cx, cy, double=False)
    wins = win_cap.find_windows()
    print(f"After {label} ({cx},{cy}):", [w["title"] for w in wins])
    if len(wins) > 1:
        break

# 3. Also test WM_SYSKEYDOWN Alt+C ('C'=0x43) and Alt+E ('E'=0x45)
u.PostMessageW(hwnd, WM_SYSKEYDOWN, 0x43, 0x20000001)
time.sleep(0.2)
u.PostMessageW(hwnd, WM_SYSKEYUP, 0x43, 0xE0000001)
time.sleep(0.4)
print("After Alt+C:", [w["title"] for w in win_cap.find_windows()])

p.terminate()
