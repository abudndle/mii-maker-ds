#!/usr/bin/env python3
"""Validate original NitroFS UI dependencies before building a private DS ROM.

Uses only source declarations and the owner's local ZIP. Never extracts or
redistributes copyrighted resource bytes; optional JSON contains counts only.
"""
import argparse
import json
import re
import struct
import sys
import zipfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent))
from private_balloon_art import derived_icons

ROOT = Path(__file__).resolve().parents[1]
UI_BYTES = 256 * 192 * 2
STATIC = re.compile(r'nitro:/([^"\s]+)')
CATEGORIES = re.compile(r'^\{"([A-Za-z0-9_]+)",(NULL|"[A-Za-z0-9_]+"),(\d+),(\d+),(\d+),\{', re.M)
FIELDS = re.compile(r'\{"[^"\n]+",(\d+),(\d+)\}')
SOURCE_F = re.compile(r'const MdsField mds_fields\[MDS_FIELDS\]\s*=\s*\{(.*?)\};', re.S)
DYNAMIC = {"art/%s%0*d.bin", "ui/%s.rgb555"}
OPTIONAL = {"test-import"}


def source_paths(root):
    source = Path(root) / "source"
    ui = (source / "ui_generated.h").read_text(encoding="utf-8")
    avatar = (source / "avatar.c").read_text(encoding="utf-8")
    files = sorted(source.rglob("*.c"))
    match = SOURCE_F.search(avatar)
    if not match:
        raise ValueError("Cannot identify original editor field maxima")
    maxima = [int(m[0]) for m in FIELDS.findall(match[1])]
    if len(maxima) != 62:
        raise ValueError(f"Editor field count changed: {len(maxima)}")
    categories = [(layout, prefix.strip('"'), int(digits), int(field), int(count))
                  for layout, prefix, digits, field, count in CATEGORIES.findall(ui)]
    if len(categories) != 13:
        raise ValueError(f"Editor category map changed: {len(categories)}")
    paths = set()
    art = set()
    backgrounds = set()
    for layout, prefix, digits, field, count in categories:
        if field >= len(maxima) or not 1 <= digits <= 3:
            raise ValueError("Unsafe editor category field or icon digits")
        background = f"ui/{layout}.rgb555"
        paths.add(background)
        backgrounds.add(background)
        if prefix == "NULL":
            if count != 0:
                raise ValueError("Category has icon slots without prefix")
            if layout == "EditBody":
                paths.add("art/BodySlider0.bin")
                art.add("art/BodySlider0.bin")
            continue
        if not 1 <= count <= 12:
            raise ValueError("Category has invalid feature page size")
        for index in range(maxima[field] + 1):
            name = f"art/{prefix}{index:0{digits}d}.bin"
            paths.add(name)
            art.add(name)
    runtime_static = set()
    dynamic = set()
    for file in files:
        for match in STATIC.finditer(file.read_text(encoding="utf-8")):
            name = match[1]
            if "%" in name:
                dynamic.add(name)
                continue
            if name in OPTIONAL:
                continue
            if name.startswith("/") or "\\" in name or ".." in name.split("/"):
                raise ValueError(f"Unsafe static NitroFS source path: {name}")
            paths.add(name)
            runtime_static.add(name)
    if dynamic != DYNAMIC:
        raise ValueError(f"Unreviewed dynamic NitroFS path templates: {sorted(dynamic ^ DYNAMIC)}")
    if not files or not runtime_static:
        raise ValueError("Missing runtime NitroFS paths")
    return paths, {"static": len(runtime_static), "backgrounds": len(backgrounds),
                   "feature_icons": len(art), "dynamic_templates": len(dynamic)}


def verify(archive, root=ROOT):
    paths, totals = source_paths(root)
    with zipfile.ZipFile(archive) as z:
        names = {}
        for info in z.infolist():
            if info.filename.startswith("nitrofiles/") and not info.is_dir():
                name = info.filename[len("nitrofiles/"):]
                if (not name or name.startswith("/") or "\\" in name or
                        any(part in ("", ".", "..") for part in name.split("/")) or
                        name in names):
                    raise ValueError("Unsafe/duplicate private NitroFS archive name")
                names[name] = info
        derived = derived_icons(z)
        missing = sorted(paths - (names.keys() | derived.keys()))
        if missing:
            raise ValueError(f"Runtime referenced NitroFS assets missing ({len(missing)}): {missing[:8]}")
        tested_ui = tested_art = 0
        # All shipped bitmaps and icons, including screens not currently used.
        graphics = {x for x in names if (x.startswith("ui/") and x.endswith(".rgb555")) or
                    (x.startswith("art/") and x.endswith(".bin"))}
        graphics.update(derived)
        for name in sorted(paths | graphics):
            data = derived.get(name)
            info = names.get(name)
            size = len(data) if data is not None else info.file_size
            if not size:
                raise ValueError("Empty NitroFS asset: " + name)
            if name.startswith("ui/") and name.endswith(".rgb555"):
                if size != UI_BYTES:
                    raise ValueError(f"Invalid DS RGB555 screen dimensions: {name}, {size}")
                tested_ui += 1
            if name.startswith("art/") and name.endswith(".bin"):
                if size < 6 or size > 4 + 2*128*128:
                    raise ValueError(f"Invalid feature sprite size: {name}")
                if data is None:
                    with z.open(info) as source:
                        header = source.read(4)
                else:
                    header = data[:4]
                width, height = struct.unpack("<HH", header)
                if not (1 <= width <= 256 and 1 <= height <= 192 and
                        width*height <= 128*128 and size == 4 + 2*width*height):
                    raise ValueError(f"Invalid RGB555 sprite header/payload: {name}")
                tested_art += 1
        return {**totals, "runtime_assets": len(paths), "verified_ui_bitmaps": tested_ui,
                "verified_art_sprites": tested_art, "packed_nitrofs_files": len(names) + len(derived)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("private_zip", type=Path)
    p.add_argument("--source-root", type=Path, default=ROOT)
    p.add_argument("--report", type=Path, help="Optional metadata-only JSON report")
    args = p.parse_args()
    try:
        report = verify(args.private_zip, args.source_root)
        if args.report:
            args.report.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
    except (OSError, zipfile.BadZipFile, ValueError, struct.error) as exc:
        p.exit(1, f"FAIL: runtime NitroFS asset parity: {exc}\n")
    print(f"PASS: {report['runtime_assets']} runtime NitroFS assets, "
          f"{report['verified_ui_bitmaps']} RGB555 screens, "
          f"{report['verified_art_sprites']} checked sprites")


if __name__ == "__main__":
    main()
