#!/usr/bin/env python3
"""Asset-free negative tests for original 53-clip MSP1 validation."""
import struct
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rom_motion_packs import FRAME_BYTES, EXPECTED_CLIPS, validate


def example():
    frame_counts = [1] * EXPECTED_CLIPS
    length = 32 + EXPECTED_CLIPS * 40 + sum(frame_counts) * FRAME_BYTES
    data = bytearray(length)
    data[:4] = b"MSP1"
    struct.pack_into("<7I", data, 4, 1, EXPECTED_CLIPS, 18, FRAME_BYTES, 32, length, 0)
    pos = 32 + EXPECTED_CLIPS * 40
    for i in range(EXPECTED_CLIPS):
        index = 32 + i * 40
        data[index:index + 24] = (f"Clip{i:02d}".encode()).ljust(24, b"\0")
        struct.pack_into("<4I", data, index + 24, pos, 1, 1, 30)
        pos += FRAME_BYTES
    return data


def must_reject(data):
    try:
        validate(data, "synthetic")
    except (ValueError, struct.error):
        return
    raise AssertionError("corrupted original motion pack was accepted")


valid = example()
assert validate(valid, "synthetic") == EXPECTED_CLIPS
bad = bytearray(valid)
bad[:4] = b"XXXX"
must_reject(bad)
must_reject(valid[:-1])
bad = bytearray(valid)
bad[72:96] = bad[32:56]  # second clip duplicates first name
must_reject(bad)
for field, value in ((8, 52), (12, 17), (16, FRAME_BYTES - 1),
                     (20, 0), (24, len(valid) - 1), (28, 1)):
    bad = bytearray(valid)
    struct.pack_into("<I", bad, field, value)
    must_reject(bad)
for field, value in ((32 + 24, 0), (32 + 28, 0), (32 + 32, 2),
                     (32 + 36, 0), (32 + 36, 61)):
    bad = bytearray(valid)
    struct.pack_into("<I", bad, field, value)
    must_reject(bad)
frame_start = 32 + EXPECTED_CLIPS * 40
for value in (float("nan"), float("inf"), 4097.0):
    bad = bytearray(valid)
    struct.pack_into("<f", bad, frame_start, value)
    must_reject(bad)
for value in (4096 * 65536 + 1, -4096 * 65536 - 1):
    bad = bytearray(valid)
    struct.pack_into("<i", bad, frame_start + 48, value)
    must_reject(bad)
print("PASS: valid 53-clip MSP1 and 19 corrupt motion-pack variants")
