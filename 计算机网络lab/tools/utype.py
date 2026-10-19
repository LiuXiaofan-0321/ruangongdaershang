#!/usr/bin/env python
"""utype.py - type text into the focused window via SendInput + KEYEVENTF_UNICODE.

Why this exists: this machine has only a Chinese keyboard layout and a Chinese
IME. pyautogui.typewrite maps characters to virtual keys, so ASCII punctuation
came out corrupted (':' produced '方法:'). KEYEVENTF_UNICODE injects the literal
UTF-16 code unit, bypassing the keyboard layout and the IME.

Usage
  python utype.py "exact text to type"
  python utype.py --file path.txt      type the file contents
"""
import ctypes
import sys
import time

user32 = ctypes.windll.user32

INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
ULONG_PTR = ctypes.c_uint64 if ctypes.sizeof(ctypes.c_void_p) == 8 else ctypes.c_uint32


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.c_ushort),
        ("wScan", ctypes.c_ushort),
        ("dwFlags", ctypes.c_uint32),
        ("time", ctypes.c_uint32),
        ("dwExtraInfo", ULONG_PTR),
    ]


class _INPUTunion(ctypes.Union):
    _fields_ = [("ki", KEYBDINPUT), ("padding", ctypes.c_ubyte * 24)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", ctypes.c_uint32), ("u", _INPUTunion)]


def press_unicode(ch):
    code = ord(ch)
    for flags in (KEYEVENTF_UNICODE, KEYEVENTF_UNICODE | KEYEVENTF_KEYUP):
        inp = INPUT(type=INPUT_KEYBOARD)
        inp.u.ki = KEYBDINPUT(0, code, flags, 0, 0)
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))


def type_text(text, delay=0.012):
    for ch in text:
        press_unicode(ch)
        time.sleep(delay)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise SystemExit(__doc__)
    if sys.argv[1] == "--file":
        with open(sys.argv[2], "r", encoding="utf-8") as fh:
            payload = fh.read()
    else:
        payload = sys.argv[1]
    type_text(payload)
    print(f"typed {len(payload)} chars via SendInput(KEYEVENTF_UNICODE): {payload!r}")
