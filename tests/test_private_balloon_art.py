#!/usr/bin/env python3
"""Synthetic-only conversion checks; no proprietary pixels are stored here."""
import struct
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from private_balloon_art import ICONS, GALLERY_SPRITES, SOURCE, derived_icons
from restore_asset_zip import REQUIRED, validate


def fixture(path, selected=None, corrupt=None, duplicate=None):
    if selected is None:
        selected = list(ICONS)
    with ZipFile(path, "w") as z:
        for name in selected:
            width, height = ICONS[name]
            data = bytes([0x80, 0x91]) * (width * height)
            if name == corrupt:
                data = data[:-2]
            z.writestr(SOURCE + name + ".bclim.rgb555", data)
        if duplicate:
            z.writestr("nitrofiles/art/Select/" + duplicate + ".bin", b"fake")


def rejects(path, expected):
    with ZipFile(path) as z:
        try:
            derived_icons(z)
        except ValueError as exc:
            assert expected in str(exc), (expected, str(exc))
        else:
            raise AssertionError("accepted " + expected)


with tempfile.TemporaryDirectory() as td:
    path = Path(td) / "fictional.zip"
    fixture(path, [])
    with ZipFile(path) as z:
        assert derived_icons(z) == {}
    fixture(path)
    with ZipFile(path) as z:
        assets = derived_icons(z)
    assert len(assets) == 4
    for name, (width, height) in ICONS.items():
        data = assets[f"art/Select/{name}.bin"]
        assert struct.unpack("<HH", data[:4]) == (width, height)
        assert len(data) == 4 + width * height * 2
        assert data[4:] == bytes([0x80, 0x91]) * (width * height)
    fixture(path, ["IconFavorite"])
    rejects(path, "incomplete")
    fixture(path, corrupt="IconOpen")
    rejects(path, "size")
    fixture(path, duplicate="IconCopyB")
    rejects(path, "duplicate")
    # The owner's ZIP may contain source-converted Select gallery textures
    # but lack the six separate NitroFS sprite wrappers.
    with ZipFile(path, "w") as z:
        for name, (width, height) in GALLERY_SPRITES.items():
            z.writestr(SOURCE + name + ".bclim.rgb555",
                       bytes([0x80, 0x91]) * (width * height))
    with ZipFile(path) as z:
        gallery = derived_icons(z)
    assert len(gallery) == 6
    for name, (width, height) in GALLERY_SPRITES.items():
        data = gallery[f"art/Select/{name}.bin"]
        assert struct.unpack("<HH", data[:4]) == (width, height)
        assert len(data) == 4 + width * height * 2
    # A partial original gallery set must not silently pass or be replaced
    # with fabricated art.
    with ZipFile(path, "w") as z:
        z.writestr(SOURCE + "BtnArrow.bclim.rgb555",
                   bytes([0x80, 0x91]) * (12 * 18))
    rejects(path, "incomplete original Select gallery")
    with ZipFile(path, "w") as z:
        for name, (width, height) in GALLERY_SPRITES.items():
            pixels = bytes([0x80, 0x91]) * (width * height)
            z.writestr(SOURCE + name + ".bclim.rgb555",
                       pixels[:-2] if name == "BtnScrollShadow" else pixels)
    rejects(path, "gallery sprite size")
    # Prepacked exact originals are accepted without duplicate NitroFS
    # destinations; mismatching prepacked bytes are rejected.
    with ZipFile(path, "w") as z:
        for name, (width, height) in GALLERY_SPRITES.items():
            pixels = bytes([0x80, 0x91]) * (width * height)
            z.writestr(SOURCE + name + ".bclim.rgb555", pixels)
            if name == "BtnArrow":
                z.writestr("nitrofiles/art/Select/BtnArrow.bin",
                           struct.pack("<HH", width, height) + pixels)
    with ZipFile(path) as z:
        assert len(derived_icons(z)) == 5
    with ZipFile(path, "a") as z:
        z.writestr("nitrofiles/art/Select/BtnMiiB.bin", b"wrong")
    rejects(path, "prepacked original gallery sprite mismatch")
    # Full private restore adds only derived original icons to local NitroFS.
    with ZipFile(path, "w") as z:
        for required in REQUIRED:
            z.writestr(required, b"fictional fixture")
        for name, (width, height) in ICONS.items():
            z.writestr(SOURCE + name + ".bclim.rgb555",
                       bytes([0x80, 0x91]) * (width * height))
    destination = Path(td) / "restore"
    destination.mkdir()
    assert validate(path, destination) == 0
    for name, (width, height) in ICONS.items():
        data = (destination / "nitrofiles/art/Select" / (name + ".bin")).read_bytes()
        assert struct.unpack("<HH", data[:4]) == (width, height)
        assert len(data) == 4 + width * height * 2
print("PASS: private SelectBalloonButton icon derivation, safe restoration and fail-closed inputs")
