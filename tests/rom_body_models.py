#!/usr/bin/env python3
"""Confirm packaged Nintendo DS ROM retains valid original Mii body geometry."""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(ROOT / "tools"))
from rom_nitrofs_assets import check
from validate_body_models import inspect_bytes

rom_path = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "mii-ds.nds"
try:
    data = rom_path.read_bytes()
    files = check(data, with_ranges=True)
    for gender in ("Male", "Female"):
        name = f"models/{gender}Body.bin"
        start, end = files[name]
        vertices, triangles = inspect_bytes(data[start:end], name)
        print(f"PASS: embedded original {gender} body: {vertices} vertices / {triangles} triangles")
except (OSError, ValueError, KeyError) as error:
    raise SystemExit(f"FAIL: packaged original model validation: {error}")
