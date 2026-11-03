#!/usr/bin/env python3
"""Verify the received-Mii choice modal remains open before a guarded retry.

This check only compares original confirmation choice-pane regions. It never
prints private screenshots or saved Mii data.
"""
import argparse
from pathlib import Path
from PIL import Image
from check_melonds_modal_dismissal import CHOICE_PANES


def verify(modal_path, after_path, threshold=28):
    with Image.open(modal_path) as modal, Image.open(after_path) as after:
        if modal.size != after.size or modal.width < 256 or modal.height < 384:
            raise ValueError("incompatible or undersized melonDS captures")
        origin = modal.height - 192
        a = modal.convert("RGB").crop((0, origin, 256, origin + 192))
        b = after.convert("RGB").crop((0, origin, 256, origin + 192))
    ma, ab = a.load(), b.load()
    changed_total = 0
    area_total = 0
    for x0, y0, x1, y1 in CHOICE_PANES:
        changed_total += sum(
            max(abs(ma[x, y][channel] - ab[x, y][channel])
                for channel in range(3)) >= threshold
            for y in range(y0, y1) for x in range(x0, x1)
        )
        area_total += (x1 - x0) * (y1 - y0)
    # Selecting the other choice may legitimately repaint one pane. Judge
    # both panes together: a single highlight transition is tolerated, while
    # a dismissed/replaced dialog changes most of the combined choice area.
    if changed_total * 100 >= area_total * 35:
        raise ValueError(
            "received confirmation no longer looks open "
            f"(changed={changed_total}, area={area_total})")
    return {"verified": True, "modal_still_open": True}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("modal", type=Path)
    p.add_argument("after", type=Path)
    args = p.parse_args()
    try:
        verify(args.modal, args.after)
    except (OSError, ValueError) as exc:
        p.exit(1, "FAIL: received choice retry guard: %s\n" % exc)
    print("PASS: received modal still visibly open; guarded choice retry permitted")


if __name__ == "__main__":
    main()
