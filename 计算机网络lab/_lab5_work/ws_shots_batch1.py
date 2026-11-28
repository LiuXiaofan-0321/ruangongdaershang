# -*- coding: utf-8 -*-
"""ws_shots_batch1.py - capture Capture Options + Frame 10 NTP/UDP/IP screenshots."""
import subprocess
import sys
import time
from pathlib import Path

sys.path.insert(0, r"C:\University Courses\计算机网络lab\_lab5_work")
import win_cap

WS = r"C:\Program Files\Wireshark\Wireshark.exe"
CAP = r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"
EV = Path(r"C:\University Courses\计算机网络lab\_lab5_work\evidence")


def wait_window(title_sub, timeout=15.0):
    t0 = time.time()
    while time.time() - t0 < timeout:
        for w in win_cap.find_windows():
            if title_sub in w["title"]:
                return w
        time.sleep(0.4)
    return None


def shot_capture_options():
    p = subprocess.Popen([WS])
    time.sleep(9.0)
    w = wait_window("Wireshark", timeout=10.0)
    if not w:
        p.terminate()
        raise RuntimeError("Main Wireshark window not found")
    win_cap.focus_hwnd(w["hwnd"])
    rx, ry, rw, rh = w["rect"]
    # Click center of window first to ensure focus, then press Ctrl+K
    win_cap.click_abs(rx + 200, ry + 150)
    time.sleep(0.3)
    win_cap.send_keys("ctrl+k")
    dlg = wait_window("捕获选项", timeout=8.0) or wait_window("Capture Options", timeout=2.0)
    if not dlg:
        p.terminate()
        raise RuntimeError(f"Capture Options dialog not found; wins={win_cap.find_windows()}")
    time.sleep(0.8)
    win_cap.focus_hwnd(dlg["hwnd"])
    res = win_cap.capture_hwnd(dlg["hwnd"], EV / "03_capture_options.png", max_width=2000, maximize=False)
    print("03_capture_options:", res)
    p.terminate()
    time.sleep(1.0)


def shot_frame10():
    p = subprocess.Popen([WS, "-r", CAP, "-g", "10"])
    w = wait_window("Lab5_UDP", timeout=15.0)
    if not w:
        p.terminate()
        raise RuntimeError("Lab5_UDP window not found")
    time.sleep(2.5)
    win_cap.focus_hwnd(w["hwnd"])
    win_cap.u.ShowWindow(w["hwnd"], 3)
    time.sleep(0.8)
    w = wait_window("Lab5_UDP", timeout=5.0)
    rx, ry, rw, rh = w["rect"]

    # Middle pane rows in maximized 2906x1730:
    # Frame 10: ~592, Ethernet II: ~628, IPv4: ~665, UDP: ~700, NTP: ~735
    # Click UDP line directly (x=280, y=700) to highlight the 8 UDP header bytes!
    win_cap.click_abs(rx + 280, ry + 700)
    time.sleep(0.4)
    res7 = win_cap.capture_hwnd(w["hwnd"], EV / "07_udp_bytes_highlight.png", max_width=2000)
    print("07_udp_bytes_highlight:", res7)

    # Double-click UDP line to expand it, then move cursor to top-right away from list
    win_cap.click_abs(rx + 280, ry + 700, double=True)
    time.sleep(0.4)
    res5 = win_cap.capture_hwnd(w["hwnd"], EV / "05_frame10_ntp_fields.png", max_width=2000)
    print("05_frame10_ntp_fields:", res5)

    # Collapse UDP (double-click again), then double-click IPv4 (y=665) to expand IPv4!
    win_cap.click_abs(rx + 280, ry + 700, double=True)
    time.sleep(0.3)
    win_cap.click_abs(rx + 280, ry + 665, double=True)
    time.sleep(0.4)
    # Move down inside IPv4 to Protocol: UDP (17)
    for _ in range(8):
        win_cap.send_keys("down")
        time.sleep(0.08)
    res8 = win_cap.capture_hwnd(w["hwnd"], EV / "08_ip_protocol_17.png", max_width=2000)
    print("08_ip_protocol_17:", res8)

    p.terminate()
    time.sleep(1.0)


if __name__ == "__main__":
    shot_frame10()
