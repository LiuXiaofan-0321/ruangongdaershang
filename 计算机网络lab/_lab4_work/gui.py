# -*- coding: utf-8 -*-
"""gui.py - minimal DPI-aware mouse helpers for the Lab4 Wireshark evidence run.

cua.py offers click/key/type but no drag, and pyautogui's corner fail-safe aborts
whenever the cursor happens to rest at (0,0). This module uses Win32 directly in
physical pixels (the process is made per-monitor DPI aware first, so coordinates
match the screenshots, which are physical).

Usage:
  python gui.py drag --x1 A --y1 B --x2 C --y2 D [--hwnd N]
  python gui.py move --x A --y B
  python gui.py maximize --hwnd N
"""
import argparse
import ctypes
import sys
import time

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)      # per-monitor v2
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

u = ctypes.windll.user32
MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP = 0x0004


def move(x, y):
    u.SetCursorPos(int(x), int(y))
    time.sleep(0.05)


def drag(x1, y1, x2, y2, steps=24, settle=0.25):
    move(x1, y1)
    u.mouse_event(MOUSEEVENTF_LEFTDOWN, 0, 0, 0, 0)
    time.sleep(settle)
    for i in range(1, steps + 1):
        move(x1 + (x2 - x1) * i / steps, y1 + (y2 - y1) * i / steps)
    time.sleep(settle)
    u.mouse_event(MOUSEEVENTF_LEFTUP, 0, 0, 0, 0)
    time.sleep(settle)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("drag")
    for k in ("x1", "y1", "x2", "y2"):
        d.add_argument(f"--{k}", type=int, required=True)
    d.add_argument("--hwnd", type=int)

    m = sub.add_parser("move")
    m.add_argument("--x", type=int, required=True)
    m.add_argument("--y", type=int, required=True)

    mx = sub.add_parser("maximize")
    mx.add_argument("--hwnd", type=int, required=True)

    args = ap.parse_args()

    if args.hwnd:
        u.SetForegroundWindow(ctypes.c_void_p(args.hwnd))
        time.sleep(0.4)

    if args.cmd == "drag":
        drag(args.x1, args.y1, args.x2, args.y2)
        print(f'{{"ok": true, "drag": [{args.x1},{args.y1}->{args.x2},{args.y2}]}}')
    elif args.cmd == "move":
        move(args.x, args.y)
        print(f'{{"ok": true, "move": [{args.x},{args.y}]}}')
    else:
        u.ShowWindow(ctypes.c_void_p(args.hwnd), 3)      # SW_MAXIMIZE
        time.sleep(0.8)
        r = ctypes.wintypes.RECT() if hasattr(ctypes, "wintypes") else None
        print(f'{{"ok": true, "maximized": {args.hwnd}}}')
    return 0


if __name__ == "__main__":
    sys.exit(main())
