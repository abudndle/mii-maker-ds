#!/usr/bin/env python3
"""Verify a copied non-Personal Mii persisted after a fresh melonDS launch.

Only isolated synthetic 8K EEPROM snapshots are accepted. Never print save
bytes, Mii names, or private paths.
"""
import argparse
import json
import struct
import zlib
from pathlib import Path

from check_gallery_favorite_save import (_bit, _validate, BODY_SIZE,
                                         FAVORITE_BIT, PERSONAL_BIT,
                                         RECORD_SIZE, SLOTS)

IMPORT_BIT = 259  # field 61: Import status, two bits in compact v2


def verify(before, after, source=1, destination=10):
    if not (0 <= source < SLOTS and 0 <= destination < SLOTS) or source == destination:
        raise ValueError("invalid source or destination slot")
    prior = _validate(before)
    current = _validate(after)
    if current != (prior + 1) & 0xffffffff:
        raise ValueError("copy did not advance save generation exactly once")
    if sum(before[24 + i * RECORD_SIZE] for i in range(SLOTS)) != 10:
        raise ValueError("expected ten saved Miis before copy")
    if before[24 + source * RECORD_SIZE] != 1 or before[24 + destination * RECORD_SIZE]:
        raise ValueError("source missing or destination already occupied")
    if any(before[24 + i * RECORD_SIZE] == 0 for i in range(destination)):
        raise ValueError("destination was not first free slot")
    if _bit(before, source, PERSONAL_BIT):
        raise ValueError("cannot use Personal Mii as copy source")
    if not _bit(before, source, FAVORITE_BIT):
        raise ValueError("Favorite acceptance must precede copy restart")
    expected = bytearray(before)
    struct.pack_into("<I", expected, 8, current)
    src = 24 + source * RECORD_SIZE
    dst = 24 + destination * RECORD_SIZE
    expected[dst:dst + RECORD_SIZE] = before[src:src + RECORD_SIZE]
    for bit in (FAVORITE_BIT, PERSONAL_BIT, IMPORT_BIT, IMPORT_BIT + 1):
        pos = dst + 1 + bit // 8
        expected[pos] &= ~(1 << (bit % 8))
    struct.pack_into("<I", expected, BODY_SIZE, zlib.crc32(expected[:BODY_SIZE]))
    if after != expected:
        raise ValueError("copy changed unrelated Miis, flags, settings or EEPROM bytes")
    return {"verified": True, "source_slot": source, "new_slot": destination,
            "saved_miis": 11, "copy_flags_reset": True,
            "original_unchanged": True, "generation_advanced": True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        result = verify(args.before.read_bytes(), args.after.read_bytes())
        if args.report:
            args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    except (OSError, ValueError) as exc:
        p.exit(1, f"FAIL: gallery copy/restart EEPROM acceptance: {exc}\n")
    print("PASS: copy persisted after fresh emulator launch; source and all other records unchanged")


if __name__ == "__main__":
    main()
