# -*- coding: utf-8 -*-
"""analyze.py (Lab5) - derive every number the report quotes straight from Lab5_UDP.pcapng.

Reads Lab5_UDP.pcapng with tshark, then re-parses Ethernet II / IPv4 / UDP headers
from raw bytes (via tshark -x) and independently verifies RFC 768 UDP checksums
with the IPv4 pseudo-header. Writes facts.json next to this script.
"""
import json
import statistics
import subprocess
import sys
from collections import Counter
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")

ROOT = Path(r"C:\University Courses\计算机网络lab")
WORK = ROOT / "_lab5_work"
CAP = WORK / "Lab5_UDP.pcapng"
TSHARK = r"C:\Program Files\Wireshark\tshark.exe"
OUT = WORK / "facts.json"

WLAN_GUID = r"\Device\NPF_{C59C96C9-17AD-4F4E-ADD7-2E166380D039}"
TUN_GUID = r"\Device\NPF_{B738A021-9842-444C-10B0-A4E3F65AB5B6}"
HOST_WLAN_IP = "192.168.31.134"
HOST_TUN_IP = "172.18.0.1"

FIELDS = [
    "frame.number", "frame.time_relative", "frame.len",
    "frame.interface_id", "frame.interface_name",
    "eth.src", "eth.dst", "eth.type",
    "ip.version", "ip.hdr_len", "ip.len", "ip.id", "ip.ttl", "ip.proto",
    "ip.checksum", "ip.src", "ip.dst",
    "udp.srcport", "udp.dstport", "udp.length", "udp.checksum",
    "udp.checksum.status",
    "_ws.col.protocol", "_ws.col.info",
]


def tshark_fields(cap, fields, display_filter=None):
    cmd = [
        TSHARK, "-r", str(cap),
        "-o", "udp.check_checksum:TRUE",
        "-T", "fields", "-E", "header=y",
        "-E", "separator=\t", "-E", "quote=d",
    ]
    if display_filter:
        cmd += ["-Y", display_filter]
    for f in fields:
        cmd += ["-e", f]
    res = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
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
    """Return raw frame bytes for one frame number, as a lowercase hex string."""
    res = subprocess.run(
        [TSHARK, "-r", str(cap), "-Y", f"frame.number == {num}", "-x"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
    )
    hexes = []
    started = False
    for ln in res.stdout.splitlines():
        if not ln.strip():
            if started:
                break
            continue
        if len(ln) < 7 or ":" in ln[:6]:
            continue
        off_str = ln[:4].strip()
        if not (len(off_str) == 4 and all(c in "0123456789abcdefABCDEF" for c in off_str)):
            continue
        if started and off_str == "0000":
            break
        started = True
        hex_col = ln[6:54].split()
        for tok in hex_col:
            if len(tok) == 2 and all(c in "0123456789abcdefABCDEF" for c in tok):
                hexes.append(tok.lower())
    return "".join(hexes)


def ones_complement_sum(data: bytes) -> int:
    if len(data) % 2 == 1:
        data = data + b"\x00"
    total = 0
    for i in range(0, len(data), 2):
        total += (data[i] << 8) | data[i + 1]
    while total >> 16:
        total = (total & 0xFFFF) + (total >> 16)
    return total


def parse_udp_frame(raw_hex: str, has_eth: bool):
    """Parse Ethernet II (if has_eth), IPv4, and UDP headers from raw frame bytes."""
    b = bytes.fromhex(raw_hex)
    out = {"frame_len": len(b), "has_eth": has_eth}
    off = 0
    if has_eth:
        out["eth_dst"] = ":".join(f"{x:02x}" for x in b[0:6])
        out["eth_src"] = ":".join(f"{x:02x}" for x in b[6:12])
        out["eth_type"] = f"0x{int.from_bytes(b[12:14], 'big'):04x}"
        out["eth_hdr_len"] = 14
        off = 14
    else:
        out["eth_hdr_len"] = 0

    ip = b[off:]
    ver = ip[0] >> 4
    ihl = (ip[0] & 0x0F) * 4
    assert ver == 4, f"Expected IPv4, got {ver}"
    ip_total_len = int.from_bytes(ip[2:4], "big")
    ip_id = f"0x{int.from_bytes(ip[4:6], 'big'):04x}"
    ip_ttl = ip[8]
    ip_proto = ip[9]
    assert ip_proto == 17, f"Expected IP proto 17 (UDP), got {ip_proto}"
    ip_cksum = f"0x{int.from_bytes(ip[10:12], 'big'):04x}"
    ip_src_b = ip[12:16]
    ip_dst_b = ip[16:20]
    ip_src = ".".join(str(x) for x in ip_src_b)
    ip_dst = ".".join(str(x) for x in ip_dst_b)

    udp = ip[ihl:ip_total_len]
    src_port = int.from_bytes(udp[0:2], "big")
    dst_port = int.from_bytes(udp[2:4], "big")
    udp_len = int.from_bytes(udp[4:6], "big")
    udp_cksum_val = int.from_bytes(udp[6:8], "big")
    udp_payload_len = udp_len - 8
    assert len(udp) == udp_len, f"UDP slice len {len(udp)} != udp_len {udp_len}"
    assert ip_total_len == ihl + udp_len
    assert len(b) == out["eth_hdr_len"] + ip_total_len

    # Verify RFC 768 UDP checksum over IPv4 pseudo-header + UDP segment
    pseudo = ip_src_b + ip_dst_b + bytes([0, ip_proto]) + udp[4:6]
    udp_zero_ck = udp[:6] + b"\x00\x00" + udp[8:]
    computed_sum = ones_complement_sum(pseudo + udp_zero_ck)
    computed_ck = (~computed_sum) & 0xFFFF
    if computed_ck == 0:
        computed_ck = 0xFFFF
    verify_sum = ones_complement_sum(pseudo + udp) if udp_cksum_val != 0 else None

    out.update({
        "ip_version": ver,
        "ip_hdr_len": ihl,
        "ip_total_len": ip_total_len,
        "ip_id": ip_id,
        "ip_ttl": ip_ttl,
        "ip_proto": ip_proto,
        "ip_checksum": ip_cksum,
        "ip_src": ip_src,
        "ip_dst": ip_dst,
        "ip_header_hex": ip[:ihl].hex(),
        "udp_hdr_len": 8,
        "udp_src_port": src_port,
        "udp_dst_port": dst_port,
        "udp_length": udp_len,
        "udp_payload_len": udp_payload_len,
        "udp_checksum": f"0x{udp_cksum_val:04x}",
        "udp_checksum_computed": f"0x{computed_ck:04x}",
        "udp_checksum_verify_fold": f"0x{verify_sum:04x}" if verify_sum is not None else None,
        "udp_checksum_valid": (verify_sum == 0xFFFF) if verify_sum is not None else None,
        "udp_header_hex": udp[:8].hex(),
    })
    return out


def main():
    rows = tshark_fields(CAP, FIELDS)
    if not rows:
        raise SystemExit("no frames parsed")

    # Key frames to inspect and verify at raw byte level
    # 10: WLAN NTP client (Ethernet II + IPv4 + UDP + NTP)
    # 11: WLAN NTP server reply
    # 124: WLAN MDNS multicast 224.0.0.251
    # 7: TUN DNS query (www.baidu.com)
    # 8: TUN DNS response (checksum = 0x0000)
    # 134: TUN QUIC (large 1258 B UDP datagram)
    key_nums = [10, 11, 124, 7, 8, 134]
    parsed = {}
    row_by_num = {int(r["frame.number"]): r for r in rows}
    def iface_label(r):
        if r["frame.interface_id"] == "0":
            assert "C59C96C9" in r["frame.interface_name"]
            return "WLAN"
        assert "B738A021" in r["frame.interface_name"]
        return "singbox_tun"

    for num in key_nums:
        r = row_by_num[num]
        has_eth = bool(r["eth.type"])
        binfo = parse_udp_frame(frame_bytes(CAP, num), has_eth=has_eth)
        parsed[str(num)] = {
            "frame_number": num,
            "time": r["frame.time_relative"],
            "interface": iface_label(r),
            "protocol": r["_ws.col.protocol"],
            "info": r["_ws.col.info"],
            "checksum_status": r["udp.checksum.status"],
            "b": binfo,
        }

    # Aggregate statistics across all frames
    iface_counts = Counter()
    proto_counts = Counter()
    udp_lengths = []
    proto_lengths = {}
    ck_zero_by_iface_src = Counter()
    ck_nonzero_count = 0
    ip_protos = Counter()
    dst_ips = Counter()
    non_host_dst_ips = Counter()
    both_non_host = []
    host_ips = {HOST_WLAN_IP, HOST_TUN_IP}

    for r in rows:
        iface = iface_label(r)
        iface_counts[iface] += 1
        proto = r["_ws.col.protocol"]
        proto_counts[proto] += 1
        ulen = int(r["udp.length"])
        udp_lengths.append(ulen)
        proto_lengths.setdefault(proto, []).append(ulen)
        ip_protos[int(r["ip.proto"])] += 1
        dst = r["ip.dst"]
        src = r["ip.src"]
        dst_ips[dst] += 1
        if dst not in host_ips:
            non_host_dst_ips[dst] += 1
        if src not in host_ips and dst not in host_ips:
            both_non_host.append(int(r["frame.number"]))
        if r["udp.checksum"] == "0x0000":
            ck_zero_by_iface_src[f"{iface}:{src}"] += 1
        else:
            ck_nonzero_count += 1

    sorted_lens = sorted(udp_lengths)
    n = len(sorted_lens)
    bins = [
        ("<=64 B", sum(1 for x in sorted_lens if x <= 64)),
        ("65-128 B", sum(1 for x in sorted_lens if 65 <= x <= 128)),
        ("129-256 B", sum(1 for x in sorted_lens if 129 <= x <= 256)),
        ("257-512 B", sum(1 for x in sorted_lens if 257 <= x <= 512)),
        ("513-1500 B", sum(1 for x in sorted_lens if 513 <= x <= 1500)),
        (">1500 B", sum(1 for x in sorted_lens if x > 1500)),
    ]
    proto_len_stats = {}
    for p, lst in sorted(proto_lengths.items(), key=lambda kv: -len(kv[1])):
        sl = sorted(lst)
        proto_len_stats[p] = {
            "count": len(sl),
            "min": min(sl),
            "max": max(sl),
            "median": int(statistics.median(sl)),
            "mean": round(statistics.mean(sl), 1),
        }

    # Check multicast/broadcast destinations specifically
    multicast_frames = [
        int(r["frame.number"]) for r in rows if r["ip.dst"].startswith("224.") or r["ip.dst"].startswith("239.")
    ]

    facts = {
        "capture": CAP.name,
        "duration_s": round(float(rows[-1]["frame.time_relative"]), 3),
        "frame_count": len(rows),
        "host": {
            "wlan_ip": HOST_WLAN_IP,
            "wlan_mac": "14:ac:60:56:df:85",
            "wlan_gw": "192.168.31.1",
            "tun_ip": HOST_TUN_IP,
            "tun_gw_dns": "172.18.0.2",
        },
        "interfaces": dict(iface_counts),
        "protocols": dict(proto_counts),
        "ip_protocol_values": {str(k): v for k, v in ip_protos.items()},
        "checksum": {
            "zero_total": sum(ck_zero_by_iface_src.values()),
            "nonzero_total": ck_nonzero_count,
            "zero_by_iface_src": dict(ck_zero_by_iface_src),
        },
        "udp_length_stats": {
            "min": min(sorted_lens),
            "max": max(sorted_lens),
            "median": int(statistics.median(sorted_lens)),
            "mean": round(statistics.mean(sorted_lens), 1),
            "p25": sorted_lens[n // 4],
            "p75": sorted_lens[(3 * n) // 4],
            "p90": sorted_lens[int(0.9 * n)],
            "le_400_count": sum(1 for x in sorted_lens if x <= 400),
            "le_400_pct": round(100 * sum(1 for x in sorted_lens if x <= 400) / n, 1),
            "bins": bins,
            "all_lengths": sorted_lens,
            "by_protocol": proto_len_stats,
        },
        "addressing": {
            "both_non_host_frames": both_non_host,
            "both_non_host_count": len(both_non_host),
            "multicast_dst_ip": "224.0.0.251",
            "multicast_frames": multicast_frames,
            "multicast_count": len(multicast_frames),
            "non_host_dst_ips": dict(non_host_dst_ips),
        },
        "key_frames": parsed,
    }

    OUT.write_text(json.dumps(facts, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"capture: {facts['capture']}  frames={facts['frame_count']}  duration={facts['duration_s']}s")
    print("interfaces:", facts["interfaces"])
    print("protocols :", facts["protocols"])
    print("ip_protos :", facts["ip_protocol_values"])
    print("checksums :", facts["checksum"])
    print("len stats :", {k: v for k, v in facts["udp_length_stats"].items() if k != "by_protocol"})
    print("by_proto  :", facts["udp_length_stats"]["by_protocol"])
    print("addressing:", facts["addressing"])
    for k, v in parsed.items():
        b = v["b"]
        print(f"  frame {k:>3s} [{v['interface']:11s}] {v['protocol']:4s} "
              f"frame={b['frame_len']}B eth={b['eth_hdr_len']}B ip={b['ip_hdr_len']}B/{b['ip_total_len']}B "
              f"udp={b['udp_length']}B(payload={b['udp_payload_len']}B) "
              f"ports={b['udp_src_port']}->{b['udp_dst_port']} ck={b['udp_checksum']} "
              f"computed={b['udp_checksum_computed']} valid={b['udp_checksum_valid']}")


if __name__ == "__main__":
    main()
