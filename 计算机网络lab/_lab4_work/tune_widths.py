# -*- coding: utf-8 -*-
"""tune_widths.py - set the table/figure widths used by build_lab4.py."""
import re
import sys

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

P = r"C:\University Courses\计算机网络lab\_lab4_work\build_lab4.py"
s = open(P, encoding="utf-8").read()

plan = {
    "01_ipconfig.png": 14.5,
    "03_route.png": 14.5,
    "02_arp_cache.png": 14.5,
    "06_arp_overview.png": 14.0,
    "08_eth_addr_filter.png": 14.0,
    "07_ethertype_bytes.png": 14.0,
    "04_arp_request_fields.png": 14.0,
    "05_arp_reply_fields.png": 14.0,
    "09_gratuitous_arp.png": 14.0,
    "10_gateway_exchange.png": 14.0,
    "fig_arp_exchange.png": 15.0,
    "fig_arp_header.png": 13.8,
}

n = 0
for img, w in plan.items():
    pat = re.compile(r'(figure\("' + re.escape(img) + r'",.*?,\s*)([\d.]+)(\))', re.S)
    s, k = pat.subn(lambda m, w=w: m.group(1) + str(w) + m.group(3), s, count=1)
    if k:
        n += 1
    else:
        print("  no match for", img)

open(P, "w", encoding="utf-8").write(s)
print(f"updated widths for {n} figures")
