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


def _weak_axis_variance(points):
    """Rotation-invariant spread in the least-observed scene direction."""
    mx = sum(x for x, _ in points) / len(points)
    my = sum(y for _, y in points) / len(points)
    xx = sum((x - mx) ** 2 for x, _ in points) / len(points)
    yy = sum((y - my) ** 2 for _, y in points) / len(points)
    xy = sum((x - mx) * (y - my) for x, y in points) / len(points)
    major = (xx + yy + math.hypot(xx - yy, 2 * xy)) / 2
    return max(0.0, (xx * yy - xy * xy) / major) if major else 0.0


def calibrate(layout, measurements, max_error=2.0):
    if (not isinstance(layout, dict) or not isinstance(measurements, dict)):
        raise ValueError("invalid calibration inputs")
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
            not 5 <= len(observations) <= 64):
        raise ValueError("five to 64 independent pane measurements required for leave-one-out validation")
    pane_map = {}
    for pane in panes:
        if not isinstance(pane, dict) or not isinstance(pane.get("name"), str):
            raise ValueError("invalid source pane entry")
        pane_map.setdefault(pane["name"], []).append(pane)
    source, target, used = [], [], set()
    for observation in observations:
        if not isinstance(observation, dict):
            raise ValueError("invalid measurement entry")
        name = observation.get("pane")
        if not isinstance(name, str) or name in used or name not in pane_map:
            raise ValueError("duplicate or unknown measurement pane")
        used.add(name)
        if len(pane_map[name]) != 1:
            raise ValueError("ambiguous measured source pane")
        x, y = _finite_pair(observation.get("ds_center"), "measured center")
        if not (0 <= x <= 256 and 0 <= y <= 192):
            raise ValueError("measured center outside DS screen")
        rect = pane_map[name][0].get("ds_bounds")
        if (not isinstance(rect, list) or len(rect) != 4 or
                any(not isinstance(v, (int, float)) or isinstance(v, bool) or
                    not math.isfinite(v) for v in rect) or
                rect[2] <= 0 or rect[3] <= 0 or
                # Unanchored CLYT coordinates are screen-scale, not astronomical.
                # Huge but finite values overflow covariance/normal equations
                # and can silently produce NaN affine candidates.
                max(abs(rect[0]), abs(rect[1]), abs(rect[2]), abs(rect[3]),
                    abs(rect[0] + rect[2]), abs(rect[1] + rect[3])) > 1_000_000):
            raise ValueError("invalid source pane bounds")
        source.append((rect[0] + rect[2] / 2, rect[1] + rect[3] / 2))
        target.append((x, y))
    a, b, tx = _solve3(source, [p[0] for p in target])
    c, d, ty = _solve3(source, [p[1] for p in target])
    # A handful of tightly clustered pane centers can fit a perfect affine
    # but cannot constrain its placement elsewhere in the 3DS scene. Reject
    # poorly spread samples even when their residual happens to be zero.
    # The minor covariance eigenvalue measures spread in the weakest axis;
    # it is rotation-invariant, unlike separate X/Y range thresholds.
    if _weak_axis_variance(source) < 16.0:  # 4 source pixels RMS
        raise ValueError("calibration panes lack two-dimensional spread")
    # The inverse problem also matters: wide source anchors can be fitted
    # exactly onto a tiny cluster or near-line in the screenshot. Such a fit
    # cannot distinguish the authentic scene placement from a misannotated
    # or collapsed transform, even if residuals are exactly zero.
    if _weak_axis_variance(target) < 16.0:  # 4 DS pixels RMS
        raise ValueError("measured panes lack two-dimensional spread")
    determinant = a * d - b * c
    # Pane ds_bounds are already in screen coordinates (rightward X and
    # downward Y). A reflection, 180-degree flip or quarter-turn can fit
    # every screenshot point perfectly yet reverse the Favorite/Copy/Edit
    # touch order. A scene anchor is not allowed to reorient the DS screen.
    if a <= 0 or d <= 0 or determinant <= 0:
        raise ValueError("scene affine reverses screen orientation")
    # The external scene transform may include modest skew, but a candidate
    # whose horizontal position depends more on source Y (or vice versa)
    # cannot represent this screen-aligned gallery. This is a conservative
    # candidate preflight, not proof of authentic 3DS placement.
    if abs(b) > a * 0.5 or abs(c) > d * 0.5:
        raise ValueError("scene affine excessively skews gallery axes")
    if (any(abs(v) > 16 for v in (a, b, c, d)) or
            any(abs(v) > 4096 for v in (tx, ty)) or
            not 0.0001 <= abs(determinant) <= 256):
        raise ValueError("invalid fitted scene affine")
    errors = [math.hypot(a * x + b * y + tx - u,
                         c * x + d * y + ty - v)
              for (x, y), (u, v) in zip(source, target)]
    if max(errors) > max_error:
        raise ValueError("runtime measurements disagree with one scene affine")
    # A distant, high-leverage mismeasured pane can pull the least-squares
    # affine toward itself while leaving every in-sample residual below the
    # threshold. Independently predict each held-out pane from the others.
    # Require at least five independent panes so every emitted candidate
    # includes an actual leave-one-out check; never emit a four-point fit
    # with a null holdout metric.
    holdout_errors = []
        for omitted in range(len(source)):
            training_source = source[:omitted] + source[omitted + 1:]
            training_target = target[:omitted] + target[omitted + 1:]
            if (_weak_axis_variance(training_source) < 16.0 or
                    _weak_axis_variance(training_target) < 16.0):
                raise ValueError("leave-one-out panes lack two-dimensional spread")
            ha, hb, htx = _solve3(training_source, [p[0] for p in training_target])
            hc, hd, hty = _solve3(training_source, [p[1] for p in training_target])
            x, y = source[omitted]
            u, v = target[omitted]
            holdout_errors.append(math.hypot(ha * x + hb * y + htx - u,
                                             hc * x + hd * y + hty - v))
    holdout_max = max(holdout_errors)
    if not math.isfinite(holdout_max) or holdout_max > max_error:
        raise ValueError("runtime measurements fail leave-one-out consistency")
    return {"source_sha256": source_hash,
            "scene_affine_ds": [round(v, 8) for v in (a, b, tx, c, d, ty)],
            "pane_count": len(observations),
            "maximum_residual_px": round(max(errors), 5),
            "rms_residual_px": round(math.sqrt(sum(e * e for e in errors) /
                                               len(errors)), 5),
            "holdout_max_residual_px": round(holdout_max, 5),
            "runtime_anchor_verified": False,
            "note": "A consistent affine is a hypothesis; verify against the actual 3DS scene and DS hitbox collisions before enabling gameplay."}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("layout_report", type=Path)
    parser.add_argument("runtime_measurements", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--max-error", type=float, default=2.0)
    parser.add_argument("--check-gallery-controls", action="store_true",
                        help="reject fitted Favorite/Copy/Edit bounds overlapping DS controls")
    parser.add_argument("--menu-header", type=Path,
                        default=Path(__file__).resolve().parents[1] / "source/menu_generated.h")
    parser.add_argument("--menu-source", type=Path,
                        default=Path(__file__).resolve().parents[1] / "source/menu.c")
    args = parser.parse_args()
    layout = json.loads(args.layout_report.read_text())
    result = calibrate(layout, json.loads(args.runtime_measurements.read_text()),
                       args.max_error)
    if args.check_gallery_controls:
        from check_gallery_anchor import check
        # A passing preflight is NOT evidence of the original runtime anchor.
        check(layout, result, args.menu_header.read_text(), args.menu_source.read_text())
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("PASS: scene affine candidate fitted; runtime anchor NOT verified")


if __name__ == "__main__":
    main()
