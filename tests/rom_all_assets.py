#!/usr/bin/env python3
"""Compare every DS NitroFS payload against private original-resource inputs.

No Nintendo resource bytes are stored in this repository.
"""
import argparse
import sys
import zipfile
from pathlib import Path

from rom_nitrofs_assets import check

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from private_balloon_art import derived_icons
MAX_ASSET_BYTES = 32 * 1024 * 1024
MAX_TOTAL_BYTES = 128 * 1024 * 1024


def compare_assets(rom, ranges, originals):
    """Reject missing, extra, truncated, or changed resource files."""
    missing = sorted(originals.keys() - ranges.keys())
    extra = sorted(ranges.keys() - originals.keys())
    if missing or extra:
        raise ValueError(f"NitroFS names differ: missing {missing[:8]}, extra {extra[:8]}")
    for name in sorted(originals):
        first, last = ranges[name]
        if not 0 <= first < last <= len(rom):
            raise ValueError(f"{name}: invalid ROM asset range")
        if rom[first:last] != originals[name]:
            raise ValueError(f"{name}: ROM bytes differ from source")
    return len(originals)


def read_assets(asset_zip=None, asset_dir=None):
    """Read only nitrofiles/ entries; never extract untrusted ZIP paths."""
    if asset_zip:
        originals = {}
        with zipfile.ZipFile(asset_zip) as archive:
            for entry in archive.infolist():
                name = entry.filename
                if not name.startswith("nitrofiles/") or name.endswith("/"):
                    continue
                relative = name[len("nitrofiles/"):]
                if (not relative or relative.startswith("/") or
                        any(part in ("", ".", "..") for part in relative.split("/")) or
                        "\\" in relative or relative in originals):
                    raise ValueError(f"unsafe or repeated private NitroFS path: {name}")
                if entry.file_size <= 0 or entry.file_size > MAX_ASSET_BYTES:
                    raise ValueError(f"{name}: unreasonable resource size")
                originals[relative] = archive.read(entry)
            # The four original Select.arc icons are derived from the same
            # private ZIP, so full ROM parity still rejects every extra byte.
            originals.update(derived_icons(archive))
    else:
        folder = Path(asset_dir or ROOT / "nitrofiles")
        originals = {}
        for path in folder.rglob("*"):
            if not path.is_file():
                continue
            if path.is_symlink():
                raise ValueError(f"symlink in original-resource tree: {path}")
            relative = path.relative_to(folder).as_posix()
            if path.stat().st_size <= 0 or path.stat().st_size > MAX_ASSET_BYTES:
                raise ValueError(f"{relative}: unreasonable resource size")
            originals[relative] = path.read_bytes()
    if not originals or sum(map(len, originals.values())) > MAX_TOTAL_BYTES:
        raise ValueError("missing or oversized private NitroFS asset collection")
    return originals


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path, help="built Mii Maker DS ROM")
    inputs = parser.add_mutually_exclusive_group()
    inputs.add_argument("--asset-zip", type=Path, help="private resource ZIP")
    inputs.add_argument("--asset-dir", type=Path, help="restored nitrofiles directory")
    args = parser.parse_args()
    try:
        rom = args.rom.read_bytes()
        ranges = check(rom, with_ranges=True)
        originals = read_assets(args.asset_zip, args.asset_dir)
        count = compare_assets(rom, ranges, originals)
    except (OSError, ValueError, UnicodeDecodeError, zipfile.BadZipFile) as exc:
        parser.exit(1, f"FAIL: original NitroFS parity: {exc}\n")
    print(f"PASS: all {count} NitroFS files are byte-identical to original resource inputs")


if __name__ == "__main__":
    main()
