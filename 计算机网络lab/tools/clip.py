#!/usr/bin/env python
"""clip.py - put text on the Windows clipboard (UTF-8 safe) and read it back.

Used to paste exact filter expressions into Wireshark. This machine has no
English keyboard layout and a Chinese IME, so SendInput-based typing corrupts
ASCII punctuation (':' became '方法:'). Clipboard paste avoids that entirely.

Usage
  python clip.py set "TEXT"
  python clip.py get
"""
import ctypes
import sys

CF_UNICODETEXT = 13
GMEM_MOVEABLE = 0x0002

user32 = ctypes.windll.user32
kernel32 = ctypes.windll.kernel32
kernel32.GlobalAlloc.restype = ctypes.c_void_p
kernel32.GlobalLock.restype = ctypes.c_void_p
kernel32.GlobalLock.argtypes = [ctypes.c_void_p]
kernel32.GlobalUnlock.argtypes = [ctypes.c_void_p]


def set_clipboard(text):
    if not user32.OpenClipboard(None):
        raise RuntimeError("OpenClipboard failed")
    try:
        user32.EmptyClipboard()
        data = text.encode("utf-16-le") + b"\x00\x00"
        h = kernel32.GlobalAlloc(GMEM_MOVEABLE, len(data))
        if not h:
            raise RuntimeError("GlobalAlloc failed")
        ptr = kernel32.GlobalLock(h)
        ctypes.memmove(ptr, data, len(data))
        kernel32.GlobalUnlock(h)
        if not user32.SetClipboardData(CF_UNICODETEXT, ctypes.c_void_p(h)):
            raise RuntimeError("SetClipboardData failed")
    finally:
        user32.CloseClipboard()


def get_clipboard():
    if not user32.OpenClipboard(None):
        raise RuntimeError("OpenClipboard failed")
    try:
        h = user32.GetClipboardData(CF_UNICODETEXT)
        if not h:
            return ""
        ptr = kernel32.GlobalLock(ctypes.c_void_p(h))
        try:
            return ctypes.wstring_at(ptr)
        finally:
            kernel32.GlobalUnlock(ctypes.c_void_p(h))
    finally:
        user32.CloseClipboard()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "get"
    if cmd == "set":
        text = sys.argv[2]
        set_clipboard(text)
        print(f"clipboard set: {get_clipboard()!r}")
    else:
        print(repr(get_clipboard()))
