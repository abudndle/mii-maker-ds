#!/usr/bin/env python3
"""Require a received-Mii No response to return visually to the gallery.

Only compares private screenshots in memory. No original art, Mii data, or
frames are printed or uploaded. The source CLYT Yes/No pane bounds are used
to reject button hover/press animation as a completed modal dismissal.
"""
import argparse
from pathlib import Path
from PIL import Image

CHOICE_PANES = ((28, 71, 228, 103), (28, 111, 228, 143))


def verify(gallery_path, modal_path, after_path, threshold=28):
    with Image.open(gallery_path) as gallery, Image.open(modal_path) as modal, \
            Image.open(after_path) as after:
        if (gallery.size != modal.size or gallery.size != after.size or
                gallery.width < 256 or gallery.height < 384):
            raise ValueError("incompatible or undersized melonDS captures")
        origin = gallery.height - 192
        a = gallery.convert("RGB").crop((0, origin, 256, origin + 192))
        b = modal.convert("RGB").crop((0, origin, 256, origin + 192))
        c = after.convert("RGB").crop((0, origin, 256, origin + 192))
    ga, mb, ac = a.load(), b.load(), c.load()

    def changed(first, second, pane):
        x0, y0, x1, y1 = pane
        return sum(
            max(abs(first[x, y][channel] - second[x, y][channel])
                for channel in range(3)) >= threshold
            for y in range(y0, y1) for x in range(x0, x1)
        )

    counts = []
    for choice, pane in enumerate(CHOICE_PANES):
        appeared = changed(ga, mb, pane)
        dismissed = changed(mb, ac, pane)
        residual = changed(ga, ac, pane)
        # A mere press highlight can change hundreds of pixels without
        # dismissing the modal. Require substantial return toward gallery.
        if appeared < 64 or dismissed * 2 < appeared or residual >= dismissed:
            # Report aggregate pixel counts, never screenshots or source art.
            # These numbers distinguish an ignored tap from a changed pane
            # that did not actually return to the gallery.
            raise ValueError(
                "received confirmation remains visible after No touch "
                f"(choice={choice}, appeared={appeared}, "
                f"changed={dismissed}, residual={residual})")
        counts.append((appeared, dismissed, residual))
    return {"verified": True, "choice_panes": 2,
            "modal_changed_pixels": sum(v[0] for v in counts),
            "dismissed_changed_pixels": sum(v[1] for v in counts)}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("gallery", type=Path)
    p.add_argument("modal", type=Path)
    p.add_argument("after", type=Path)
    args = p.parse_args()
    try:
        result = verify(args.gallery, args.modal, args.after)
    except (OSError, ValueError) as exc:
        p.exit(1, "FAIL: received confirmation dismissal: %s\n" % exc)
    print("PASS: received confirmation dismissed across both original choice panes "
          "(%d changed pixels)" % result["dismissed_changed_pixels"])


if __name__ == "__main__":
    main()
