#!/usr/bin/env python3
"""Fail-closed private EEPROM checks for a received Mii's copy-before-edit.

The source must remain read-only. A cancelled confirmation must not write
anything; accepting must create exactly one ordinary editable copy without
changing any other record. Only synthetic 8K compact-v2 saves are supported.
No Mii names, save bytes, or private paths are printed.
"""
import argparse
import json
import struct
import zlib
from pathlib import Path

from check_gallery_favorite_save import (
    _bit, _validate, BODY_SIZE, FAVORITE_BIT, PERSONAL_BIT, RECORD_SIZE, SLOTS,
)
from check_gallery_copy_save import IMPORT_BIT

# Packed v2 fields 46 (Favorite), 47 (Sharing), 48 (Copy permission).
COPY_ALLOWED_BIT = FAVORITE_BIT + 2


def _received_source(before, source, destination):
    if not (0 <= source < SLOTS and 0 <= destination < SLOTS) or source == destination:
        raise ValueError("invalid source or destination slot")
    _validate(before)
    if sum(before[24 + i * RECORD_SIZE] for i in range(SLOTS)) != 10:
        raise ValueError("expected ten synthetic saved Miis")
    if sum(_bit(before, i, PERSONAL_BIT) for i in range(SLOTS)
           if before[24 + i * RECORD_SIZE]) != 1:
        raise ValueError("expected exactly one Personal Mii")
    if before[24 + source * RECORD_SIZE] != 1 or _bit(before, source, PERSONAL_BIT):
        raise ValueError("source missing or Personal")
    if (_bit(before, source, IMPORT_BIT),
            _bit(before, source, IMPORT_BIT + 1)) != (1, 0):
        raise ValueError("source must be received, not special or ordinary")
    if not _bit(before, source, COPY_ALLOWED_BIT):
        raise ValueError("received source does not permit copying")
    if before[24 + destination * RECORD_SIZE]:
        raise ValueError("copy destination already occupied")
    if any(not before[24 + i * RECORD_SIZE] for i in range(destination)):
        raise ValueError("copy destination is not first free slot")


def verify_cancel(before, after, source=1, destination=10):
    """A rejected/cancelled received-Mii prompt must not change EEPROM."""
    _received_source(before, source, destination)
    _validate(after)
    if before != after:
        raise ValueError("cancel changed cartridge EEPROM bytes")
    return {"verified": True, "cancel_unchanged": True}


def verify_copy(before, after, source=1, destination=10):
    """Accept one exact copy transaction; source, flags and all else unchanged."""
    _received_source(before, source, destination)
    first = _validate(before)
    second = _validate(after)
    if second != (first + 1) & 0xffffffff:
        raise ValueError("received copy did not advance generation exactly once")
    expected = bytearray(before)
    struct.pack_into("<I", expected, 8, second)
    src = 24 + source * RECORD_SIZE
    dst = 24 + destination * RECORD_SIZE
    expected[dst:dst + RECORD_SIZE] = before[src:src + RECORD_SIZE]
    for bit in (FAVORITE_BIT, PERSONAL_BIT, IMPORT_BIT, IMPORT_BIT + 1):
        expected[dst + 1 + bit // 8] &= ~(1 << (bit % 8))
    struct.pack_into("<I", expected, BODY_SIZE, zlib.crc32(expected[:BODY_SIZE]))
    if after != expected:
        raise ValueError("received copy changed original, permissions, or unrelated EEPROM bytes")
    return {"verified": True, "source_unchanged": True, "new_slot": destination,
            "saved_miis": 11, "received_flags_reset": True,
            "generation_advanced": True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("after", type=Path)
    p.add_argument("--mode", choices=("cancel", "copy"), required=True)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    try:
        before, after = args.before.read_bytes(), args.after.read_bytes()
        result = (verify_cancel if args.mode == "cancel" else verify_copy)(before, after)
        if args.report:
            args.report.write_text(json.dumps(result, sort_keys=True, indent=2) + "\n")
    except (OSError, ValueError) as exc:
        p.exit(1, "FAIL: received Mii EEPROM acceptance: %s\n" % exc)
    print("PASS: received Mii %s EEPROM transaction verified" % args.mode)


if __name__ == "__main__":
    main()
