#!/usr/bin/env python3
"""Asset-free regression tests for the original BOD2 Mii body validator."""
import math
import struct
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from validate_body_models import inspect


def mesh():
    buf = bytearray(56 + 3 * 12)
    buf[:4] = b"BOD2"
    struct.pack_into("<I", buf, 4, 3)
    struct.pack_into("<12f", buf, 8,
                     1, 0, 0, 0, 0, 1, 0, 0, 0, 0, 1, 0)
    for i in range(3):
        buf[56 + i * 12 + 9] = i % 2
        buf[56 + i * 12 + 10] = i
    return buf


def rejects(path, data):
    path.write_bytes(data)
    try:
        inspect(path)
    except ValueError:
        return
    raise AssertionError("invalid body mesh accepted")


with tempfile.TemporaryDirectory() as temp:
    path = Path(temp) / "MaleBody.bin"
    valid = mesh()
    path.write_bytes(valid)
    assert inspect(path) == (3, 1)

    bad = bytearray(valid)
    bad[:4] = b"XXXX"
    rejects(path, bad)
    rejects(path, valid[:-1])
    for count in (0, 1, 4, 12003, 0xffffffff):
        bad = bytearray(valid)
        struct.pack_into("<I", bad, 4, count)
        rejects(path, bad)
    bad = bytearray(valid)
    bad[56 + 10] = 18
    rejects(path, bad)
    bad = bytearray(valid)
    bad[56 + 9] = 2
    rejects(path, bad)
    for value in (math.nan, math.inf, -math.inf, 4097.0):
        bad = bytearray(valid)
        struct.pack_into("<f", bad, 8, value)
        rejects(path, bad)

print("PASS: original Mii body validator accepts valid BOD2 and rejects 13 corruptions")
