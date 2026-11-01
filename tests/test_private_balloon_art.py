#!/usr/bin/env python3
"""Synthetic-only conversion checks; no proprietary pixels are stored here."""
import struct
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from private_balloon_art import ICONS, SOURCE, derived_icons


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
print("PASS: private SelectBalloonButton icon derivation, dimensions and fail-closed inputs")
