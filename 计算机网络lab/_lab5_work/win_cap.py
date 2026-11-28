# -*- coding: utf-8 -*-
"""win_cap.py - PrintWindow + DPI-aware Win32 input helpers for exebox desktop."""
import ctypes
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
k = ctypes.windll.kernel32

ULONG_PTR = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_uint32

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

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_uint32), ("time", ctypes.c_uint32),
                ("dwExtraInfo", ULONG_PTR)]

class _INPUTunion(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("padding", ctypes.c_ubyte * 24)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_uint32), ("u", _INPUTunion)]

def find_windows():
    wins = []
    EnumProc = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)
    def cb(hwnd, _):
        if not u.IsWindowVisible(hwnd):
            return True
        buf = ctypes.create_unicode_buffer(256)
        u.GetWindowTextW(hwnd, buf, 256)
        if buf.value:
            pid = wintypes.DWORD()
            u.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
            r = RECT()
            u.GetWindowRect(hwnd, ctypes.byref(r))
            wins.append({
                "hwnd": int(hwnd),
                "title": buf.value,
                "pid": int(pid.value),
                "rect": (r.left, r.top, r.right - r.left, r.bottom - r.top),
            })
        return True
    u.EnumWindows(EnumProc(cb), 0)
    return wins

def focus_hwnd(hwnd):
    if u.IsIconic(hwnd):
        u.ShowWindow(hwnd, 9)
        time.sleep(0.25)
    fg = u.GetForegroundWindow()
    fg_t = u.GetWindowThreadProcessId(fg, None)
    my_t = k.GetCurrentThreadId()
    attached = False
    if fg_t and fg_t != my_t:
        attached = bool(u.AttachThreadInput(my_t, fg_t, True))
    try:
        u.BringWindowToTop(hwnd)
        u.SetForegroundWindow(hwnd)
        u.SetFocus(hwnd)
        time.sleep(0.15)
        if u.GetForegroundWindow() != hwnd:
            u.SetWindowPos(hwnd, -1, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0040)
            u.SetWindowPos(hwnd, -2, 0, 0, 0, 0, 0x0002 | 0x0001 | 0x0040)
            u.SetForegroundWindow(hwnd)
            time.sleep(0.2)
    finally:
        if attached:
            u.AttachThreadInput(my_t, fg_t, False)
    return u.GetForegroundWindow() == hwnd

def capture_hwnd(hwnd, out_path, max_width=2000, maximize=False):
    if maximize:
        u.ShowWindow(hwnd, 3)
        time.sleep(0.5)
    r = RECT()
    u.GetWindowRect(hwnd, ctypes.byref(r))
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        raise RuntimeError(f"Invalid rect for hwnd {hwnd}: {(w, h)}")
    hdc_win = u.GetWindowDC(hwnd)
    hdc_mem = g.CreateCompatibleDC(hdc_win)
    hbmp = g.CreateCompatibleBitmap(hdc_win, w, h)
    old = g.SelectObject(hdc_mem, hbmp)
    ok = u.PrintWindow(hwnd, hdc_mem, 2)
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
    if max_width and img.width > max_width:
        ratio = max_width / img.width
        img = img.resize((max_width, int(img.height * ratio)), Image.Resampling.LANCZOS)
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)
    return {"path": str(out_path), "orig": (w, h), "saved": img.size, "ok": bool(ok)}

def click_abs(x, y, double=False):
    u.SetCursorPos(int(x), int(y))
    time.sleep(0.06)
    for _ in range(2 if double else 1):
        u.mouse_event(0x0002, 0, 0, 0, 0)
        time.sleep(0.04)
        u.mouse_event(0x0004, 0, 0, 0, 0)
        time.sleep(0.06)

VK = {
    "enter": 0x0D, "esc": 0x1B, "tab": 0x09, "space": 0x20, "backspace": 0x08,
    "delete": 0x2E, "home": 0x24, "end": 0x23, "left": 0x25, "up": 0x26,
    "right": 0x27, "down": 0x28, "pageup": 0x21, "pagedown": 0x22,
    "ctrl": 0x11, "alt": 0x12, "shift": 0x10,
}
EXTENDED = {"delete", "home", "end", "left", "up", "right", "down", "pageup", "pagedown"}

def send_keys(combo):
    parts = [p.strip().lower() for p in combo.split("+")]
    pairs = [(p, VK.get(p, ord(p.upper()) if len(p) == 1 else None)) for p in parts]
    for name, vk in pairs:
        fl = 0x0001 if name in EXTENDED else 0
        sc = u.MapVirtualKeyW(vk, 0)
        inp = INPUT(type=1)
        inp.u.ki = KEYBDINPUT(vk, sc, fl, 0, 0)
        u.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    time.sleep(0.05)
    for name, vk in reversed(pairs):
        fl = 0x0002 | (0x0001 if name in EXTENDED else 0)
        sc = u.MapVirtualKeyW(vk, 0)
        inp = INPUT(type=1)
        inp.u.ki = KEYBDINPUT(vk, sc, fl, 0, 0)
        u.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
    time.sleep(0.08)

def clipboard_paste(text):
    CF_UNICODETEXT = 13
    GMEM_MOVEABLE = 0x0002
    k.GlobalAlloc.restype = ctypes.c_void_p
    k.GlobalLock.restype = ctypes.c_void_p
    k.GlobalLock.argtypes = [ctypes.c_void_p]
    k.GlobalUnlock.argtypes = [ctypes.c_void_p]
    u.SetClipboardData.restype = wintypes.HANDLE
    u.SetClipboardData.argtypes = [ctypes.c_uint, wintypes.HANDLE]
    if not u.OpenClipboard(None):
        raise RuntimeError("OpenClipboard failed")
    try:
        u.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\x00\x00"
        h = k.GlobalAlloc(GMEM_MOVEABLE, len(data))
        ptr = k.GlobalLock(h)
        ctypes.memmove(ptr, data, len(data))
        k.GlobalUnlock(h)
        u.SetClipboardData(CF_UNICODETEXT, h)
    finally:
        u.CloseClipboard()
    send_keys("ctrl+v")
