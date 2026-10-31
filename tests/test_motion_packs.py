#!/usr/bin/env python3
"""Asset-free negative tests for original 53-clip MSP1 validation."""
import struct
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rom_motion_packs import FRAME_BYTES, EXPECTED_CLIPS, GALLERY_IDLE_CLIPS, ensure_gallery_clips, compare_rig_catalogs, validate


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
# The six original gallery clips must exist independently on each rig.
named = bytearray(valid)
for i, clip in enumerate(GALLERY_IDLE_CLIPS):
    named[32 + i * 40:32 + i * 40 + 24] = clip.encode().ljust(24, bytes((0,)))
ensure_gallery_clips(named, "synthetic")
missing = bytearray(named)
missing[32:56] = b"Other".ljust(24, bytes((0,)))
try:
    ensure_gallery_clips(missing, "synthetic")
except ValueError:
    pass
else:
    raise AssertionError("missing gallery idle clip was accepted")
compare_rig_catalogs(named, bytearray(named))
different = bytearray(named)
different[32:56] = b"Different".ljust(24, bytes((0,)))
assert validate(different, "synthetic") == EXPECTED_CLIPS
try:
    compare_rig_catalogs(named, different)
except ValueError:
    pass
else:
    raise AssertionError("mismatched male/female clip catalog was accepted")
# Both valid packs must also agree on source timing metadata by clip name.
different_fps = bytearray(named)
struct.pack_into("<I", different_fps, 32 + 36, 60)
assert validate(different_fps, "synthetic") == EXPECTED_CLIPS
try:
    compare_rig_catalogs(named, different_fps)
except ValueError:
    pass
else:
    raise AssertionError("mismatched male/female animation FPS was accepted")
# Exercise the public --asset-zip CLI with a real ZIP container, not only
# the helper functions. All data here is synthetic (no Nintendo assets).
with tempfile.TemporaryDirectory() as directory:
    archive_path = Path(directory) / "motions.zip"
    cli = Path(__file__).resolve().parent / "rom_motion_packs.py"

    def write_zip(male, female):
        with zipfile.ZipFile(archive_path, "w") as archive:
            archive.writestr("nitrofiles/models/MaleBody.msp", male)
            archive.writestr("nitrofiles/models/FemaleBody.msp", female)

    write_zip(named, named)
    result = subprocess.run([sys.executable, str(cli), "--source-only",
                             "--asset-zip", str(archive_path)], capture_output=True, text=True)
    assert result.returncode == 0, result.stdout + result.stderr

    write_zip(named, different_fps)
    result = subprocess.run([sys.executable, str(cli), "--source-only",
                             "--asset-zip", str(archive_path)], capture_output=True, text=True)
    assert result.returncode != 0, "ZIP CLI accepted mismatched original rig FPS"

    write_zip(named, valid)
    result = subprocess.run([sys.executable, str(cli), "--source-only",
                             "--asset-zip", str(archive_path)], capture_output=True, text=True)
    assert result.returncode != 0, "ZIP CLI accepted missing gallery idle clips"

print("PASS: valid 53-clip MSP1 and 19 corrupt motion-pack variants plus gallery clip and ZIP CLI coverage")
