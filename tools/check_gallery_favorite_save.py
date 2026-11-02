#!/usr/bin/env python3
"""Verify one persisted Favorite toggle in a private melonDS 8K EEPROM.

The checker prints no Mii names or save bytes. It requires an independently
captured pre-interaction image and rejects any unrelated cartridge changes.
"""
import argparse
import json
import struct
import zlib
from pathlib import Path

SAVE_SIZE = 8192
SLOTS = 100
RECORD_SIZE = 75
BODY_SIZE = 24 + SLOTS * RECORD_SIZE
# Source save_compact.c v2 packs each field at its minimum bit width.
# Field 46 (Favorite) starts after 183 bits; field 51 (Personal) after 195.
FAVORITE_BIT = 183
PERSONAL_BIT = 195


def _bit(image, slot, field_bit):
    pos = 24 + slot * RECORD_SIZE + 1 + field_bit // 8
    return (image[pos] >> (field_bit % 8)) & 1


def _validate(image):
    if len(image) != SAVE_SIZE:
        raise ValueError("expected exactly 8192 bytes of compact EEPROM")
    if image[:4] != b"MDSC" or struct.unpack_from("<I", image, 4)[0] != 2:
        raise ValueError("expected version 2 compact EEPROM")
    if struct.unpack_from("<I", image, 12)[0] != BODY_SIZE:
        raise ValueError("invalid compact body length")
    if struct.unpack_from("<I", image, BODY_SIZE)[0] != zlib.crc32(image[:BODY_SIZE]):
        raise ValueError("compact EEPROM CRC mismatch")
    if any(image[24 + i * RECORD_SIZE] not in (0, 1) for i in range(SLOTS)):
        raise ValueError("invalid slot occupancy")
    return struct.unpack_from("<I", image, 8)[0]


def verify(before, after, slot=1, expected_miis=10):
    """Accept exactly one non-Personal Mii Favorite toggle and one save generation."""
    if not 0 <= slot < SLOTS:
        raise ValueError("target slot outside gallery")
    first = _validate(before)
    second = _validate(after)
    if second != (first + 1) & 0xffffffff:
        raise ValueError("save generation did not advance exactly once")
    count = sum(before[24 + i * RECORD_SIZE] for i in range(SLOTS))
    if count != expected_miis:
        raise ValueError("unexpected number of saved Miis in baseline")
    if before[24 + slot * RECORD_SIZE] != 1 or _bit(before, slot, PERSONAL_BIT):
        raise ValueError("target is missing or is the Personal Mii")
    if sum(_bit(before, i, PERSONAL_BIT) for i in range(SLOTS)
           if before[24 + i * RECORD_SIZE]) != 1:
        raise ValueError("baseline must contain exactly one Personal Mii")
    if _bit(before, slot, FAVORITE_BIT) != 0 or _bit(after, slot, FAVORITE_BIT) != 1:
        raise ValueError("target Favorite was not enabled")
    expected = bytearray(before)
    struct.pack_into("<I", expected, 8, second)
    pos = 24 + slot * RECORD_SIZE + 1 + FAVORITE_BIT // 8
    expected[pos] ^= 1 << (FAVORITE_BIT % 8)
    struct.pack_into("<I", expected, BODY_SIZE, zlib.crc32(expected[:BODY_SIZE]))
    if after != expected:
        raise ValueError("unrelated saved Mii, settings, or EEPROM bytes changed")
    return {"verified": True, "slot": slot, "saved_miis": count,
            "favorite_enabled": True, "generation_advanced": True,
            "unrelated_bytes_unchanged": True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--slot", type=int, default=1)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        result = verify(args.before.read_bytes(), args.after.read_bytes(), args.slot)
        if args.report:
            args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    except (OSError, ValueError) as exc:
        p.exit(1, f"FAIL: gallery Favorite EEPROM acceptance: {exc}\n")
    print("PASS: one non-Personal Favorite persisted; every other EEPROM byte preserved")


if __name__ == "__main__":
    main()
