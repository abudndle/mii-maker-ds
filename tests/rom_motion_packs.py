#!/usr/bin/env python3
"""Verify original skeletal motion packs survive DS ROM packaging byte for byte."""
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from rom_nitrofs_assets import check

FRAME_BYTES = 48 + 18 * 48
EXPECTED_CLIPS = 53


def validate(pack, label):
    if len(pack) < 32 or pack[:4] != b"MSP1":
        raise ValueError(f"{label}: bad motion pack signature")
    version, count, bones, stride, directory, length, reserved = struct.unpack_from("<7I", pack, 4)
    if (version != 1 or count != EXPECTED_CLIPS or bones != 18 or
            stride != FRAME_BYTES or directory != 32 or length != len(pack) or reserved):
        raise ValueError(f"{label}: motion pack header mismatch")
    expected = 32 + count * 40
    seen = set()
    for idx in range(count):
        offset = 32 + idx * 40
        raw_name = pack[offset:offset + 24]
        name = raw_name.split(b"\0", 1)[0]
        if (b"\0" not in raw_name or not name or
                any(not (48 <= b <= 57 or 65 <= b <= 90 or 97 <= b <= 122 or b == 95) for b in name)
                or name in seen):
            raise ValueError(f"{label}: invalid or duplicate clip name at {idx}")
        seen.add(name)
        start, frames, loop, fps = struct.unpack_from("<4I", pack, offset + 24)
        if start != expected or not 1 <= frames <= 7200 or loop > 1 or not 1 <= fps <= 60:
            raise ValueError(f"{label}: invalid clip directory entry {idx}")
        expected += frames * FRAME_BYTES
        if expected > len(pack):
            raise ValueError(f"{label}: truncated clip frames")
    if expected != len(pack):
        raise ValueError(f"{label}: trailing motion data")
    return count


def main():
    rom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "mii-ds.nds"
    try:
        rom = rom_path.read_bytes()
        files = check(rom, with_ranges=True)
        for gender in ("Male", "Female"):
            name = f"models/{gender}Body.msp"
            first, last = files[name]
            embedded = rom[first:last]
            count = validate(embedded, name)
            source = (ROOT / "nitrofiles" / name).read_bytes()
            if source != embedded:
                raise ValueError(f"{name}: packaged animation bytes differ from source")
            print(f"PASS: {gender} original motions, {count} clips, exact packaged bytes")
    except (OSError, KeyError, ValueError, struct.error) as error:
        raise SystemExit(f"FAIL: original motion packaging: {error}")


if __name__ == "__main__":
    main()
