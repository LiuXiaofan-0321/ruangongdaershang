#!/usr/bin/env python
"""winshot.py - capture a single window's own content, independent of z-order.

`ImageGrab`/`CopyFromScreen` on a window rect returns whatever is currently
painting over that area. `PrintWindow(hwnd, hdc, PW_RENDERFULLCONTENT)` asks the
window to draw itself into our bitmap instead, so overlapping windows do not
matter (works for Chrome/Electron/WinUI/classic Win32).

Usage:
  python winshot.py --hwnd N --out FILE [--method full|screen]
  python winshot.py --list
"""
import argparse
import ctypes
import sys
import time

from PIL import Image

# physical-pixel coordinates, matching cua.py / screenshots
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

PW_CLIENTONLY = 0x00000001
PW_RENDERFULLCONTENT = 0x00000002
SRCCOPY = 0x00CC0020


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", ctypes.c_uint32), ("biWidth", ctypes.c_int32),
        ("biHeight", ctypes.c_int32), ("biPlanes", ctypes.c_uint16),
        ("biBitCount", ctypes.c_uint16), ("biCompression", ctypes.c_uint32),
        ("biSizeImage", ctypes.c_uint32), ("biXPelsPerMeter", ctypes.c_int32),
        ("biYPelsPerMeter", ctypes.c_int32), ("biClrUsed", ctypes.c_uint32),
        ("biClrImportant", ctypes.c_uint32),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", ctypes.c_uint32 * 3)]


def window_rect(hwnd):
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    r = RECT()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(r))
    return r


def print_window(hwnd):
    r = window_rect(hwnd)
    w, h = r.right - r.left, r.bottom - r.top
    if w <= 0 or h <= 0:
        raise RuntimeError(f"window {hwnd} has no area ({w}x{h}) - minimized?")

    hdc_window = user32.GetWindowDC(ctypes.c_void_p(hwnd))
    hdc_mem = gdi32.CreateCompatibleDC(hdc_window)
    hbmp = gdi32.CreateCompatibleBitmap(hdc_window, w, h)
    gdi32.SelectObject(hdc_mem, hbmp)

    ok = user32.PrintWindow(ctypes.c_void_p(hwnd), hdc_mem, PW_RENDERFULLCONTENT)
    if not ok:
        # older/odd windows may need the flag off
        ok = user32.PrintWindow(ctypes.c_void_p(hwnd), hdc_mem, 0)

    bmi = BITMAPINFO()
    bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
    bmi.bmiHeader.biWidth = w
    bmi.bmiHeader.biHeight = -h  # top-down
    bmi.bmiHeader.biPlanes = 1
    bmi.bmiHeader.biBitCount = 32
    bmi.bmiHeader.biCompression = 0

    buf = ctypes.create_string_buffer(w * h * 4)
    gdi32.GetDIBits(hdc_mem, hbmp, 0, h, buf, ctypes.byref(bmi), 0)

    img = Image.frombuffer("RGBA", (w, h), buf, "raw", "BGRA", 0, 1).convert("RGB")

    gdi32.DeleteObject(hbmp)
    gdi32.DeleteDC(hdc_mem)
    user32.ReleaseDC(ctypes.c_void_p(hwnd), hdc_window)
    return img, r, bool(ok)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hwnd", type=int)
    ap.add_argument("--out")
    ap.add_argument("--list", action="store_true")
    args = ap.parse_args()

    if args.list or not args.hwnd:
        import pygetwindow
        for w in pygetwindow.getAllWindows():
            if (w.title or "").strip():
                print(f"[{getattr(w, '_hWnd', None)}] {w.width}x{w.height} "
                      f"@({w.left},{w.top}) {w.title}")
        return

    img, r, ok = print_window(args.hwnd)
    out = args.out or time.strftime("win-%H%M%S.png")
    img.save(out)
    print(f"PRINTWINDOW ok={ok} {out} rect={r.left},{r.top},{r.right},{r.bottom} "
          f"size={img.size}")


if __name__ == "__main__":
    main()
