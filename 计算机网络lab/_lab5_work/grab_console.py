# -*- coding: utf-8 -*-
"""grab_console.py - capture 01_ipconfig.png and 02_workload.png in real console windows."""
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, r"C:\University Courses\计算机网络lab\_lab5_work")
import win_cap

EV = Path(r"C:\University Courses\计算机网络lab\_lab5_work\evidence")

def run_console_shot(title, cmd_lines, out_name, cols=115, lines=46, wait=4.0):
    d = Path(tempfile.mkdtemp(prefix="con-"))
    bat = d / "run.bat"
    body = [
        "@echo off",
        f"mode con: cols={cols} lines={lines}",
        f"title {title}",
    ] + cmd_lines + [
        "echo.",
        "echo ---- press any key to close ----",
        "pause >nul",
    ]
    bat.write_text("\r\n".join(body) + "\r\n", encoding="gbk", errors="replace")
    si = subprocess.STARTUPINFO()
    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    si.wShowWindow = 5  # SW_SHOW
    p = subprocess.Popen(["conhost.exe", "cmd.exe", "/k", str(bat)], creationflags=0x10, startupinfo=si)
    time.sleep(wait)
    wins = [w for w in win_cap.find_windows() if title in w["title"] or "conhost" in w["title"].lower() or "cmd.exe" in w["title"].lower()]
    if not wins:
        p.terminate()
        raise RuntimeError(f"Window {title} not found; all={win_cap.find_windows()}")
    hwnd = wins[0]["hwnd"]
    res = win_cap.capture_hwnd(hwnd, EV / out_name, max_width=2000, maximize=False)
    print(out_name, res)
    win_cap.u.PostMessageW(hwnd, 0x0010, 0, 0)  # WM_CLOSE
    p.terminate()
    time.sleep(0.5)

if __name__ == "__main__":
    run_console_shot(
        "Lab5_ipconfig",
        ["echo $ ipconfig", "ipconfig"],
        "01_ipconfig.png", cols=100, lines=48, wait=3.0
    )
    run_console_shot(
        "Lab5_workload",
        [
            "echo $ nslookup www.baidu.com",
            "nslookup www.baidu.com",
            "echo.",
            "echo $ nslookup www.ecnu.edu.cn",
            "nslookup www.ecnu.edu.cn",
            "echo.",
            "echo $ w32tm /stripchart /computer:ntp.aliyun.com /samples:2 /dataonly",
            "w32tm /stripchart /computer:ntp.aliyun.com /samples:2 /dataonly",
        ],
        "02_workload.png", cols=105, lines=40, wait=8.5
    )
