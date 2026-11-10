# -*- coding: utf-8 -*-
"""analyze.py (Lab4) - derive every number the report quotes straight from the pcapng.

Reads Lab4_ARP.pcapng with tshark, then recomputes the ARP/Ethernet layout of the
request and the reply from raw bytes so the report's claims (opcode, sizes,
EtherType, unknown-target value, broadcast/unicast destinations) are verified
rather than copied from the GUI.

Writes facts.json next to this script and prints a summary.
"""
import json
import subprocess
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab4_work"
CAP = ROOT / "Lab4_ARP.pcapng"
TSHARK = r"C:\Program Files\Wireshark\tshark.exe"
OUT = WORK / "facts.json"

FIELDS = [
    "frame.number", "frame.time_relative", "frame.len",
    "eth.src", "eth.dst", "eth.type",
    "arp.opcode", "arp.hw.type", "arp.proto.type", "arp.hw.size", "arp.proto.size",
    "arp.src.hw_mac", "arp.src.proto_ipv4",
    "arp.dst.hw_mac", "arp.dst.proto_ipv4",
    "arp.isprobe", "arp.isannouncement", "arp.isgratuitous",
    "_ws.col.info",
]


def tshark_fields(cap, fields, display_filter=None, occurrence=None):
    cmd = [TSHARK, "-r", str(cap), "-T", "fields", "-E", "header=y",
           "-E", "separator=\t", "-E", "quote=d"]
    if display_filter:
        cmd += ["-Y", display_filter]
    if occurrence:
        cmd += ["-E", f"occurrence={occurrence}"]
    for f in fields:
        cmd += ["-e", f]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    if res.returncode != 0:
        raise SystemExit(f"tshark failed: {res.stderr[:400]}")
    lines = [ln for ln in res.stdout.splitlines() if ln.strip()]
    if not lines:
        return []
    head = [h.strip('"') for h in lines[0].split("\t")]
    rows = []
    for ln in lines[1:]:
        vals = [v.strip('"') for v in ln.split("\t")]
        rows.append(dict(zip(head, vals)))
    return rows


def frame_bytes(cap, num):
    """Return the raw frame bytes for one frame number, as a hex string."""
    res = subprocess.run([TSHARK, "-r", str(cap), "-Y", f"frame.number == {num}",
                          "-x"], capture_output=True, text=True, encoding="utf-8",
                         errors="replace")
    hexes = []
    for ln in res.stdout.splitlines():
        parts = ln.split()
        if not parts:
            continue
        # data lines look like: 0000  14 ac 60 ...   ascii
        if len(parts) < 2 or ":" in parts[0]:
            continue
        for tok in parts[1:]:
            if len(tok) == 2 and all(c in "0123456789abcdefABCDEF" for c in tok):
                hexes.append(tok.lower())
            else:
                break
    return "".join(hexes)


def parse_arp(raw):
    """Split a raw Ethernet frame carrying ARP into its fields."""
    b = bytes.fromhex(raw)
    out = {
        "frame_len": len(b),
        "eth_dst": ":".join(f"{x:02x}" for x in b[0:6]),
        "eth_src": ":".join(f"{x:02x}" for x in b[6:12]),
        "eth_type": f"0x{int.from_bytes(b[12:14], 'big'):04x}",
    }
    a = b[14:]                                  # ARP message starts here
    out["arp_len"] = len(a)
    out["hw_type"] = f"0x{int.from_bytes(a[0:2], 'big'):04x}"
    out["proto_type"] = f"0x{int.from_bytes(a[2:4], 'big'):04x}"
    out["hw_size"] = a[4]
    out["proto_size"] = a[5]
    out["opcode"] = int.from_bytes(a[6:8], "big")
    out["sha"] = ":".join(f"{x:02x}" for x in a[8:14])
    out["spa"] = ".".join(str(x) for x in a[14:18])
    out["tha"] = ":".join(f"{x:02x}" for x in a[18:24])
    out["tpa"] = ".".join(str(x) for x in a[24:28])
    out["header_bytes"] = a[:28].hex()
    # everything after the 28-byte ARP message is Ethernet padding / trailer
    out["payload_after_arp"] = len(a) - 28
    return out


def main():
    rows = tshark_fields(CAP, FIELDS)
    if not rows:
        raise SystemExit("no frames parsed")

    # the request for the gateway and the gateway's reply
    req = next(r for r in rows
               if r["arp.opcode"] == "1" and r["arp.dst.proto_ipv4"] == "172.31.0.1"
               and r["arp.src.proto_ipv4"] != "0.0.0.0")
    rep = next(r for r in rows if r["arp.opcode"] == "2")

    req_bytes = parse_arp(frame_bytes(CAP, req["frame.number"]))
    rep_bytes = parse_arp(frame_bytes(CAP, rep["frame.number"]))

    probes = [r for r in rows if "ARP Probe" in r["_ws.col.info"]]
    announces = [r for r in rows if "ARP Announcement" in r["_ws.col.info"]]
    # gratuitous per RFC 5227: sender and target IP are the same address
    gratuitous = [r for r in rows
                  if r["arp.src.proto_ipv4"] == r["arp.dst.proto_ipv4"]]
    # probes use 0.0.0.0 as the sender address (a sender that does not yet own it)
    zeroconf = [r for r in rows if r["arp.src.proto_ipv4"] == "0.0.0.0"]

    facts = {
        "capture": CAP.name,
        "frame_count": len(rows),
        "request_frame": req["frame.number"],
        "reply_frame": rep["frame.number"],
        "request": {
            "b": req_bytes,
            "eth_dst": req["eth.dst"], "eth_src": req["eth.src"],
            "info": req["_ws.col.info"], "time": req["frame.time_relative"],
            "frame_len": int(req["frame.len"]),
        },
        "reply": {
            "b": rep_bytes,
            "eth_dst": rep["eth.dst"], "eth_src": rep["eth.src"],
            "info": rep["_ws.col.info"], "time": rep["frame.time_relative"],
            "frame_len": int(rep["frame.len"]),
        },
        "opcodes": {"request": 1, "reply": 2},
        "counts": {
            "requests": sum(1 for r in rows if r["arp.opcode"] == "1"),
            "replies": sum(1 for r in rows if r["arp.opcode"] == "2"),
            "probes": len(probes),
            "announcements": len(announces),
            "gratuitous": len(gratuitous),
            "zero_sender": len(zeroconf),
        },
        "probe_frames": [int(r["frame.number"]) for r in probes],
        "announce_frames": [int(r["frame.number"]) for r in announces],
        "gratuitous_frames": [int(r["frame.number"]) for r in gratuitous],
        "zero_sender_frames": [int(r["frame.number"]) for r in zeroconf],
        "unicast_requests": [
            {"frame": int(r["frame.number"]), "eth_dst": r["eth.dst"],
             "info": r["_ws.col.info"]}
            for r in rows
            if r["arp.opcode"] == "1" and r["eth.dst"] != "ff:ff:ff:ff:ff:ff"
        ],
        "frame_lengths": {
            "request": int(req["frame.len"]),
            "reply": int(rep["frame.len"]),
        },
        "arp_message_len": req_bytes["arp_len"] - req_bytes["payload_after_arp"],
        "padding_on_reply": rep_bytes["payload_after_arp"],
    }

    OUT.write_text(json.dumps(facts, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"capture            : {facts['capture']}  ({facts['frame_count']} frames)")
    print(f"request / reply    : frame {facts['request_frame']} / {facts['reply_frame']}")
    print(f"  request  eth.type={req_bytes['eth_type']} opcode={req_bytes['opcode']} "
          f"hw={req_bytes['hw_size']} proto={req_bytes['proto_size']} "
          f"arp_len={facts['arp_message_len']}B frame={facts['frame_lengths']['request']}B")
    print(f"  reply    eth.type={rep_bytes['eth_type']} opcode={rep_bytes['opcode']} "
          f"arp_len={facts['arp_message_len']}B frame={facts['frame_lengths']['reply']}B "
          f"padding={facts['padding_on_reply']}B")
    print(f"  unknown target MAC in request : {req_bytes['tha']}")
    print(f"  request 以太网目的            : {req_bytes['eth_dst']}")
    print(f"  reply   以太网目的            : {rep_bytes['eth_dst']}")
    print(f"counts             : {facts['counts']}")
    print(f"unicast requests   : {facts['unicast_requests']}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
