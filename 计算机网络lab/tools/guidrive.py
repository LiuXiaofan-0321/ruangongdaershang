#!/usr/bin/env python
"""guidrive.py - focus a window, then run a short, explicit click/key sequence.

Every step is printed so the run can be verified afterwards. Use it instead of
long blind click chains: one small run, then screenshot and check.

Usage:
  python guidrive.py --hwnd N [--shot out.png] --steps "click:400,596" "key:right" "sleep:0.3"
Step kinds:
  click:X,Y      move pointer and left-click
  rclick:X,Y     right-click (context menu)
  dclick:X,Y     double-click
  key:NAME       single key press (right, left, up, down, enter, esc, plus, minus, tab, ...)
  hotkey:a+b     key combination
  type:TEXT      type literal text
  sleep:SECONDS  wait
"""
import argparse
import ctypes
import sys
import time

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import pyautogui  # noqa: E402

user32 = ctypes.windll.user32
pyautogui.FAILSAFE = True
pyautogui.PAUSE = 0.05


def focus(hwnd):
    user32.ShowWindow(ctypes.c_void_p(hwnd), 3)  # SW_MAXIMIZE
    user32.SetForegroundWindow(ctypes.c_void_p(hwnd))
    time.sleep(0.6)
    return user32.GetForegroundWindow() == hwnd


def run_step(step):
    kind, _, arg = step.partition(":")
    kind = kind.strip().lower()
    if kind == "click":
        x, y = (int(v) for v in arg.split(","))
        pyautogui.moveTo(x, y, duration=0.12)
        pyautogui.click()
        print(f"  click ({x},{y})")
    elif kind == "dclick":
        x, y = (int(v) for v in arg.split(","))
        pyautogui.moveTo(x, y, duration=0.12)
        pyautogui.doubleClick()
        print(f"  double-click ({x},{y})")
    elif kind == "rclick":
        x, y = (int(v) for v in arg.split(","))
        pyautogui.moveTo(x, y, duration=0.12)
        pyautogui.click(button="right")
        print(f"  right-click ({x},{y})")
    elif kind == "key":
        pyautogui.press(arg.strip())
        print(f"  key {arg.strip()}")
    elif kind == "hotkey":
        keys = [k.strip() for k in arg.split("+")]
        pyautogui.hotkey(*keys)
        print(f"  hotkey {'+'.join(keys)}")
    elif kind == "type":
        pyautogui.typewrite(arg, interval=0.03)
        print(f"  type {arg!r}")
    elif kind == "sleep":
        time.sleep(float(arg))
        print(f"  sleep {arg}s")
    else:
        raise SystemExit(f"unknown step kind: {step!r}")
    time.sleep(0.25)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hwnd", type=int, required=True)
    ap.add_argument("--steps", nargs="+", required=True)
    args = ap.parse_args()

    ok = focus(args.hwnd)
    print(f"FOCUS hwnd={args.hwnd} is_foreground={ok}")
    if not ok:
        print("WARNING: target is not foreground; keystrokes could land elsewhere")
    for step in args.steps:
        run_step(step)
    print("DONE")


if __name__ == "__main__":
    main()
