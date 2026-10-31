#!/usr/bin/env python3
"""Ensure invalid gallery pointers are rejected before cartridge I/O."""
from pathlib import Path
import re

source = (Path(__file__).resolve().parents[1] / "source/save_nds.c").read_text()
for name, expected in (
    ("mds_cart_open", "if(!g)return 0;"),
    ("mds_cart_flush", "if(!g||!ready)return 0;"),
):
    match = re.search(r"int\s+" + name + r"\s*\(MdsGallery\s*\*g\)\s*\{", source)
    if not match:
        raise SystemExit("FAIL: missing " + name)
    body = source[match.end():]
    if expected not in body[:170]:
        raise SystemExit("FAIL: " + name + " must guard null input before use")
print("PASS: cartridge save entry points reject invalid gallery pointers")
