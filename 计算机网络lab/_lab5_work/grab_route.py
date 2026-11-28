# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\University Courses\计算机网络lab\_lab5_work")
import grab_console

grab_console.run_console_shot(
    "Lab5_route_udp",
    [
        "echo $ route print 0.0.0.0",
        "route print 0.0.0.0",
        "echo $ netstat -ano -p UDP ^| findstr /R \"192.168.31.134 172.18.0.1\"",
        'netstat -ano -p UDP | findstr /R "192.168.31.134 172.18.0.1"',
    ],
    "01b_route_udp.png", cols=108, lines=42, wait=4.0
)
