# -*- coding: utf-8 -*-
"""font_coverage.py - test which installed fonts actually contain every character
used in a DOCX, using the Windows GDI (GetGlyphIndicesW). No extra packages.

A font that lacks a character makes LibreOffice substitute a *different* typeface
for just those glyphs, which is what produces uneven stroke weights in the PDF.

Usage:  python font_coverage.py <document.docx>
"""
import ctypes
import sys
from ctypes import wintypes

from docx import Document

gdi32 = ctypes.windll.gdi32
user32 = ctypes.windll.user32

GGI_MARK_NONEXISTING_GLYPHS = 0x0001
DEFAULT_CHARSET = 1
OUT_TT_PRECIS = 4
CLIP_DEFAULT_PRECIS = 0
ANTIALIASED_QUALITY = 4
FF_DONTCARE = 0
DEFAULT_PITCH = 0

gdi32.CreateFontW.restype = wintypes.HGDIOBJ
gdi32.CreateFontW.argtypes = [ctypes.c_int] * 5 + [wintypes.DWORD, wintypes.DWORD,
                                                   wintypes.DWORD, wintypes.DWORD,
                                                   wintypes.DWORD, wintypes.DWORD,
                                                   wintypes.DWORD, wintypes.DWORD,
                                                   wintypes.LPCWSTR]
gdi32.SelectObject.restype = wintypes.HGDIOBJ
gdi32.SelectObject.argtypes = [wintypes.HDC, wintypes.HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL
gdi32.DeleteObject.argtypes = [wintypes.HGDIOBJ]
gdi32.GetGlyphIndicesW.argtypes = [wintypes.HDC, wintypes.LPCWSTR, ctypes.c_int,
                                   ctypes.POINTER(wintypes.WORD), wintypes.DWORD]
user32.GetDC.restype = wintypes.HDC
user32.GetDC.argtypes = [wintypes.HWND]
user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]


def chars_in_doc(path):
    d = Document(path)
    chars = set()
    for p in d.paragraphs:
        chars |= set(p.text)
    for t in d.tables:
        for row in t.rows:
            for c in row.cells:
                chars |= set(c.text)
    for s in d.sections:
        for p in list(s.header.paragraphs) + list(s.footer.paragraphs):
            chars |= set(p.text)
    return {c for c in chars if ord(c) > 0x2000}   # CJK + fullwidth punctuation


def coverage(font_name, chars):
    hdc = user32.GetDC(None)
    hfont = gdi32.CreateFontW(
        -20, 0, 0, 0, 400, 0, 0, 0, DEFAULT_CHARSET, OUT_TT_PRECIS,
        CLIP_DEFAULT_PRECIS, ANTIALIASED_QUALITY,
        DEFAULT_PITCH | FF_DONTCARE, font_name)
    old = gdi32.SelectObject(hdc, hfont)
    missing = []
    try:
        for ch in sorted(chars):
            glyphs = (wintypes.WORD * 1)()
            n = gdi32.GetGlyphIndicesW(hdc, ch, 1, glyphs,
                                       GGI_MARK_NONEXISTING_GLYPHS)
            if n == 0 or glyphs[0] == 0xFFFF:
                missing.append(ch)
    finally:
        gdi32.SelectObject(hdc, old)
        gdi32.DeleteObject(hfont)
        user32.ReleaseDC(None, hdc)
    return missing


def main():
    doc = sys.argv[1]
    chars = chars_in_doc(doc)
    print(f"document: {doc}")
    print(f"distinct non-ASCII chars to render: {len(chars)}")
    print()
    fonts = [
        "DengXian", "Microsoft YaHei", "SimSun", "SimHei",
        "KaiTi", "FangSong", "NSimSun", "Microsoft JhengHei UI",
    ]
    rows = []
    for f in fonts:
        miss = coverage(f, chars)
        rows.append((f, miss))
        print(f"{f:22s} missing {len(miss):3d}/{len(chars)}  {''.join(miss[:50])}")
    print()
    perfect = [f for f, m in rows if not m]
    print("fonts with FULL coverage:", ", ".join(perfect) if perfect else "none")


if __name__ == "__main__":
    main()
