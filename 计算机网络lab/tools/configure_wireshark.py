"""configure_wireshark.py - add DKU/Lab2-friendly columns to the Wireshark profile.

Runs once; Wireshark writes its own preferences on exit, preserving these.
Idempotent: re-running replaces the managed block instead of duplicating it.
"""
import os
import re
import shutil
import time

pref = os.path.join(os.environ["APPDATA"], "Wireshark", "preferences")

COLUMNS = [
    ("No.", "0", "NUM"),
    ("Time", "1", "REL_TIME"),
    ("Source", "2", "SRC"),
    ("Destination", "3", "DST"),
    ("Protocol", "4", "PROTOCOL"),
    ("Length", "5", "FRAME_LEN"),
    ("eth.dst", "6", "eth.dst"),
    ("eth.src", "7", "eth.src"),
    ("eth.type", "8", "eth.type"),
    ("Info", "9", "INFO"),
]

BEGIN = "# --- DSH managed columns begin ---"
END = "# --- DSH managed columns end ---"

block = [BEGIN]
for name, num, field in COLUMNS:
    block.append(f'gui.column.format:\t"{name}"\t"%{field}"')
block.append(END)
block_text = "\n".join(block) + "\n"

text = ""
if os.path.exists(pref):
    with open(pref, "r", encoding="utf-8", errors="replace") as fh:
        text = fh.read()
    shutil.copy2(pref, pref + ".bak-dsh-" + time.strftime("%H%M%S"))

# drop any previous managed block (and any older stray gui.column.format lines)
text = re.sub(re.escape(BEGIN) + r".*?" + re.escape(END) + r"\n?", "", text, flags=re.S)
text = "\n".join(l for l in text.splitlines() if not l.startswith("gui.column.format:"))
if text and not text.endswith("\n"):
    text += "\n"

with open(pref, "w", encoding="utf-8") as fh:
    fh.write(text + block_text)

print(f"wrote {pref}")
print(f"backup: {pref}.bak-dsh-*")
print("columns:", ", ".join(n for n, _, _ in COLUMNS))
