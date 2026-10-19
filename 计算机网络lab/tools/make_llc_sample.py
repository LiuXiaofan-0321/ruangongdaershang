#!/usr/bin/env python
"""make_llc_sample.py - build a valid DIX/IEEE-802.3+LLC pcap for the Lab2
"Explore on your own (IEEE 802.3)" question.

Our own captures contain no LLC frames (verified: 0 matches for `llc` in all
traces), so the lab's exploration task cannot be answered from live traffic.
This script writes a minimal class-1 pcap containing:

  frame 1: IEEE 802.3 + LLC (DSAP=SSAP=0x42, Control=0x03 UI) + payload + padding
  frame 2: Ethernet II + IPv4  (same 2-byte field carrying 0x0800 as an EtherType)

so Wireshark's own dissector can show the Length-vs-Type distinction and the
LLC demultiplexing key. The file is clearly labelled as a constructed sample.
"""
import struct
from pathlib import Path

OUT = Path(r"C:\University Courses\计算机网络lab\_lab2_工作\captures\Lab2_LLC_构造样例.pcapng")

# --- frame 1: IEEE 802.3 + LLC -------------------------------------------------
srcdst = bytes.fromhex("aabbccddeeff112233445566")   # dst, src (12 B)
payload = b"LLC-DEMO"                                 # 8 B of payload
llc = bytes([0x42, 0x42, 0x03])                       # DSAP, SSAP, Control(UI)
length = len(llc) + len(payload)                      # 802.3 Length field value = 11
body = llc + payload
# NOTE: deliberately NOT padded to 46 B. Padding here would add 0x00 bytes that
# Wireshark parses as a SNAP header (NLPID 0x00 -> STP), which confuses the demo.
f1 = srcdst + struct.pack(">H", length) + body

# --- frame 2: Ethernet II + a minimal IPv4 header ------------------------------
ip = bytes([0x45, 0x00, 0x00, 0x28, 0x00, 0x01, 0x00, 0x00,
            0x40, 0x11, 0x00, 0x00, 192, 168, 1, 10,
            192, 168, 1, 20])
f2 = bytes.fromhex("aabbccddeeff112233445566") + struct.pack(">H", 0x0800) + ip

PCAP_MAGIC = 0xA1B2C3D4
GLOBAL_HDR = struct.pack("<IHHiIII", PCAP_MAGIC, 2, 4, 0, 0, 65535, 1)  # LINKTYPE_ETHERNET


def rec(data, ts):
    return struct.pack("<IIII", ts, 0, len(data), len(data)) + data


with open(OUT, "wb") as fh:
    fh.write(GLOBAL_HDR)
    fh.write(rec(f1, 0))
    fh.write(rec(f2, 1))
    fh.write(rec(f1, 2))
    fh.write(rec(f2, 3))

print(f"wrote {OUT}  ({OUT.stat().st_size} bytes)")
print(f"frame 1 (802.3+LLC): {len(f1)} B on wire, Length field = {length} (0x{length:04X}), "
      f"LLC DSAP=SSAP=0x42 Control=0x03")
print(f"frame 2 (Ethernet II): Type field = 0x0800")
