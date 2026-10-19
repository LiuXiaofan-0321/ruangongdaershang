"""set_wireshark_prefs.py - add Lab2-friendly Wireshark preferences safely.

Uses Wireshark's own preference keys:
  gui.name_resolve            -> MAC, enables MAC name resolution (lab requirement)
  gui.filter_buttons          -> clickable one-click display filter buttons,
                                 which avoids typing filters through a Chinese IME

Removes any previous managed block first (idempotent); writes UTF-8 with a backup.
"""
import os
import shutil
import time

pref = os.path.join(os.environ["APPDATA"], "Wireshark", "preferences")
BEGIN = "##### DSH Lab2 additions (removable) #####"
END = "##### end DSH Lab2 #####"

# ASCII-only labels: this console/machine has no English keyboard layout and a
# Chinese IME, so labels must not depend on typing or on console encoding.
BUTTONS = [
    ("ETH-BROADCAST", "eth.dst == ff:ff:ff:ff:ff:ff"),
    ("ETH-MULTICAST-NONBC", "eth.dst.ig == 1 && eth.dst != ff:ff:ff:ff:ff:ff"),
    ("ETH-MULTICAST-ALL", "eth.dst.ig == 1"),
    ("LLC-802.3", "llc"),
    ("ICMP", "icmp"),
    ("ARP", "arp"),
]

block = [BEGIN, "gui.name_resolve: MAC"]
for label, expr in BUTTONS:
    block.append(f'gui.filter_buttons: "{label}" {expr}')
block.append(END)

with open(pref, "r", encoding="utf-8", errors="surrogateescape") as fh:
    text = fh.read()
shutil.copy2(pref, pref + ".bak-dsh3-" + time.strftime("%H%M%S"))

# strip any previous managed block or stray managed keys
lines = text.splitlines()
out, skip = [], False
for line in lines:
    if line.strip() == BEGIN:
        skip = True
        continue
    if line.strip() == END:
        skip = False
        continue
    if skip:
        continue
    if line.startswith("gui.filter_buttons:") or line.startswith("#gui.filter_buttons:"):
        continue
    if line.startswith("gui.name_resolve:") or line.startswith("#gui.name_resolve:"):
        continue
    out.append(line)

out.extend(block)
with open(pref, "w", encoding="utf-8", errors="surrogateescape") as fh:
    fh.write("\n".join(out) + "\n")

print(f"preferences: {pref}")
print(f"total lines: {len(out)}")
for line in block:
    print("  ", line)
