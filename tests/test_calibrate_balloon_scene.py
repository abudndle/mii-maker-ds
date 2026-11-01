#!/usr/bin/env python3
"""Synthetic scene anchor calibration regression; no Nintendo assets."""
import copy
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from calibrate_balloon_scene import calibrate

HASH = "a" * 64
positions = [(20, 20), (80, 20), (20, 80), (80, 80), (120, 110)]
layout = {"source_sha256": HASH, "runtime_anchor_verified": False,
          "external_scene_affine_ds": None, "external_offset_ds": [0, 0],
          "panes": [{"name": "Pane%d" % i,
                     "ds_bounds": [x - 5, y - 5, 10, 10]}
                    for i, (x, y) in enumerate(positions)]}
expected = (1.1, 0.1, 7, -0.05, 0.9, 8)
measurements = {"source_sha256": HASH, "points": [
    {"pane": "Pane%d" % i,
     "ds_center": [expected[0] * x + expected[1] * y + expected[2],
                   expected[3] * x + expected[4] * y + expected[5]]}
    for i, (x, y) in enumerate(positions)]}
result = calibrate(layout, measurements)
assert result["runtime_anchor_verified"] is False
assert result["pane_count"] == 5
assert result["maximum_residual_px"] == 0
assert all(abs(a - b) < 1e-6 for a, b in zip(result["scene_affine_ds"], expected))


def rejects(changed_layout, changed_measurements, fragment):
    try:
        calibrate(changed_layout, changed_measurements)
    except ValueError as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError("accepted " + fragment)


# Unmeasured duplicate CLYT names are harmless, but a measured duplicate
# must not silently select one of two source panes.
repeated = copy.deepcopy(layout)
repeated["panes"].extend([{"name": "Unused", "ds_bounds": [0, 0, 10, 10]}] * 2)
assert calibrate(repeated, measurements) == result
ambiguous = copy.deepcopy(layout)
ambiguous["panes"].append(copy.deepcopy(ambiguous["panes"][0]))
rejects(ambiguous, measurements, "ambiguous")
bad = copy.deepcopy(measurements)
bad["points"][4]["ds_center"][0] += 15
rejects(layout, bad, "disagree")
bad = copy.deepcopy(measurements)
bad["points"][4]["pane"] = "Pane0"
rejects(layout, bad, "duplicate")
bad = copy.deepcopy(measurements)
bad["source_sha256"] = "b" * 64
rejects(layout, bad, "mismatched")
bad = copy.deepcopy(layout)
bad["external_offset_ds"] = [3, 0]
rejects(bad, measurements, "unanchored")
bad = copy.deepcopy(layout)
bad["runtime_anchor_verified"] = True
rejects(bad, measurements, "unanchored")
bad = copy.deepcopy(layout)
for i, pane in enumerate(bad["panes"]):
    pane["ds_bounds"] = [i * 20, 20, 10, 10]
rejects(bad, measurements, "collinear")
bad = copy.deepcopy(measurements)
bad["points"][0]["ds_center"] = [math.inf, 0]
rejects(layout, bad, "measured center")
with tempfile.TemporaryDirectory() as temp:
    root = Path(temp)
    source = root / "layout.json"
    observed = root / "measured.json"
    output = root / "candidate.json"
    source.write_text(json.dumps(layout))
    observed.write_text(json.dumps(measurements))
    subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1] /
                                        "tools" / "calibrate_balloon_scene.py"),
                    str(source), str(observed), "--output", str(output)],
                   check=True, capture_output=True)
    assert json.loads(output.read_text()) == result
print("PASS: synthetic runtime scene affine fitting, mismatch rejection, degeneracy, and CLI")
