#!/usr/bin/env python3
"""Fail-closed proof of a *settled* received-Mii modal state.

Compare independent private melonDS captures. A single highlighted choice
pane or transition frame never authorizes another stylus touch. Only aggregate
pixel counts are reported; do not publish raw screenshots or game assets.
"""
import argparse
from pathlib import Path

from PIL import Image

from check_melonds_modal_dismissal import CHOICE_PANES, verify as dismissed
from check_melonds_modal_still_open import verify as still_open


def _drift(first_path, second_path, threshold=28):
    with Image.open(first_path) as first, Image.open(second_path) as second:
        if first.size != second.size or first.width < 256 or first.height < 384:
            raise ValueError("incompatible or undersized melonDS captures")
        origin = first.height - 192
        a = first.convert("RGB").crop((0, origin, 256, origin + 192)).load()
        b = second.convert("RGB").crop((0, origin, 256, origin + 192)).load()
        changed = 0
        total = 0
        for x0, y0, x1, y1 in CHOICE_PANES:
            for y in range(y0, y1):
                for x in range(x0, x1):
                    total += 1
                    if max(abs(a[x, y][c] - b[x, y][c]) for c in range(3)) >= threshold:
                        changed += 1
        return changed, total


def classify(gallery, modal, settled_a, settled_b, max_drift_percent=5):
    """Return 'dismissed' or 'open'; reject every ambiguous visual state.

    A stable *open* judgement is sufficient only to gate the existing
    byte-identical EEPROM check and bounded retry, not proof of original art.
    """
    if not isinstance(max_drift_percent, (int, float)) or isinstance(max_drift_percent, bool) or not 0 <= max_drift_percent <= 10:
        raise ValueError("invalid stability tolerance")
    drift, area = _drift(settled_a, settled_b)
    if drift * 100 > area * max_drift_percent:
        raise ValueError("received modal frames are still changing")
    returns = []
    remains = []
    for frame in (settled_a, settled_b):
        try:
            dismissed(gallery, modal, frame)
            returns.append(True)
        except ValueError:
            returns.append(False)
        try:
            still_open(modal, frame)
            remains.append(True)
        except ValueError:
            remains.append(False)
    if all(returns) and not any(remains):
        return "dismissed"
    if all(remains) and not any(returns):
        return "open"
    raise ValueError("received modal state is ambiguous across settled frames")


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("gallery", type=Path)
    p.add_argument("modal", type=Path)
    p.add_argument("settled_a", type=Path)
    p.add_argument("settled_b", type=Path)
    p.add_argument("--expect", required=True, choices=("dismissed", "open"))
    args = p.parse_args()
    try:
        state = classify(args.gallery, args.modal, args.settled_a, args.settled_b)
        if state != args.expect:
            raise ValueError("received modal is " + state + ", not " + args.expect)
    except (OSError, ValueError) as exc:
        p.exit(1, "FAIL: received modal settled-state proof: %s\n" % exc)
    print("PASS: received modal has two stable " + state + " frames; screenshot-only proof")


if __name__ == "__main__":
    main()
