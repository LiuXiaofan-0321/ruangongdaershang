#!/usr/bin/env python
"""cua.py - Computer-Use helper for the DSH agent on Windows.

Everything here works in PHYSICAL screen pixels, matching screenshots taken by
`imagegrab` (the panel is 2880x1800 at 200% scaling, so logical 1440x900 is NOT
the coordinate space you want).

Commands
  info                                  screen/DPI/pointer facts
  windows [--json]                      visible top-level windows (HWND, title, rect, pid)
  shot [--out FILE] [--monitor N]       full desktop (or one monitor) -> PNG
  win-shot --hwnd N --out FILE          single window -> PNG
  focus --hwnd N                        restore + bring window to front
  click X Y [--button left] [--double]  move + click
  move X Y                              move pointer only
  type "TEXT" [--interval 0.03]         type text into focused control
  keys "alt+f4" "enter"                 press hotkeys / key sequences
  scroll N                              scroll wheel (negative = down)

Notes
  * pyautogui.FAILSAFE is ON: slamming the pointer into a corner raises
    FailSafeException, which stops a runaway automation.
  * Prefer UIA element targeting (uia.py) over raw coordinates.
"""
import argparse
import ctypes
import json
import sys
import time

# --- force physical-pixel coordinates before anything touches the desktop ---
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # PROCESS_PER_MONITOR_DPI_AWARE
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import pyautogui  # noqa: E402
import pygetwindow  # noqa: E402
from PIL import ImageGrab  # noqa: E402

pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.12

user32 = ctypes.windll.user32


def _rect(hwnd):
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    r = RECT()
    user32.GetWindowRect(ctypes.c_void_p(hwnd), ctypes.byref(r))
    return r


def cmd_info(_args):
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    vs = RECT()
    user32.GetWindowRect(user32.GetDesktopWindow(), ctypes.byref(vs))
    pt = ctypes.wintypes.POINT() if hasattr(ctypes, "wintypes") else None
    print(f"pyautogui screen size : {pyautogui.size()}")
    print(f"pointer position      : {pyautogui.position()}")
    print(f"screenshot size       : {ImageGrab.grab().size}")
    print(f"desktop window rect   : {vs.left},{vs.top} -> {vs.right},{vs.bottom}")
    try:
        print(f"window count (pygetwindow): {len([t for t in pygetwindow.getAllTitles() if t.strip()])}")
    except Exception as exc:  # noqa: BLE001
        print(f"window count failed: {exc}")


def cmd_windows(args):
    rows = []
    for w in pygetwindow.getAllWindows():
        title = (w.title or "").strip()
        if not title:
            continue
        if not args.all and getattr(w, "isMinimized", False) and not args.json:
            pass
        rows.append({
            "title": title,
            "hwnd": getattr(w, "_hWnd", None),
            "left": w.left, "top": w.top, "width": w.width, "height": w.height,
            "minimized": bool(getattr(w, "isMinimized", False)),
            "active": bool(getattr(w, "isActive", False)),
            "visible": bool(getattr(w, "visible", True)),
        })
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=2))
    else:
        for r in rows:
            flag = " MIN" if r["minimized"] else (" ACTIVE" if r["active"] else "")
            print(f"[{r['hwnd']}] {r['width']}x{r['height']} @({r['left']},{r['top']}){flag}  {r['title']}")


def cmd_shot(args):
    img = pyautogui.screenshot() if not args.monitor else ImageGrab.grab(
        all_screens=False)
    out = args.out or time.strftime("shot-%H%M%S.png")
    img.save(out)
    print(f"SCREENSHOT {out} size={img.size}")


def cmd_win_shot(args):
    r = _rect(args.hwnd)
    img = pyautogui.screenshot(region=(r.left, r.top, r.right - r.left, r.bottom - r.top))
    out = args.out or time.strftime("win-%H%M%S.png")
    img.save(out)
    print(f"WINDOWSHOT {out} rect={r.left},{r.top},{r.right},{r.bottom} size={img.size}")


def cmd_focus(args):
    r = _rect(args.hwnd)
    try:
        user32.ShowWindow(ctypes.c_void_p(args.hwnd), 9)  # SW_RESTORE
    except Exception:
        pass
    try:
        user32.SetForegroundWindow(ctypes.c_void_p(args.hwnd))
    except Exception:
        pass
    time.sleep(0.4)
    fg = user32.GetForegroundWindow()
    print(f"FOCUS requested hwnd={args.hwnd} rect={r.left},{r.top},{r.right},{r.bottom} "
          f"is_foreground={fg == args.hwnd} foreground={fg}")


def cmd_click(args):
    pyautogui.moveTo(args.x, args.y, duration=0.15)
    time.sleep(0.1)
    pyautogui.click(button=args.button, clicks=2 if args.double else 1,
                    interval=0.08 if args.double else 0.0)
    print(f"CLICK {args.x},{args.y} button={args.button} double={args.double} "
          f"pointer_now={pyautogui.position()}")


def cmd_move(args):
    pyautogui.moveTo(args.x, args.y, duration=0.15)
    print(f"MOVE {args.x},{args.y} pointer_now={pyautogui.position()}")


def cmd_type(args):
    pyautogui.typewrite(args.text, interval=args.interval)
    print(f"TYPED {len(args.text)} chars: {args.text!r}")


def cmd_keys(args):
    for combo in args.combos:
        pyautogui.hotkey(*[p.strip() for p in combo.split("+")])
        time.sleep(0.25)
        print(f"KEYS {combo}")


def cmd_scroll(args):
    pyautogui.scroll(args.amount)
    print(f"SCROLL {args.amount}")


def main():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info").set_defaults(func=cmd_info)

    w = sub.add_parser("windows")
    w.add_argument("--json", action="store_true")
    w.add_argument("--all", action="store_true")
    w.set_defaults(func=cmd_windows)

    s = sub.add_parser("shot")
    s.add_argument("--out")
    s.add_argument("--monitor", type=int)
    s.set_defaults(func=cmd_shot)

    ws = sub.add_parser("win-shot")
    ws.add_argument("--hwnd", type=int, required=True)
    ws.add_argument("--out")
    ws.set_defaults(func=cmd_win_shot)

    f = sub.add_parser("focus")
    f.add_argument("--hwnd", type=int, required=True)
    f.set_defaults(func=cmd_focus)

    c = sub.add_parser("click")
    c.add_argument("x", type=int)
    c.add_argument("y", type=int)
    c.add_argument("--button", default="left")
    c.add_argument("--double", action="store_true")
    c.set_defaults(func=cmd_click)

    m = sub.add_parser("move")
    m.add_argument("x", type=int)
    m.add_argument("y", type=int)
    m.set_defaults(func=cmd_move)

    t = sub.add_parser("type")
    t.add_argument("text")
    t.add_argument("--interval", type=float, default=0.03)
    t.set_defaults(func=cmd_type)

    k = sub.add_parser("keys")
    k.add_argument("combos", nargs="+")
    k.set_defaults(func=cmd_keys)

    sc = sub.add_parser("scroll")
    sc.add_argument("amount", type=int)
    sc.set_defaults(func=cmd_scroll)

    args = p.parse_args()
    if not hasattr(ctypes, "wintypes"):
        pass
    args.func(args)


if __name__ == "__main__":
    main()
