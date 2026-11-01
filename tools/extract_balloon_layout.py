#!/usr/bin/env python3
"""Inspect PRIVATE SelectBalloonButton.bclyt pane hierarchy without exporting art.

This recovers local CLYT affine transforms (including nested rotation and scale),
not the runtime placement of SelectBalloonButton within the full Select scene.
A separate scene anchor must be established before using bounds for DS input.
Never commit the generated report or original layout files.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import struct
from zipfile import ZipFile

PRIVATE_MEMBER = "assets/decoded/layout/Select.arc.files/blyt/SelectBalloonButton.bclyt"
PANE_TAGS = {b"pan1", b"pic1", b"bnd1", b"txt1", b"wnd1"}
REQUIRED = {"B_Favorite", "I_Favorite", "I_MyMii", "I_MiiCopy", "I_MiiOpen"}
MAX_SIZE = 16 * 1024 * 1024


def _read(fmt, data, offset):
    if offset < 0 or offset + struct.calcsize(fmt) > len(data):
        raise ValueError("truncated CLYT structure")
    return struct.unpack_from(fmt, data, offset)


def _matrix(x, y, sx, sy, degrees):
    angle = math.radians(degrees)
    c, s = math.cos(angle), math.sin(angle)
    return (c * sx, -s * sy, x, s * sx, c * sy, y)


def _compose(parent, local):
    a, b, tx, c, d, ty = parent
    e, f, ux, g, h, uy = local
    return (a*e+b*g, a*f+b*h, a*ux+b*uy+tx,
            c*e+d*g, c*f+d*h, c*ux+d*uy+ty)


def _rect(matrix, origin, width, height, canvas, offset):
    ox = (origin % 3) / 2
    oy = (origin // 3) / 2
    x0, x1 = -ox*width, (1-ox)*width
    y0, y1 = -oy*height, (1-oy)*height
    a, b, tx, c, d, ty = matrix
    points = []
    for x, y in ((x0, y0), (x1, y0), (x0, y1), (x1, y1)):
        px, py = a*x+b*y+tx, c*x+d*y+ty
        points.append(((px+canvas[0]/2)*256/canvas[0]+offset[0],
                       (canvas[1]/2-py)*192/canvas[1]+offset[1]))
    xs, ys = zip(*points)
    return [round(min(xs), 4), round(min(ys), 4),
            round(max(xs)-min(xs), 4), round(max(ys)-min(ys), 4)]


def extract(payload, offset=(0, 0)):
    if not isinstance(payload, bytes) or len(payload) < 20 or len(payload) > MAX_SIZE:
        raise ValueError("invalid CLYT size")
    if payload[:4] != b"CLYT" or _read("<H", payload, 4)[0] != 0xfeff:
        raise ValueError("invalid CLYT header or byte order")
    if _read("<H", payload, 6)[0] != 20 or _read("<I", payload, 12)[0] != len(payload):
        raise ValueError("invalid CLYT header size")
    count = _read("<H", payload, 16)[0]
    if count < 2 or count > 4096:
        raise ValueError("invalid CLYT section count")
    if len(offset) != 2 or any(not math.isfinite(v) or abs(v) > 4096 for v in offset):
        raise ValueError("invalid external scene offset")
    pos, sections = 20, []
    for _ in range(count):
        if pos + 8 > len(payload):
            raise ValueError("truncated CLYT section")
        size = _read("<I", payload, pos+4)[0]
        if size < 8 or pos + size > len(payload):
            raise ValueError("invalid CLYT section extent")
        sections.append(payload[pos:pos+size])
        pos += size
    if pos != len(payload):
        raise ValueError("trailing CLYT bytes")
    canvases = [s for s in sections if s[:4] == b"lyt1"]
    if len(canvases) != 1 or len(canvases[0]) < 20:
        raise ValueError("missing or ambiguous lyt1 canvas")
    canvas = _read("<ff", canvases[0], 12)
    if any(not math.isfinite(v) or not 1 <= v <= 4096 for v in canvas):
        raise ValueError("invalid source canvas")
    identity = (1., 0., 0., 0., 1., 0.)
    stack, last, panes = [], None, []
    for section in sections:
        tag = section[:4]
        if tag == b"pas1":
            if last is None:
                raise ValueError("orphan pane hierarchy start")
            stack.append(last)
            if len(stack) > 64:
                raise ValueError("excessive CLYT nesting")
        elif tag == b"pae1":
            if not stack:
                raise ValueError("unmatched pane hierarchy end")
            stack.pop()
        elif tag in PANE_TAGS:
            if len(section) < 76:
                raise ValueError("truncated pane transform")
            raw_name = section[12:28].split(b"\0", 1)[0]
            try:
                name = raw_name.decode("ascii")
            except UnicodeDecodeError as exc:
                raise ValueError("invalid pane name") from exc
            if not name:
                raise ValueError("unnamed CLYT pane")
            values = _read("<10f", section, 36)
            x, y, rotation, sx, sy, w, h = (values[0], values[1], values[5],
                                              values[6], values[7], values[8], values[9])
            if any(not math.isfinite(v) or abs(v) > 1e6 for v in (x, y, rotation, sx, sy, w, h)):
                raise ValueError("nonfinite or unreasonable pane transform")
            if w < 0 or h < 0 or abs(sx) > 1000 or abs(sy) > 1000:
                raise ValueError("invalid pane dimensions or scale")
            origin = section[9]
            if origin > 8:
                raise ValueError("invalid pane origin")
            parent = stack[-1] if stack else None
            matrix = _compose(parent["matrix"] if parent else identity,
                              _matrix(x, y, sx, sy, rotation))
            entry = {"name": name, "kind": tag.decode("ascii"),
                     "parent": parent["name"] if parent else None,
                     "ancestors": parent["ancestors"] + [parent["name"]] if parent else [],
                     "visible": bool(section[8] & 1) and (parent["visible"] if parent else True),
                     "alpha": (section[10] * parent["alpha"] // 255
                               if parent and (section[8] & 2) else section[10]),
                     "origin": origin, "local": [x, y, rotation, sx, sy, w, h],
                     "matrix": list(matrix), "ds_bounds": _rect(matrix, origin, w, h, canvas, offset)}
            panes.append(entry)
            last = entry
    if stack:
        raise ValueError("unclosed CLYT hierarchy")
    found = {name: [p for p in panes if p["name"] == name] for name in REQUIRED}
    missing = sorted(name for name, hits in found.items() if len(hits) != 1)
    if missing:
        raise ValueError("missing or ambiguous SelectBalloonButton panes: " + ", ".join(missing))
    return {"source_sha256": hashlib.sha256(payload).hexdigest(),
            "source_canvas": list(canvas), "target_canvas": [256, 192],
            "external_offset_ds": list(offset),
            "runtime_anchor_verified": False,
            "note": "CLYT-local geometry only; verify enclosing scene transform before using hitboxes.",
            "panes": panes}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_bclyt", type=Path,
                        help="private .bclyt or MiiMaker_DS_Resources.zip")
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--offset-x", type=float, default=0)
    parser.add_argument("--offset-y", type=float, default=0)
    args = parser.parse_args()
    if args.private_bclyt.suffix.lower() == ".zip":
        with ZipFile(args.private_bclyt) as archive:
            payload = archive.read(PRIVATE_MEMBER)
    else:
        payload = args.private_bclyt.read_bytes()
    result = extract(payload, (args.offset_x, args.offset_y))
    args.report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS: local SelectBalloonButton hierarchy inspected; runtime anchor NOT verified")


if __name__ == "__main__":
    main()
