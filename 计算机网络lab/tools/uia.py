#!/usr/bin/env python
"""uia.py - UI Automation (Accessibility) helper for the DSH agent.

Element-level inspection and control, so tasks use accessible names/IDs instead
of guessed pixel coordinates.

Commands
  windows                                  top-level windows (name/class/pid/hwnd)
  tree   --hwnd N [--depth D] [--max M]    element tree of one window
  find   [--hwnd N] [--name RE] [--type T] [--auto RE]
                                           locate elements by name/type/automation-id
  value  [--hwnd N] --name RE              read ValuePattern text (edits, documents)
  set    [--hwnd N] --name RE --text S     write text via ValuePattern (no keystrokes!)
  click  [--hwnd N] --name RE              click via Invoke/Select/Toggle pattern
  focus  --hwnd N                          UI Automation focus for a window
  pid    --hwnd N                          resolve hwnd -> pid

Prefer `value`/`set`/`click` over raw keystrokes: they address one specific
control and cannot leak typing into whatever window happens to be in front.
"""
import argparse
import ctypes
import re

try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    try:
        ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass

import comtypes.client  # noqa: E402

comtypes.client.GetModule("UIAutomationCore.dll")
from comtypes.gen import UIAutomationClient as UIA  # noqa: E402

TS = UIA.TreeScope
CT_NAMES = {v: k.replace("UIA_", "").replace("ControlTypeId", "")
            for k, v in vars(UIA).items() if k.endswith("ControlTypeId")}
PATTERN_IDS = {
    "invoke": UIA.UIA_InvokePatternId,
    "select": UIA.UIA_SelectionItemPatternId,
    "toggle": UIA.UIA_TogglePatternId,
    "expand": UIA.UIA_ExpandCollapsePatternId,
}


def desktop():
    return comtypes.client.CreateObject(UIA.CUIAutomation, interface=UIA.IUIAutomation)


def rect_of(el):
    try:
        r = el.CurrentBoundingRectangle
        return (int(r.left), int(r.top), int(r.right - r.left), int(r.bottom - r.top))
    except Exception:
        return None


def describe(el, depth=0):
    def safe(fn, default=None):
        try:
            return fn()
        except Exception:
            return default
    ctype = safe(lambda: el.CurrentControlType)
    return {
        "depth": depth,
        "type": CT_NAMES.get(ctype, f"type{ctype}"),
        "name": safe(lambda: el.CurrentName, "") or "",
        "auto_id": safe(lambda: el.CurrentAutomationId, "") or "",
        "class": safe(lambda: el.CurrentClassName, "") or "",
        "pid": safe(lambda: el.CurrentProcessId, 0),
        "hwnd": safe(lambda: el.CurrentNativeWindowHandle, 0),
        "rect": rect_of(el),
        "enabled": safe(lambda: el.CurrentIsEnabled),
        "offscreen": safe(lambda: el.CurrentIsOffscreen),
    }


def window_element(ui, hwnd):
    cond = ui.CreatePropertyCondition(UIA.UIA_NativeWindowHandlePropertyId, int(hwnd))
    el = ui.GetRootElement().FindFirst(TS.TreeScope_Children, cond)
    if el:
        return el
    raise SystemExit(f"no UIA window element for hwnd {hwnd} "
                     f"(try running uia.py windows to see what UIA exposes)")


def find_all(ui, hwnd, name_re=None, type_name=None, auto_re=None, deep=True):
    root = window_element(ui, hwnd) if hwnd else ui.GetRootElement()
    scope = TS.TreeScope_Descendants if deep else TS.TreeScope_Children
    els = root.FindAll(scope, ui.CreateTrueCondition())
    out = []
    for i in range(els.Length):
        try:
            el = els.GetElement(i)
        except Exception:
            continue
        d = describe(el)
        if name_re and not re.search(name_re, d["name"]):
            continue
        if type_name and d["type"].lower() != type_name.lower():
            continue
        if auto_re and not re.search(auto_re, d["auto_id"]):
            continue
        out.append((el, d))
    return out


def get_value(el):
    """Read ValuePattern text, or a clear 'no value pattern' marker (never raises)."""
    try:
        pat = el.GetCurrentPattern(UIA.UIA_ValuePatternId)
    except Exception:
        return "<no ValuePattern>"
    if not pat:
        return "<no ValuePattern>"
    try:
        return pat.QueryInterface(UIA.IUIAutomationValuePattern).CurrentValue
    except Exception:
        return "<ValuePattern unavailable>"


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("windows")

    t = sub.add_parser("tree")
    t.add_argument("--hwnd", type=int, required=True)
    t.add_argument("--depth", type=int, default=3)
    t.add_argument("--max", type=int, default=60)

    f = sub.add_parser("find")
    f.add_argument("--hwnd", type=int)
    f.add_argument("--name", dest="name_re")
    f.add_argument("--type", dest="type_name")
    f.add_argument("--auto", dest="auto_re")
    f.add_argument("--max", type=int, default=40)

    v = sub.add_parser("value")
    v.add_argument("--hwnd", type=int)
    v.add_argument("--name", dest="name_re", default=".*")
    v.add_argument("--type", dest="type_name")
    v.add_argument("--auto", dest="auto_re")
    v.add_argument("--max", type=int, default=15)
    v.add_argument("--nonempty", action="store_true",
                   help="only show elements whose value text is non-empty")

    s = sub.add_parser("set")
    s.add_argument("--hwnd", type=int)
    s.add_argument("--name", dest="name_re", required=True)
    s.add_argument("--text", required=True)

    c = sub.add_parser("click")
    c.add_argument("--hwnd", type=int)
    c.add_argument("--name", dest="name_re", required=True)

    fo = sub.add_parser("focus")
    fo.add_argument("--hwnd", type=int, required=True)

    p = sub.add_parser("pid")
    p.add_argument("--hwnd", type=int, required=True)

    args = ap.parse_args()
    ui = desktop()

    if args.cmd == "windows":
        cond = ui.CreatePropertyCondition(UIA.UIA_ControlTypePropertyId,
                                          UIA.UIA_WindowControlTypeId)
        els = ui.GetRootElement().FindAll(TS.TreeScope_Children, cond)
        for i in range(els.Length):
            d = describe(els.GetElement(i))
            print(f"hwnd={d['hwnd']:<9} pid={d['pid']:<7} class={d['class']:<26} name={d['name']!r}")
        return

    if args.cmd == "pid":
        print(window_element(ui, args.hwnd).CurrentProcessId)
        return

    if args.cmd == "tree":
        el = window_element(ui, args.hwnd)
        rows = []
        walker = ui.ControlViewWalker

        def walk(node, depth):
            if len(rows) >= args.max:
                return
            rows.append(describe(node, depth))
            if depth >= args.depth:
                return
            try:
                child = walker.GetFirstChildElement(node)
            except Exception:
                child = None
            while child is not None and len(rows) < args.max:
                walk(child, depth + 1)
                try:
                    child = walker.GetNextSiblingElement(child)
                except Exception:
                    child = None

        walk(el, 0)
        for d in rows:
            print(f"{'  ' * d['depth']}{d['type']:<20} name={d['name']!r} "
                  f"auto={d['auto_id']!r} class={d['class']!r} rect={d['rect']}")
        return

    if args.cmd == "find":
        hits = find_all(ui, args.hwnd, args.name_re, args.type_name, args.auto_re)
        for _el, d in hits[: args.max]:
            print(f"{d['type']:<20} name={d['name']!r} auto={d['auto_id']!r} "
                  f"class={d['class']!r} rect={d['rect']} pid={d['pid']}")
        print(f"# {len(hits)} match(es)")
        return

    if args.cmd == "value":
        hits = find_all(ui, args.hwnd, args.name_re, args.type_name, args.auto_re)
        shown = 0
        for el, d in hits:
            val = get_value(el)
            if args.nonempty and (val.startswith("<") or not val.strip()):
                continue
            print(f"{d['type']:<20} name={d['name']!r} auto={d['auto_id']!r} VALUE={val!r}")
            shown += 1
            if shown >= args.max:
                break
        print(f"# {len(hits)} match(es), {shown} shown")
        return

    if args.cmd == "set":
        hits = find_all(ui, args.hwnd, args.name_re)
        if not hits:
            raise SystemExit("no matching element")
        el, d = hits[0]
        pat = el.GetCurrentPattern(UIA.UIA_ValuePatternId)
        vp = pat.QueryInterface(UIA.IUIAutomationValuePattern)
        vp.SetValue(args.text)
        print(f"SET {d['type']} name={d['name']!r} -> {args.text!r}")
        print(f"VERIFY VALUE={vp.CurrentValue!r}")
        return

    if args.cmd == "click":
        hits = find_all(ui, args.hwnd, args.name_re)
        if not hits:
            raise SystemExit("no matching element")
        el, d = hits[0]
        for key, pid_ in PATTERN_IDS.items():
            try:
                pat = el.GetCurrentPattern(pid_)
            except Exception:
                continue
            if key == "invoke":
                pat.QueryInterface(UIA.IUIAutomationInvokePattern).Invoke()
            elif key == "select":
                pat.QueryInterface(UIA.IUIAutomationSelectionItemPattern).Select()
            elif key == "toggle":
                pat.QueryInterface(UIA.IUIAutomationTogglePattern).Toggle()
            else:
                pat.QueryInterface(UIA.IUIAutomationExpandCollapsePattern).Expand()
            print(f"CLICK via {key} pattern on {d['type']} name={d['name']!r} rect={d['rect']}")
            return
        raise SystemExit(f"no invokable pattern for {d['type']} {d['name']!r}")

    if args.cmd == "focus":
        window_element(ui, args.hwnd).SetFocus()
        print(f"UIA FOCUS set on hwnd {args.hwnd}")


if __name__ == "__main__":
    main()
