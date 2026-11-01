#!/usr/bin/env python3
"""Derive private DS sprites from the owner's original Select.arc textures.

Only source-independent dimensions and code are committed. The returned bytes
are never printed or uploaded; they are packed into a private local ROM.
"""
from __future__ import annotations
import struct

SOURCE = "assets/converted/layout/Select.arc.files/timg/"
# Original SelectBalloonButton picture pane texture dimensions (CLIM).
ICONS = {
    "IconFavorite": (32, 32),
    "IconMyMii": (32, 32),
    "IconCopyB": (20, 18),
    "IconOpen": (16, 16),
}


def derived_icons(archive) -> dict[str, bytes]:
    """Return NitroFS-relative path -> exact header + original RGB555A1 pixels.

    Archives predating this private resource set may contain none of the four
    converted icons, in which case the runtime uses the existing text labels.
    A partially present or malformed set must never silently build.
    """
    members = set(archive.namelist())
    found = [name for name in ICONS if SOURCE + name + ".bclim.rgb555" in members]
    if not found:
        return {}
    if len(found) != len(ICONS):
        raise ValueError("incomplete original SelectBalloonButton icon set")
    result = {}
    for name, (width, height) in ICONS.items():
        path = SOURCE + name + ".bclim.rgb555"
        pixels = archive.read(path)
        if len(pixels) != 2 * width * height:
            raise ValueError(f"invalid converted original icon size: {name}")
        target = f"art/Select/{name}.bin"
        if "nitrofiles/" + target in members:
            raise ValueError(f"duplicate derived original icon destination: {target}")
        result[target] = struct.pack("<HH", width, height) + pixels
    return result
