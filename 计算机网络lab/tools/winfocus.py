#!/usr/bin/env python
"""winfocus.py - reliably force a window to the foreground on Windows.

`SetForegroundWindow` alone is often refused by the Windows foreground lock
(another process owns the foreground). The standard workaround is:

  1. attach our input queue to the current foreground window's thread
     (AttachThreadInput), which lifts the lock while attached,
  2. send Alt/F23 to nudge the shell into giving us foreground rights,
  3. SetForegroundWindow + SetFocus, then detach.

Usage:
  python winfocus.py --hwnd N            focus and report
  python winfocus.py --hwnd N --verify   focus, then verify and exit non-zero on failure
"""
import argparse
import ctypes
import sys
import time

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32

SW_RESTORE = 9
GWL_EXSTYLE = -20
WS_EX_TOPMOST = 0x00000008
HWND_TOPMOST = -1
HWND_NOTOPMOST = -2
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_SHOWWINDOW = 0x0040


def focus(hwnd):
    if not user32.IsWindow(ctypes.c_void_p(hwnd)):
        return False, "not a window"

    if user32.IsIconic(ctypes.c_void_p(hwnd)):
        user32.ShowWindow(ctypes.c_void_p(hwnd), SW_RESTORE)
        time.sleep(0.3)

    fg = user32.GetForegroundWindow()
    fg_thread = user32.GetWindowThreadProcessId(ctypes.c_void_p(fg), None)
    my_thread = kernel32.GetCurrentThreadId()
    attached = False
    if fg_thread and fg_thread != my_thread:
        attached = bool(user32.AttachThreadInput(my_thread, fg_thread, True))
    try:
        user32.BringWindowToTop(ctypes.c_void_p(hwnd))
        user32.SetForegroundWindow(ctypes.c_void_p(hwnd))
        user32.SetFocus(ctypes.c_void_p(hwnd))
        time.sleep(0.15)
        if user32.GetForegroundWindow() != hwnd:
            # second attempt: brief TOPMOST pulse forces the switch
            user32.SetWindowPos(ctypes.c_void_p(hwnd), HWND_TOPMOST, 0, 0, 0, 0,
                                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            user32.SetWindowPos(ctypes.c_void_p(hwnd), HWND_NOTOPMOST, 0, 0, 0, 0,
                                SWP_NOMOVE | SWP_NOSIZE | SWP_SHOWWINDOW)
            user32.SetForegroundWindow(ctypes.c_void_p(hwnd))
            time.sleep(0.2)
    finally:
        if attached:
            user32.AttachThreadInput(my_thread, fg_thread, False)

    now = user32.GetForegroundWindow()
    return now == hwnd, f"foreground={now}"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hwnd", type=int, required=True)
    ap.add_argument("--verify", action="store_true")
    args = ap.parse_args()

    ok, detail = focus(args.hwnd)
    print(f"FOCUS hwnd={args.hwnd} ok={ok} {detail}")
    if args.verify and not ok:
        sys.exit(1)


if __name__ == "__main__":
    main()
