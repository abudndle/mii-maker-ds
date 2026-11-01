#!/usr/bin/env python3
"""Fit a candidate DS-space SelectBalloonButton scene affine from runtime measurements.

Input must be an UNANCHORED private CLYT report from extract_balloon_layout.py
and independent measured pane centers from a runtime screenshot. This is a
calibration aid, not proof of the authentic scene placement. Never commit
private reports, measurements, screenshots, or derived resource archives.
"""
import argparse
import json
import math
from pathlib import Path


def _finite_pair(value, label):
    if (not isinstance(value, (list, tuple)) or len(value) != 2 or
            any(not isinstance(v, (int, float)) or isinstance(v, bool) or
                not math.isfinite(v) for v in value)):
        raise ValueError("invalid " + label)
    return tuple(float(v) for v in value)


def _solve3(rows, values):
    # Center/scale source points before solving to reduce normal-equation
    # conditioning issues for DS coordinates and subpixel measurements.
    mx = sum(p[0] for p in rows) / len(rows)
    my = sum(p[1] for p in rows) / len(rows)
    sx = max(1., max(abs(p[0] - mx) for p in rows))
    sy = max(1., max(abs(p[1] - my) for p in rows))
    normalized = [((x - mx) / sx, (y - my) / sy, 1.) for x, y in rows]
    augmented = [[sum(p[i] * p[j] for p in normalized) for j in range(3)] +
                 [sum(p[i] * value for p, value in zip(normalized, values))]
                 for i in range(3)]
    for column in range(3):
        pivot = max(range(column, 3), key=lambda row: abs(augmented[row][column]))
        if abs(augmented[pivot][column]) < 1e-9:
            raise ValueError("collinear or insufficiently separated calibration panes")
        augmented[column], augmented[pivot] = augmented[pivot], augmented[column]
        divisor = augmented[column][column]
        for j in range(column, 4):
            augmented[column][j] /= divisor
        for row in range(3):
            if row == column:
                continue
            factor = augmented[row][column]
            for j in range(column, 4):
                augmented[row][j] -= factor * augmented[column][j]
    a, b, center = (augmented[i][3] for i in range(3))
    a /= sx
    b /= sy
    return (a, b, center - a * mx - b * my)


def calibrate(layout, measurements, max_error=2.0):
    if (not isinstance(max_error, (int, float)) or isinstance(max_error, bool) or
            not math.isfinite(max_error) or not 0 < max_error <= 10):
        raise ValueError("invalid maximum residual")
    if (layout.get("runtime_anchor_verified") is not False or
            layout.get("external_scene_affine_ds") is not None or
            layout.get("external_offset_ds") != [0, 0]):
        raise ValueError("calibration requires an unanchored source layout report")
    source_hash = layout.get("source_sha256")
    if (not isinstance(source_hash, str) or len(source_hash) != 64 or
            any(c not in "0123456789abcdef" for c in source_hash) or
            measurements.get("source_sha256") != source_hash):
        raise ValueError("source layout hash missing or mismatched")
    panes = layout.get("panes")
    observations = measurements.get("points")
    if (not isinstance(panes, list) or not isinstance(observations, list) or
            not 4 <= len(observations) <= 64):
        raise ValueError("four to 64 independent pane measurements required")
    pane_map = {}
    for pane in panes:
        name = pane.get("name")
        if name in pane_map:
            raise ValueError("ambiguous source pane name")
        pane_map[name] = pane
    source, target, used = [], [], set()
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("invalid measurement entry")
        name = observation.get("pane")
        if not isinstance(name, str) or name in used or name not in pane_map:
            raise ValueError("duplicate or unknown measurement pane")
        used.add(name)
        x, y = _finite_pair(observation.get("ds_center"), "measured center")
        if not (0 <= x <= 256 and 0 <= y <= 192):
            raise ValueError("measured center outside DS screen")
        rect = pane_map[name].get("ds_bounds")
        if (not isinstance(rect, list) or len(rect) != 4 or
                any(not isinstance(v, (int, float)) or isinstance(v, bool) or
                    not math.isfinite(v) for v in rect) or
                rect[2] <= 0 or rect[3] <= 0):
            raise ValueError("invalid source pane bounds")
        source.append((rect[0] + rect[2] / 2, rect[1] + rect[3] / 2))
        target.append((x, y))
    a, b, tx = _solve3(source, [p[0] for p in target])
    c, d, ty = _solve3(source, [p[1] for p in target])
    determinant = a * d - b * c
    if (any(abs(v) > 16 for v in (a, b, c, d)) or
            any(abs(v) > 4096 for v in (tx, ty)) or
            not 0.0001 <= abs(determinant) <= 256):
        raise ValueError("invalid fitted scene affine")
    errors = [math.hypot(a * x + b * y + tx - u,
                         c * x + d * y + ty - v)
              for (x, y), (u, v) in zip(source, target)]
    if max(errors) > max_error:
        raise ValueError("runtime measurements disagree with one scene affine")
    return {"source_sha256": source_hash,
            "scene_affine_ds": [round(v, 8) for v in (a, b, tx, c, d, ty)],
            "pane_count": len(observations),
            "maximum_residual_px": round(max(errors), 5),
            "rms_residual_px": round(math.sqrt(sum(e * e for e in errors) /
                                               len(errors)), 5),
            "runtime_anchor_verified": False,
            "note": "A consistent affine is a hypothesis; verify against the actual 3DS scene and DS hitbox collisions before enabling gameplay."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout_report", type=Path)
    parser.add_argument("runtime_measurements", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-error", type=float, default=2.0)
    args = parser.parse_args()
    result = calibrate(json.loads(args.layout_report.read_text()),
                       json.loads(args.runtime_measurements.read_text()),
                       args.max_error)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS: scene affine candidate fitted; runtime anchor NOT verified")


if __name__ == "__main__":
    main()
