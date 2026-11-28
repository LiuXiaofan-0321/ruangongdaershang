# -*- coding: utf-8 -*-
import ctypes
import subprocess
import time
from ctypes import wintypes
from pathlib import Path
from PIL import Image

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

u = ctypes.windll.user32
g = ctypes.windll.gdi32

class RECT(ctypes.Structure):
    _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                ("right", ctypes.c_long), ("bottom", ctypes.c_long)]

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD), ("biWidth", ctypes.c_long), ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD), ("biBitCount", wintypes.WORD), ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD), ("biXPelsPerMeter", ctypes.c_long), ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD), ("biClrImportant", wintypes.DWORD),
    ]

def capture_hwnd(hwnd, out_path):
    u.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
    time.sleep(0.5)
    r = RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        return None
    hdc_win = u.GetWindowDC(hwnd)
    hdc_mem = g.CreateCompatibleDC(hdc_win)
    hbmp = g.CreateCompatibleBitmap(hdc_win, w, h)
    old = g.SelectObject(hdc_mem, hbmp)
    ok = u.PrintWindow(hwnd, hdc_mem, 2)  # PW_RENDERFULLCONTENT = 2
    if not ok:
        ok = u.PrintWindow(hwnd, hdc_mem, 0)
    bmi = BITMAPINFOHEADER()
    bmi.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.biWidth = w
    bmi.biHeight = -h
    bmi.biPlanes = 1
    bmi.biBitCount = 32
    bmi.biCompression = 0
    buf = ctypes.create_string_buffer(w * h * 4)
    g.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bmi), 0)
    g.SelectObject(hdc_mem, old)
    g.DeleteObject(hbmp)
    g.DeleteDC(hdc_mem)
    u.ReleaseDC(hwnd, hdc_win)
    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")
    img.save(out_path)
    return (w, h, ok)

def find_windows():
    wins = []
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(h, _):
        if u.IsWindowVisible(h):
            buf = ctypes.create_unicode_buffer(256)
            u.GetWindowTextW(h, buf, 256)
            if buf.value:
                wins.append((h, buf.value))
        return True
    u.EnumWindows(EnumProc(cb), 0)
    return wins

if __name__ == "__main__":
    p = subprocess.Popen([
        r"C:\Program Files\Wireshark\Wireshark.exe",
        "-r", r"C:\University Courses\计算机网络lab\_lab5_work\Lab5_UDP.pcapng"
    ])
    time.sleep(5)
    wins = find_windows()
    print("Wins:", wins)
    for h, title in wins:
        if "Wireshark" in title or "Lab5_UDP" in title:
            res = capture_hwnd(h, r"C:\University Courses\计算机网络lab\_lab5_work\test_ws.png")
            print("Captured WS:", res)
            break
    p.terminate()
