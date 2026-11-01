#!/usr/bin/env python3
"""Emit private build provenance without copying or disclosing proprietary bytes."""
import argparse
import hashlib
import json
from pathlib import Path

def digest(path):
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def record(rom, assets):
    rom, assets = Path(rom), Path(assets)
    for path in (rom, assets):
        if not path.is_file() or path.stat().st_size == 0:
            raise ValueError("required private input is missing or empty")
    return {"schema": 1, "rom_sha256": digest(rom),
            "rom_size": rom.stat().st_size,
            "asset_zip_sha256": digest(assets),
            "asset_zip_size": assets.stat().st_size,
            "private_assets_included": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("rom", type=Path)
    parser.add_argument("--asset-zip", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("build/private-build-provenance.json"))
    args = parser.parse_args()
    data = record(args.rom, args.asset_zip)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(data, sort_keys=True, indent=2) + "\n")
    print("Private build provenance saved:", args.output)

if __name__ == "__main__":
    main()
