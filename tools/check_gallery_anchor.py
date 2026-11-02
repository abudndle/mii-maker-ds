#!/usr/bin/env python3
"""Fail-closed collision preflight for a PRIVATE SelectBalloonButton scene fit.

This does not verify a runtime anchor or enable gameplay hitboxes. Keep
source layout reports, measurements, and screenshots outside public GitHub.
"""
import argparse
import json
import math
import re
from pathlib import Path

ACTIONS = ("B_Favorite", "I_MiiCopy", "I_MiiOpen")
# EDITSelectBase room arrows are handled separately in mds_gallery_room_arrow.
ARROWS = ((0., 59., 19., 72.), (237., 59., 19., 72.))


def _rectangles_from_header(header):
    """Read current generated room/slot hitboxes rather than duplicating them."""
    groups = []
    for name, expected in (("gallery_hits", 10), ("gallery_room_hits", 10)):
        match = re.search(r"static const MdsMenuHit\s+" + name +
                          r"\s*\[\]\s*=\s*\{(.*?)\};", header, re.S)
        if not match:
            raise ValueError("missing generated " + name)
        rows = re.findall(r"\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\}", match.group(1))
        if len(rows) != expected or re.sub(r"\{\s*-?\d+\s*,\s*-?\d+\s*,\s*\d+\s*,\s*\d+\s*,\s*\d+\s*\}\s*,?", "", match.group(1)).strip():
            raise ValueError("unexpected generated " + name)
        if sorted(int(row[4]) for row in rows) != list(range(expected)):
            raise ValueError("duplicate or missing generated " + name + " actions")
        rects = [tuple(map(float, row[:4])) for row in rows]
        if any(w <= 0 or h <= 0 for _, _, w, h in rects):
            raise ValueError("invalid generated " + name + " dimensions")
        groups.extend(rects)
    return groups + list(ARROWS)


def _overlap(a, b, tolerance=0.01):
    return (min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]) > tolerance and
            min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]) > tolerance)


def check(layout, candidate, header):
    """Return transformed action bounds only when they avoid existing controls."""
    if not isinstance(layout, dict) or not isinstance(candidate, dict):
        raise ValueError("invalid anchor inputs")
    sha = layout.get("source_sha256")
    if (not isinstance(sha, str) or not re.fullmatch(r"[0-9a-f]{64}", sha) or
            candidate.get("source_sha256") != sha):
        raise ValueError("mismatched source hash")
    if layout.get("runtime_anchor_verified") is not False or candidate.get("runtime_anchor_verified") is not False:
        raise ValueError("scene preflight cannot certify a runtime anchor")
    if layout.get("external_scene_affine_ds") is not None or layout.get("external_offset_ds") != [0, 0]:
        raise ValueError("expected unanchored source layout")
    affine = candidate.get("scene_affine_ds")
    if (not isinstance(affine, list) or len(affine) != 6 or
            any(not isinstance(v, (int, float)) or isinstance(v, bool) or
                not math.isfinite(v) for v in affine)):
        raise ValueError("invalid candidate affine")
    a, b, tx, c, d, ty = affine
    det = a * d - b * c
    if not 0.0001 <= abs(det) <= 256 or any(abs(v) > 16 for v in (a, b, c, d)):
        raise ValueError("degenerate candidate affine")
    panes = layout.get("panes")
    if not isinstance(panes, list):
        raise ValueError("missing source panes")
    protected = _rectangles_from_header(header)
    result = {}
    for name in ACTIONS:
        matching = [p for p in panes if isinstance(p, dict) and p.get("name") == name]
        if len(matching) != 1:
            raise ValueError("missing or ambiguous action pane: " + name)
        pane = matching[0]
        rect = pane.get("ds_bounds")
        if (not isinstance(rect, list) or len(rect) != 4 or
                any(not isinstance(v, (int, float)) or isinstance(v, bool) or
                    not math.isfinite(v) for v in rect) or
                rect[2] <= 0 or rect[3] <= 0):
            raise ValueError("invalid action bounds: " + name)
        x, y, w, h = rect
        corners = ((x, y), (x + w, y), (x, y + h), (x + w, y + h))
        points = [(a * px + b * py + tx, c * px + d * py + ty) for px, py in corners]
        xs, ys = zip(*points)
        transformed = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
        if (transformed[0] < -0.01 or transformed[1] < -0.01 or
                transformed[0] + transformed[2] > 256.01 or
                transformed[1] + transformed[3] > 192.01):
            raise ValueError("action outside DS screen: " + name)
        if any(_overlap(transformed, target) for target in protected):
            raise ValueError("action overlaps gallery controls: " + name)
        if any(_overlap(transformed, prior) for prior in result.values()):
            raise ValueError("action panes overlap: " + name)
        result[name] = transformed
    return {"source_sha256": sha, "runtime_anchor_verified": False,
            "action_bounds_ds": {k: [round(v, 4) for v in rect]
                                 for k, rect in result.items()},
            "note": "Collision-free candidate only; original runtime anchor unverified."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_layout", type=Path)
    parser.add_argument("candidate_fit", type=Path)
    parser.add_argument("--menu-header", type=Path,
                        default=Path(__file__).resolve().parents[1] / "source/menu_generated.h")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = check(json.loads(args.source_layout.read_text()),
                   json.loads(args.candidate_fit.read_text()),
                   args.menu_header.read_text())
    args.output.write_text(json.dumps(result, indent=2) + "\n")
    print("PASS: candidate action panes avoid existing gallery controls; anchor NOT verified")


if __name__ == "__main__":
    main()
