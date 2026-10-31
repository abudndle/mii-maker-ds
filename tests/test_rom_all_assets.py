#!/usr/bin/env python3
"""Asset-free regression tests for exact complete NitroFS packaging parity."""
from pathlib import Path
import sys
import tempfile
import zipfile

sys.path.insert(0, str(Path(__file__).resolve().parent))
from rom_all_assets import compare_assets, read_assets


def rejects(fn, label):
    try:
        fn()
    except ValueError:
        return
    raise AssertionError("accepted " + label)


rom = b"HEADER" + b"ABC" + b"DEF!" + b"TAIL"
ranges = {"ui/a.rgb555": (6, 9), "models/b.bin": (9, 13)}
assets = {"ui/a.rgb555": b"ABC", "models/b.bin": b"DEF!"}
assert compare_assets(rom, ranges, assets) == 2
rejects(lambda: compare_assets(rom, ranges, {**assets, "font/c.bin": b"X"}),
        "missing packaged resource")
rejects(lambda: compare_assets(rom, ranges, {"ui/a.rgb555": b"ABC"}),
        "extra packaged resource")
rejects(lambda: compare_assets(rom, ranges, {**assets, "models/b.bin": b"DEF?"}),
        "modified packaged resource")
rejects(lambda: compare_assets(rom, ranges, {**assets, "models/b.bin": b"DEF"}),
        "truncated packaged resource")
rejects(lambda: compare_assets(rom, {**ranges, "models/b.bin": (9, len(rom)+1)}, assets),
        "out-of-bounds NitroFS range")
rejects(lambda: compare_assets(rom, {**ranges, "models/b.bin": (13, 9)}, assets),
        "reversed NitroFS range")

with tempfile.TemporaryDirectory() as temporary:
    root = Path(temporary)
    archive = root / "assets.zip"
    with zipfile.ZipFile(archive, "w") as zipfile_out:
        zipfile_out.writestr("reference/not-a-rom-file.bin", b"IGNORE")
        zipfile_out.writestr("nitrofiles/ui/a.rgb555", b"ABC")
        zipfile_out.writestr("nitrofiles/models/b.bin", b"DEF!")
    assert read_assets(asset_zip=archive) == assets

    original_dir = root / "nitrofiles"
    for relative, data in assets.items():
        path = original_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
    assert read_assets(asset_dir=original_dir) == assets

    with zipfile.ZipFile(archive, "w") as zipfile_out:
        zipfile_out.writestr("nitrofiles/../private.bin", b"NO")
    rejects(lambda: read_assets(asset_zip=archive), "unsafe ZIP traversal")

    with zipfile.ZipFile(archive, "w") as zipfile_out:
        zipfile_out.writestr("nitrofiles/ui/empty.bin", b"")
    rejects(lambda: read_assets(asset_zip=archive), "empty NitroFS resource")

print("PASS: full NitroFS byte parity, missing/extra/corrupt payloads, ZIP and folder validation")
