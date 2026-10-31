#!/usr/bin/env python3
"""Verify original skeletal motion packs survive DS ROM packaging byte for byte."""
import argparse
import math
import struct
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from rom_nitrofs_assets import check

FRAME_BYTES = 48 + 18 * 48
EXPECTED_CLIPS = 53
GALLERY_IDLE_CLIPS = ("Wait00", "Wait01", "Wait02", "Wait03Pre", "Wait03", "Wait04")


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
        for frame in range(frames):
            at = start + frame * FRAME_BYTES
            if not all(math.isfinite(v) and abs(v) <= 4096 for v in
                       struct.unpack_from("<12f", pack, at)):
                raise ValueError(f"{label}: invalid head matrix in clip {idx}, frame {frame}")
            # Same Q16.16 bounds required by source/motion.c at playback.
            for (value,) in struct.iter_unpack("<i", memoryview(pack)[at + 48:at + FRAME_BYTES]):
                if not -4096 * 65536 <= value <= 4096 * 65536:
                    raise ValueError(f"{label}: invalid bone matrix in clip {idx}, frame {frame}")
    if expected != len(pack):
        raise ValueError(f"{label}: trailing motion data")
    return count


def ensure_gallery_clips(pack, label):
    """Required original idle clips must be resolvable by name on both rigs."""
    names = set()
    count = struct.unpack_from("<I", pack, 8)[0]
    for i in range(count):
        name = pack[32 + i * 40:32 + i * 40 + 24].split(bytes((0,)), 1)[0]
        names.add(name.decode("ascii"))
    missing = sorted(set(GALLERY_IDLE_CLIPS) - names)
    if missing:
        raise ValueError(f"{label}: missing gallery animation clips: {', '.join(missing)}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", nargs="?", type=Path, default=ROOT / "mii-ds.nds")
    parser.add_argument("--source-only", action="store_true",
                        help="validate source motion assets before compiling a ROM")
    args = parser.parse_args()
    try:
        rom = args.rom.read_bytes() if not args.source_only else None
        files = check(rom, with_ranges=True) if rom is not None else None
        for gender in ("Male", "Female"):
            name = f"models/{gender}Body.msp"
            source = (ROOT / "nitrofiles" / name).read_bytes()
            count = validate(source, name)
            ensure_gallery_clips(source, name)
            if files is not None:
                first, last = files[name]
                if rom[first:last] != source:
                    raise ValueError(f"{name}: packaged animation bytes differ from source")
            kind = "source validated" if files is None else "exact packaged bytes"
            print(f"PASS: {gender} original motions, {count} clips, {kind}")
    except (OSError, KeyError, ValueError, struct.error) as error:
        raise SystemExit(f"FAIL: original motion packaging: {error}")


if __name__ == "__main__":
    main()
