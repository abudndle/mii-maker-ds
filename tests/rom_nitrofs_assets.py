#!/usr/bin/env python3
"""Verify that a built DS ROM contains accessible, nonempty original NitroFS assets."""
import argparse
import struct
from pathlib import Path

REQUIRED = (
    "cfl/CFL_Res.dat",
    "models/MaleBody.msp", "models/FemaleBody.msp",
    "models/MaleBody.bin", "models/FemaleBody.bin",
    "models/MaleBody.ani", "models/FemaleBody.ani",
    "ui/EditBody.rgb555", "ui/home-bottom.rgb555",
    "ui/profile.rgb555", "ui/import-bottom.rgb555",
    "ui/qr-menu-ds.rgb555", "ui/qr-menu-dsi.rgb555",
    "ui/photo-select.rgb555",
    "art/StatusPersonal.bin", "art/StatusFavorite.bin",
    "font/number.bin",
)


def check(rom: bytes) -> dict:
    def u16(offset):
        return struct.unpack_from("<H", rom, offset)[0]

    def u32(offset):
        return struct.unpack_from("<I", rom, offset)[0]

    if len(rom) < 0x200 or rom[0x0c:0x10] != b"MDSD":
        raise ValueError("Not a Mii Maker DS ROM")
    fnt, fnt_size = u32(0x40), u32(0x44)
    fat, fat_size = u32(0x48), u32(0x4c)
    boundary = u32(0x80)
    if (not fnt_size or not fat_size or fat_size % 8 or
            fnt + fnt_size > len(rom) or fat + fat_size > len(rom)):
        raise ValueError("Invalid NitroFS table bounds")
    count = fat_size // 8
    if fnt_size < 8:
        raise ValueError("Invalid directory table")
    dir_count = u16(fnt + 6)
    if dir_count < 1 or dir_count * 8 > fnt_size:
        raise ValueError("Invalid NitroFS directory count")
    files = {}
    ranges = []
    visited = set()

    def walk(directory, prefix):
        index = directory & 0xfff
        if directory & 0xf000 != 0xf000 or index >= dir_count:
            raise ValueError("Invalid NitroFS directory reference")
        if index in visited:
            raise ValueError("Repeated or cyclic NitroFS directory")
        visited.add(index)
        offset, file_id, _ = struct.unpack_from("<IHH", rom, fnt + index * 8)
        cursor = fnt + offset
        while True:
            if cursor >= fnt + fnt_size:
                raise ValueError("Unterminated NitroFS directory")
            entry = rom[cursor]
            cursor += 1
            if entry == 0:
                return
            length = entry & 0x7f
            if length == 0 or cursor + length > fnt + fnt_size:
                raise ValueError("Invalid NitroFS filename")
            name = rom[cursor:cursor + length].decode("ascii")
            cursor += length
            if entry & 0x80:
                if cursor + 2 > fnt + fnt_size:
                    raise ValueError("Truncated subdirectory reference")
                subdir = u16(cursor)
                cursor += 2
                walk(subdir, prefix + name + "/")
            else:
                if file_id >= count:
                    raise ValueError("File ID outside NitroFS FAT")
                first, last = u32(fat + file_id * 8), u32(fat + file_id * 8 + 4)
                if not 0x8000 <= first < last <= min(boundary, len(rom)):
                    raise ValueError("Unreachable or empty NitroFS file: " + prefix + name)
                path = prefix + name
                if path in files:
                    raise ValueError("Duplicate NitroFS filename: " + path)
                files[path] = file_id
                ranges.append((first, last, path))
                file_id += 1

    walk(0xf000, "")
    if len(files) != count or set(files.values()) != set(range(count)):
        raise ValueError("Not all NitroFS FAT entries are indexed")
    ranges.sort()
    for previous, following in zip(ranges, ranges[1:]):
        if previous[1] > following[0]:
            raise ValueError('Overlapping NitroFS file payloads: ' + previous[2] + ' and ' + following[2])
    missing = sorted(set(REQUIRED) - files.keys())
    if missing:
        raise ValueError("Required original resources missing from ROM: " + ", ".join(missing))
    return files


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("rom", nargs="?", type=Path, default=Path("mii-ds.nds"))
    args = parser.parse_args()
    try:
        paths = check(args.rom.read_bytes())
    except (OSError, ValueError, struct.error, UnicodeDecodeError) as error:
        parser.exit(1, "FAIL: " + str(error) + "\n")
    print(f"PASS: {len(paths)} accessible NitroFS entries, all {len(REQUIRED)} original resources packaged")
