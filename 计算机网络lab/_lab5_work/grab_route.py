# -*- coding: utf-8 -*-
import sys
sys.path.insert(0, r"C:\University Courses\计算机网络lab\_lab5_work")
import grab_console

grab_console.run_console_shot(
    "Lab5_route_udp",
    [
        "echo $ route print 0.0.0.0",
        "route print 0.0.0.0",
        "echo $ netstat -ano -p UDP",
        'netstat -ano -p UDP | findstr /R ":5353 :1900 :123 :53 "',
    ],
    "01b_route_udp.png", cols=108, lines=42, wait=4.0
)
