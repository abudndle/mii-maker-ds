#!/usr/bin/env python3
"""Asset-free source anchor collision and fail-closed regression."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_gallery_anchor import check

SHA = "a" * 64
layout = {"source_sha256": SHA, "runtime_anchor_verified": False,
          "external_scene_affine_ds": None, "external_offset_ds": [0, 0],
          "panes": [{"name": name, "ds_bounds": [x, 169, 18, 18]}
                    for name, x in (("B_Favorite", 23),
                                    ("I_MiiCopy", 100),
                                    ("I_MiiOpen", 181))]}
fit = {"source_sha256": SHA, "runtime_anchor_verified": False,
       "scene_affine_ds": [1, 0, 0, 0, 1, 0]}
header = (ROOT / "source/menu_generated.h").read_text()
menu = (ROOT / "source/menu.c").read_text()
result = check(layout, fit, header, menu)
assert list(result["action_bounds_ds"]) == ["B_Favorite", "I_MiiCopy", "I_MiiOpen"]
assert result["runtime_anchor_verified"] is False


def reject(l, f, h, fragment):
    try:
        check(l, f, h, menu)
    except ValueError as exc:
        assert fragment in str(exc), (fragment, str(exc))
    else:
        raise AssertionError("accepted " + fragment)


bad = copy.deepcopy(layout)
bad["panes"][0]["ds_bounds"][1] = 135
reject(bad, fit, header, "overlaps gallery controls")
bad = copy.deepcopy(layout)
bad["panes"][1]["ds_bounds"][1] = 15
reject(bad, fit, header, "overlaps gallery controls")
bad = copy.deepcopy(layout)
bad["panes"][0]["ds_bounds"] = [0, 100, 18, 18]
reject(bad, fit, header, "overlaps gallery controls")
bad = copy.deepcopy(layout)
bad["panes"][0]["ds_bounds"] = [245, 169, 18, 18]
reject(bad, fit, header, "outside DS screen")
bad = copy.deepcopy(layout)
bad["panes"][2]["ds_bounds"] = [102, 169, 18, 18]
reject(bad, fit, header, "action panes overlap")
bad = copy.deepcopy(layout)
bad["panes"].append(copy.deepcopy(bad["panes"][0]))
reject(bad, fit, header, "ambiguous")
bad = copy.deepcopy(fit)
bad["source_sha256"] = "b" * 64
reject(layout, bad, header, "mismatched")
bad = copy.deepcopy(fit)
bad["runtime_anchor_verified"] = True
reject(layout, bad, header, "cannot certify")
bad = copy.deepcopy(fit)
bad["scene_affine_ds"] = [1, 0, 0, 0, 0, 0]
reject(layout, bad, header, "degenerate")
bad = copy.deepcopy(fit)
bad["scene_affine_ds"] = [1, 0, float("nan"), 0, 1, 0]
reject(layout, bad, header, "invalid candidate")
reject(layout, fit, header.replace("gallery_room_hits", "missing_room_hits"), "missing generated")
try:
    check(layout, fit, header, menu.replace("x<19", "x<20"))
except ValueError as exc:
    assert "room arrow source bounds changed" in str(exc)
else:
    raise AssertionError("accepted stale room-arrow collision bounds")
with tempfile.TemporaryDirectory() as tmp:
    temp = Path(tmp)
    source, candidate, output = (temp / n for n in ("layout.json", "fit.json", "checked.json"))
    source.write_text(json.dumps(layout))
    candidate.write_text(json.dumps(fit))
    subprocess.run([sys.executable, str(ROOT / "tools/check_gallery_anchor.py"),
                    str(source), str(candidate), "--output", str(output)],
                   check=True, capture_output=True)
    assert json.loads(output.read_text()) == result
print("PASS: synthetic scene action bounds, overlap, screen clipping, hash and CLI")
