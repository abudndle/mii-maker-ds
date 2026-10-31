#!/usr/bin/env python3
"""Validate executable ARM9/ARM7 sections of a packaged Nintendo DS ROM."""
import argparse
import struct
from pathlib import Path


def check(data: bytes) -> None:
    if len(data) < 0x200 or data[0x0c:0x10] != b"MDSD":
        raise ValueError("Not a Mii Maker DS cartridge image")

    def u32(offset: int) -> int:
        return struct.unpack_from("<I", data, offset)[0]

    ranges = []
    for name, header in (("ARM9", 0x20), ("ARM7", 0x30)):
        source, entry, destination, size = (u32(header + off) for off in (0, 4, 8, 12))
        if not size or size % 4:
            raise ValueError(name + ": missing or unaligned executable")
        if source < 0x4000 or source % 4 or source + size > len(data):
            raise ValueError(name + ": section outside ROM")
        if entry % 4 or destination % 4 or not destination <= entry < destination + size:
            raise ValueError(name + ": entry point outside loaded program")
        if not any(data[source:source + size]):
            raise ValueError(name + ": empty program")
        ranges.append((source, source + size, name))
    ranges.sort()
    if ranges[0][1] > ranges[1][0]:
        raise ValueError("ARM9 and ARM7 executable sections overlap")
    for name, offset in (("ARM9 overlays", 0x50), ("ARM7 overlays", 0x58)):
        start, size = u32(offset), u32(offset + 4)
        if bool(start) != bool(size):
            raise ValueError(name + ": incomplete overlay table")
        if size and (start + size > len(data) or size % 32):
            raise ValueError(name + ": invalid overlay table range")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", nargs="?", type=Path, default=Path("mii-ds.nds"))
    args = parser.parse_args()
    try:
        check(args.rom.read_bytes())
    except (OSError, ValueError, struct.error) as error:
        parser.exit(1, f"FAIL: {error}\n")
    print("PASS: ARM9 and ARM7 sections, entry points, and overlay table bounds")
