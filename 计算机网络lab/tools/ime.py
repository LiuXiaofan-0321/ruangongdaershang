#!/usr/bin/env python
"""ime.py - inspect and switch the Windows input language / IME.

The Chinese IME turns ASCII punctuation into full-width characters ('::' became
'方法:'), which silently corrupts Wireshark display filters typed via SendInput.
Switch to an English layout before typing code-like text.

Usage
  python ime.py list                 installed input languages + current one
  python ime.py status               current layout, IME open/closed, conversion mode
  python ime.py en                   switch to an English (en-*) layout
  python ime.py zh                   switch back to the first Chinese (zh-*) layout
"""
import ctypes
import sys
import time

user32 = ctypes.windll.user32
imm32 = ctypes.windll.imm32
kernel32 = ctypes.windll.kernel32

HKL_EN = None
HKL_ZH = None


def installed_layouts():
    """Enumerate keyboard layouts via GetKeyboardLayoutList."""
    n = user32.GetKeyboardLayoutList(0, None)
    buf = (ctypes.c_void_p * n)()
    user32.GetKeyboardLayoutList(n, buf)
    out = []
    for h in buf:
        hkl = ctypes.c_void_p(h)
        langid = user32.GetKeyboardLayoutLangId(hkl) if hasattr(
            user32, "GetKeyboardLayoutLangId") else (h & 0xFFFF)
        out.append((h, langid))
    return out


def langid_to_tag(langid):
    chars = [
        chr(langid & 0xFF),
        chr((langid >> 8) & 0xFF),
    ]
    return "".join(c for c in chars[:2] if c.isalpha())


def describe(hkl, langid):
    tag = langid_to_tag(langid)
    name = ctypes.create_unicode_buffer(256)
    kernel32.GetLocaleInfoW(langid, 0x00000002, name, 256)  # LOCALE_SLANGUAGE
    return f"hkl=0x{hkl & 0xFFFFFFFF:08X} lang=0x{langid:04X} ({tag}) {name.value}"


def current_thread_layout():
    return user32.GetKeyboardLayout(kernel32.GetCurrentThreadId())


def ime_state():
    """Report the IME conversion mode of the foreground window, if any."""
    hwnd = user32.GetForegroundWindow()
    hkl = user32.GetKeyboardLayout(user32.GetWindowThreadProcessId(hwnd, None))
    buf = ctypes.create_unicode_buffer(64)
    res = imm32.ImmGetDescriptionW(hkl, buf, 64)
    # conversion mode: 1 = native/ALPHANUMERIC, 0 = IME active
    conv = ctypes.c_uint(0)
    cm = imm32.ImmGetConversionStatus(hwnd, ctypes.byref(conv), None)
    return hkl, buf.value, cm, conv.value


def activate(hkl_hex):
    """Ask the OS to activate a layout: load it, then post it to the foreground."""
    hkl = user32.LoadKeyboardLayoutW(hkl_hex, 0x00000001)  # KLF_ACTIVATE
    if not hkl:
        return False, "LoadKeyboardLayout failed"
    hwnd = user32.GetForegroundWindow()
    WM_INPUTLANGCHANGEREQUEST = 0x0050
    user32.PostMessageW(hwnd, WM_INPUTLANGCHANGEREQUEST, 0, hkl)
    time.sleep(0.5)
    return True, f"posted layout 0x{hkl:08X} to hwnd {hwnd}"


def main():
    cmd = sys.argv[1] if len(sys.argv) > 1 else "list"

    if cmd == "list":
        print("Installed keyboard layouts:")
        en = zh = None
        for h, langid in installed_layouts():
            print("  " + describe(h, langid))
            tag = langid_to_tag(langid)
            if tag == "en" and en is None:
                en = h
            if tag == "zh" and zh is None:
                zh = h
        cur = current_thread_layout()
        print(f"\nCurrent thread layout: 0x{cur & 0xFFFFFFFF:08X}")
        if en:
            print(f"English layout hex: {en & 0xFFFFFFFF:08X}")
        if zh:
            print(f"Chinese layout hex: {zh & 0xFFFFFFFF:08X}")
        return

    if cmd == "status":
        hkl, desc, cm, conv = ime_state()
        print(f"foreground IME: hkl=0x{hkl & 0xFFFFFFFF:08X} desc={desc!r}")
        print(f"ImmGetConversionStatus returned {cm}, conversion mode = 0x{conv:X}")
        print(f"  native/alphanumeric (English input) = {bool(conv & 0x1)}")
        print(f"  full shape = {bool(conv & 0x8)}")
        print(f"  Chinese punctuation = {bool(conv & 0x400)}")
        return

    if cmd in ("en", "zh"):
        layouts = installed_layouts()
        want = "en" if cmd == "en" else "zh"
        target = None
        for h, langid in layouts:
            if langid_to_tag(langid) == want:
                target = h
                break
        if target is None:
            raise SystemExit(f"no {want}-* layout installed")
        ok, msg = activate(f"{target & 0xFFFF:08X}")
        print(f"switch to {want}: ok={ok} {msg}")
        hkl, desc, cm, conv = ime_state()
        print(f"foreground IME now: hkl=0x{hkl & 0xFFFFFFFF:08X} desc={desc!r} "
              f"conversion=0x{conv:X} native={bool(conv & 0x1)}")
        return

    raise SystemExit(__doc__)


if __name__ == "__main__":
    main()
