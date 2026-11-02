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

# Exact original Select.arc texture dimensions, also checked by the DS
# gallery sprite loaders. These six controls were formerly supplied as a
# separate private NitroFS bundle; the owner ZIP may instead retain their
# converted original RGB555A1 textures under SOURCE.
GALLERY_SPRITES = {
    "BtnArrow": (12, 18),
    "BtnMiiB": (54, 60),
    "BtnMiiLine": (54, 60),
    "BtnRoomEDITline": (32, 28),
    "BtnRoomEDITline01": (32, 28),
    "BtnScrollShadow": (16, 16),
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

    # Recover original gallery buttons from the same owner's ZIP without
    # inventing replacement artwork or requiring a second private download.
    # A complete already-packaged NitroFS set is also valid. A partial set
    # cannot silently build with missing original controls.
    available = [name for name in GALLERY_SPRITES
                 if (SOURCE + name + ".bclim.rgb555" in members or
                     "nitrofiles/art/Select/" + name + ".bin" in members)]
    if available and len(available) != len(GALLERY_SPRITES):
        raise ValueError("incomplete original Select gallery sprite set")
    for name, (width, height) in GALLERY_SPRITES.items():
        source = SOURCE + name + ".bclim.rgb555"
        target = "art/Select/" + name + ".bin"
        packed = "nitrofiles/" + target
        if source not in members:
            continue  # The original packed NitroFS sprite may be present.
        pixels = archive.read(source)
        if len(pixels) != 2 * width * height:
            raise ValueError("invalid converted original gallery sprite size: " + name)
        expected = struct.pack("<HH", width, height) + pixels
        if packed in members:
            if archive.read(packed) != expected:
                raise ValueError("prepacked original gallery sprite mismatch: " + name)
        else:
            result[target] = expected
    return result
