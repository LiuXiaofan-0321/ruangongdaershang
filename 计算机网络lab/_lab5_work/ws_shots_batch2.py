# -*- coding: utf-8 -*-
"""ws_shots_batch2.py - capture DNS, IP-proto-17, Checksum=0, mDNS, and QUIC screenshots."""
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

WS = r"C:\Program Files\Wireshark\Wireshark.exe"
CAP = r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"
EV = Path(r"C:\University Courses\计算机网络lab\_lab5_work\evidence")


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
    time.sleep(0.4)


def open_ws(args):
    p = subprocess.Popen([WS, "-r", CAP] + args)
    hwnd = None
    for _ in range(30):
        time.sleep(0.5)
        for w in win_cap.find_windows():
            if "Lab5_UDP" in w["title"]:
                hwnd = w["hwnd"]
                break
        if hwnd:
            break
    if not hwnd:
        p.terminate()
        raise RuntimeError("Wireshark window not found")
    time.sleep(2.2)
    u.ShowWindow(hwnd, 3)
    time.sleep(0.7)
    return p, hwnd


def main():
    # 1. 08_ip_protocol_17.png (Frame 10, expand IPv4 at cy=722, click Protocol: UDP (17))
    p, hwnd = open_ws(["-g", "10"])
    post_click(hwnd, 280, 722, double=True)
    # Row 9 inside IPv4: 722 + 9*34 = 1028 -> let's test 1028
    post_click(hwnd, 280, 1028, double=False)
    print("08:", win_cap.capture_hwnd(hwnd, EV / "08_ip_protocol_17.png", max_width=2000))
    p.terminate()
    time.sleep(0.8)

    # 2. 06_frame7_dns_fields.png (Frame 7 DNS query)
    p, hwnd = open_ws(["-g", "7"])
    post_click(hwnd, 280, 757, double=True)
    print("06:", win_cap.capture_hwnd(hwnd, EV / "06_frame7_dns_fields.png", max_width=2000))
    p.terminate()
    time.sleep(0.8)

    # 3. 09_checksum_zero.png (udp.checksum == 0, Frame 8, with udp.check_checksum:TRUE)
    p, hwnd = open_ws(["-Y", "udp.checksum==0", "-o", "udp.check_checksum:TRUE", "-g", "8"])
    post_click(hwnd, 280, 757, double=True)
    print("09:", win_cap.capture_hwnd(hwnd, EV / "09_checksum_zero.png", max_width=2000))
    p.terminate()
    time.sleep(0.8)

    # 4. 11_mdns_multicast.png (mdns, Frame 124 on WLAN)
    p, hwnd = open_ws(["-Y", "mdns", "-g", "124"])
    post_click(hwnd, 280, 757, double=True)
    print("11:", win_cap.capture_hwnd(hwnd, EV / "11_mdns_multicast.png", max_width=2000))
    p.terminate()
    time.sleep(0.8)

    # 5. 12_quic_large.png (quic, Frame 134, 1258 B)
    p, hwnd = open_ws(["-Y", "quic", "-g", "134"])
    post_click(hwnd, 280, 757, double=True)
    print("12:", win_cap.capture_hwnd(hwnd, EV / "12_quic_large.png", max_width=2000))
    p.terminate()
    time.sleep(0.8)


if __name__ == "__main__":
    main()
