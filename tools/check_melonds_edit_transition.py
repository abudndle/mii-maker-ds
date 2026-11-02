#!/usr/bin/env python3
"""Require a real two-screen transition from gallery into the Mii editor.

This detects ignored Edit taps; it does not establish original 3DS visual
fidelity. Private screenshots remain on the trusted runner.
"""
import argparse
from pathlib import Path
from PIL import Image


def verify(gallery_path, editor_path, threshold=28):
    with Image.open(gallery_path) as a, Image.open(editor_path) as b:
        if a.size != b.size or a.width < 256 or a.height < 384:
            raise ValueError("incompatible or undersized melonDS captures")
        a = a.convert("RGB").crop((0, a.height - 384, 256, a.height))
        b = b.convert("RGB").crop((0, b.height - 384, 256, b.height))
    counts = [0, 0]
    pa, pb = a.load(), b.load()
    for y in range(384):
        for x in range(256):
            if max(abs(pa[x, y][c] - pb[x, y][c]) for c in range(3)) >= threshold:
                counts[y // 192] += 1
    if counts[0] < 200 or counts[1] < 350:
        raise ValueError("Edit did not visibly transition both screens: %r" % counts)
    return {"top_changed_pixels": counts[0], "bottom_changed_pixels": counts[1]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("gallery", type=Path)
    parser.add_argument("editor", type=Path)
    args = parser.parse_args()
    try:
        result = verify(args.gallery, args.editor)
    except (OSError, ValueError) as exc:
        parser.exit(1, "FAIL: Edit scene transition: %s\n" % exc)
    print("PASS: Edit changed both DS screens (%d top, %d bottom pixels)" %
          (result["top_changed_pixels"], result["bottom_changed_pixels"]))


if __name__ == "__main__":
    main()
