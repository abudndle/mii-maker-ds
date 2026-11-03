#!/usr/bin/env python3
"""Validate private 3DS pane measurements against a held-out scene fit.

All metadata, capture hashes and measured centers must come from a private,
authorized original runtime capture. A self-described capture is NOT
authentication: output remains runtime_anchor_verified=False until separate
original-runtime provenance review and DS visual/touch acceptance.
"""
import argparse
import hashlib
import json
import math
import re
from pathlib import Path

from calibrate_balloon_scene import calibrate

SHA256 = re.compile(r"[0-9a-f]{64}\Z")


def _hash(value, label):
    if not isinstance(value, str) or not SHA256.fullmatch(value):
        raise ValueError("invalid " + label)
    return value


def _point(value, label):
    if (not isinstance(value, list) or len(value) != 2 or
            any(isinstance(v, bool) or not isinstance(v, (int, float)) or
                not math.isfinite(v) for v in value)):
        raise ValueError("invalid " + label)
    x, y = value
    if not (0 <= x <= 256 and 0 <= y <= 192):
        raise ValueError(label + " outside DS bottom screen")
    return (float(x), float(y))


def validate(layout, evidence, tolerance=2.0):
    if not isinstance(layout, dict) or not isinstance(evidence, dict):
        raise ValueError("invalid evidence")
    if evidence.get("schema_version") != 1 or isinstance(evidence.get("schema_version"), bool):
        raise ValueError("unsupported evidence schema")
    source_hash = _hash(layout.get("source_sha256"), "layout source hash")
    if evidence.get("source_sha256") != source_hash:
        raise ValueError("evidence source hash mismatch")
    capture = evidence.get("capture")
    if not isinstance(capture, dict):
        raise ValueError("missing original runtime capture metadata")
    capture_hash = _hash(capture.get("sha256"), "capture SHA256")
    if (capture.get("screen") != "bottom" or
            capture.get("orientation") != "upright" or
            capture.get("coordinate_system") != "DS-bottom-top-left" or
            capture.get("width") != 256 or capture.get("height") != 192 or
            any(isinstance(capture.get(key), bool) for key in ("width", "height"))):
        raise ValueError("unsupported capture geometry or coordinate convention")
    # This is a provenance *record*, not cryptographic proof that the bytes
    # originated on real 3DS hardware. No field can authorize verification.
    provenance = evidence.get("provenance")
    if (not isinstance(provenance, dict) or
            provenance.get("kind") not in ("original-3ds-runtime", "synthetic") or
            not isinstance(provenance.get("capture_method"), str) or
            not provenance["capture_method"].strip() or
            len(provenance["capture_method"]) > 256):
        raise ValueError("incomplete or invalid capture provenance")
    fit_points, holdouts = evidence.get("fit_points"), evidence.get("holdout_points")
    if (not isinstance(fit_points, list) or not 5 <= len(fit_points) <= 64 or
            not isinstance(holdouts, list) or not 2 <= len(holdouts) <= 64):
        raise ValueError("at least five fit and two independent holdout points required")
    pane_map = {}
    for pane in layout.get("panes", []):
        if not isinstance(pane, dict) or not isinstance(pane.get("name"), str):
            raise ValueError("invalid source layout panes")
        pane_map.setdefault(pane["name"], []).append(pane)
    seen = set()
    def record(point, label):
        if not isinstance(point, dict) or not isinstance(point.get("pane"), str):
            raise ValueError("invalid " + label)
        name = point["pane"]
        if name in seen or len(pane_map.get(name, [])) != 1:
            raise ValueError("duplicate, missing or ambiguous " + label + " pane")
        seen.add(name)
        xy = _point(point.get("ds_center"), label + " center")
        bounds = pane_map[name][0].get("ds_bounds")
        if (not isinstance(bounds, list) or len(bounds) != 4 or
                any(isinstance(v, bool) or not isinstance(v, (int, float)) or
                    not math.isfinite(v) or abs(v) > 1_000_000 for v in bounds) or
                bounds[2] <= 0 or bounds[3] <= 0):
            raise ValueError("invalid source pane bounds")
        return name, (bounds[0] + bounds[2] / 2, bounds[1] + bounds[3] / 2), xy
    for p in fit_points:
        record(p, "fit")
    independent = [record(p, "holdout") for p in holdouts]
    if (not isinstance(tolerance, (int, float)) or isinstance(tolerance, bool) or
            not math.isfinite(tolerance) or not 0 < tolerance <= 10):
        raise ValueError("invalid tolerance")
    fit = calibrate(layout, {"source_sha256": source_hash, "points": fit_points}, tolerance)
    a, b, tx, c, d, ty = fit["scene_affine_ds"]
    errors = {}
    for name, (x, y), (u, v) in independent:
        err = math.hypot(a*x + b*y + tx-u, c*x + d*y + ty-v)
        if not math.isfinite(err) or err > tolerance:
            raise ValueError("independent holdout exceeds pixel tolerance")
        errors[name] = round(err, 5)
    determinant = a*d-b*c
    frobenius_sq = a*a+b*b+c*c+d*d
    discriminant = max(0.0, frobenius_sq*frobenius_sq-4*determinant*determinant)
    eigen_max = (frobenius_sq + math.sqrt(discriminant))/2
    condition = eigen_max/abs(determinant) if determinant else math.inf
    if not math.isfinite(condition) or condition > 16:
        raise ValueError("scene transform poorly conditioned")
    encoded = json.dumps(evidence, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()
    return {
        "schema_version": 1,
        "source_sha256": source_hash,
        "capture_sha256": capture_hash,
        "evidence_sha256": hashlib.sha256(encoded).hexdigest(),
        "scene_affine_ds": fit["scene_affine_ds"],
        "fit_point_count": len(fit_points),
        "holdout_point_count": len(holdouts),
        "fit_max_residual_px": fit["maximum_residual_px"],
        "fit_leave_one_out_max_residual_px": fit["holdout_max_residual_px"],
        "independent_holdout_errors_px": errors,
        "independent_holdout_max_residual_px": max(errors.values()),
        "determinant": round(determinant, 8),
        "condition_number": round(condition, 5),
        "capture_provenance_kind": provenance["kind"],
        "runtime_anchor_verified": False,
        "note": "Candidate only: metadata and synthetic fits cannot certify authentic 3DS source or runtime dispatch."
    }


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source_layout", type=Path)
    p.add_argument("private_evidence", type=Path)
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--max-error", type=float, default=2.0)
    args = p.parse_args()
    result = validate(json.loads(args.source_layout.read_text()),
                      json.loads(args.private_evidence.read_text()), args.max_error)
    args.output.write_text(json.dumps(result, indent=2, allow_nan=False) + "\n")
    print("PASS: independent holdouts consistent; original 3DS runtime anchor NOT verified")


if __name__ == "__main__":
    main()
