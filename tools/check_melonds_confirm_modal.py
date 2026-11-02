#!/usr/bin/env python3
"""Require a visible lower-screen received-Mii confirmation transition.

This is a framebuffer transition gate, not a claim of original 3DS visual
parity. Screenshots stay private and are never printed.
"""
import argparse
from pathlib import Path
from PIL import Image


def verify(before_path, modal_path, threshold=28, minimum=350):
    with Image.open(before_path) as before, Image.open(modal_path) as modal:
        if before.size != modal.size or before.width < 256 or before.height < 384:
            raise ValueError("incompatible or undersized melonDS captures")
        box = (0, before.height - 192, 256, before.height)
        a = before.convert("RGB").crop(box)
        b = modal.convert("RGB").crop(box)
    pa, pb = a.load(), b.load()
    changed = sum(
        max(abs(pa[x, y][channel] - pb[x, y][channel])
            for channel in range(3)) >= threshold
        for y in range(192) for x in range(256)
    )
    if changed < minimum:
        raise ValueError("confirmation dialog did not visibly change bottom screen")
    return {"verified": True, "bottom_changed_pixels": changed}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("before", type=Path)
    p.add_argument("modal", type=Path)
    args = p.parse_args()
    try:
        result = verify(args.before, args.modal)
    except (OSError, ValueError) as exc:
        p.exit(1, "FAIL: received confirmation frame: %s\n" % exc)
    print("PASS: received confirmation changed %d bottom-screen pixels" %
          result["bottom_changed_pixels"])


if __name__ == "__main__":
    main()
