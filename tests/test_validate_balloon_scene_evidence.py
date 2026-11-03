"""Synthetic-only independent 3DS scene measurements; no original assets."""
import copy
import hashlib
import json
import math
import struct
import subprocess
import zlib
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from validate_balloon_scene_evidence import validate, verify_capture_file

SHA = "a" * 64
CAPTURE_SHA = "b" * 64
POSITIONS = [(20, 20), (70, 20), (20, 70), (70, 70), (125, 100),
             (130, 35), (45, 120)]
AFFINE = (1, .04, 8, -.03, .9, 9)


def observed(x, y):
    a, b, tx, c, d, ty = AFFINE
    return [a*x + b*y + tx, c*x + d*y + ty]


def fixture():
    panes = [{"name": "P"+str(i), "ds_bounds": [x-5, y-5, 10, 10]}
             for i, (x, y) in enumerate(POSITIONS)]
    points = [{"pane": "P"+str(i), "ds_center": observed(x,y)}
              for i, (x,y) in enumerate(POSITIONS)]
    layout = {"source_sha256": SHA, "runtime_anchor_verified": False,
              "external_scene_affine_ds": None, "external_offset_ds": [0,0],
              "panes": panes}
    evidence = {
        "schema_version": 1, "source_sha256": SHA,
        "capture": {"sha256": CAPTURE_SHA, "screen": "bottom",
                    "orientation": "upright",
                    "coordinate_system": "DS-bottom-top-left",
                    "width": 256, "height": 192},
        "provenance": {"kind": "synthetic", "capture_method": "synthetic unittest only"},
        "fit_points": points[:5], "holdout_points": points[5:]}
    return layout, evidence


class IndependentHoldouts(unittest.TestCase):
    def setUp(self):
        self.layout, self.evidence = fixture()

    def fail_case(self, expected):
        with self.assertRaisesRegex(ValueError, expected):
            validate(self.layout, self.evidence)

    def test_exact_fit_independent_holdouts_and_hashes(self):
        result = validate(self.layout, self.evidence)
        self.assertEqual(result["fit_point_count"], 5)
        self.assertEqual(result["holdout_point_count"], 2)
        self.assertEqual(result["independent_holdout_max_residual_px"], 0)
        self.assertFalse(result["runtime_anchor_verified"])
        self.assertEqual(len(result["evidence_sha256"]), 64)
        self.assertEqual(result["capture_sha256"], CAPTURE_SHA)

    def test_false_original_claim_never_verifies(self):
        self.evidence["provenance"]["kind"] = "original-3ds-runtime"
        self.assertFalse(validate(self.layout, self.evidence)["runtime_anchor_verified"])

    def test_independent_holdout_outlier_rejected(self):
        self.evidence["holdout_points"][0]["ds_center"][0] += 6
        self.fail_case("independent holdout exceeds")

    def test_missing_or_duplicate_holdouts_rejected(self):
        self.evidence["holdout_points"] = self.evidence["holdout_points"][:1]
        self.fail_case("two independent")
        self.layout, self.evidence = fixture()
        self.evidence["holdout_points"][1]["pane"] = "P0"
        self.fail_case("duplicate")

    def test_capture_mismatch_and_orientation_rejected(self):
        self.evidence["capture"]["sha256"] = "invalid"
        self.fail_case("capture SHA256")
        self.layout, self.evidence = fixture()
        self.evidence["capture"]["orientation"] = "rotated"
        self.fail_case("capture geometry")

    def test_source_sha_and_metadata_required(self):
        self.evidence["source_sha256"] = "c"*64
        self.fail_case("source hash mismatch")
        self.layout, self.evidence = fixture()
        self.evidence["provenance"]["capture_method"] = ""
        self.fail_case("provenance")

    def test_nonfinite_holdout_and_tolerance_rejected(self):
        self.evidence["holdout_points"][1]["ds_center"][0] = float("nan")
        self.fail_case("invalid holdout center")
        self.layout, self.evidence = fixture()
        with self.assertRaisesRegex(ValueError, "invalid tolerance"):
            validate(self.layout, self.evidence, float("nan"))

    def test_fit_point_count_and_bad_source_rect_rejected(self):
        self.evidence["fit_points"] = self.evidence["fit_points"][:4]
        self.fail_case("five fit")
        self.layout, self.evidence = fixture()
        self.layout["panes"][6]["ds_bounds"][2] = -2
        self.fail_case("invalid source pane")

    def test_distinct_hash_for_changed_evidence(self):
        original = validate(self.layout, self.evidence)["evidence_sha256"]
        self.evidence["provenance"]["capture_method"] = "different synthetic procedure"
        self.assertNotEqual(original, validate(self.layout, self.evidence)["evidence_sha256"])

    def test_private_capture_png_bytes_required_and_bound(self):
        def chunk(kind, payload):
            content = kind + payload
            return (struct.pack(">I", len(payload)) + content +
                    struct.pack(">I", zlib.crc32(content) & 0xffffffff))
        def make_png(width=256, height=192):
            header = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
            raw = b"".join(b"\x00" + b"\0" * (width * 3) for _ in range(height))
            return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", header) +
                    chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            capture = root / "original-test-fixture.png"
            data = make_png()
            capture.write_bytes(data)
            sha = hashlib.sha256(data).hexdigest()
            self.assertEqual(verify_capture_file(capture, sha), sha)
            with self.assertRaisesRegex(ValueError, "SHA256 does not match"):
                verify_capture_file(capture, "b" * 64)
            capture.write_bytes(make_png(width=255))
            with self.assertRaisesRegex(ValueError, "dimensions mismatch"):
                verify_capture_file(capture, hashlib.sha256(capture.read_bytes()).hexdigest())
            broken = bytearray(data)
            broken[29] ^= 1
            capture.write_bytes(broken)
            with self.assertRaisesRegex(ValueError, "CRC mismatch"):
                verify_capture_file(capture, hashlib.sha256(broken).hexdigest())
            capture.write_bytes(b"not a PNG")
            with self.assertRaisesRegex(ValueError, "PNG size"):
                verify_capture_file(capture, sha)
            # The CLI will not write a result when capture bytes do not
            # correspond to the hash in the private measurement record.
            layout_path, evidence_path = root / "layout.json", root / "evidence.json"
            output = root / "report.json"
            layout_path.write_text(json.dumps(self.layout))
            self.evidence["capture"]["sha256"] = sha
            evidence_path.write_text(json.dumps(self.evidence))
            script = ROOT / "tools/validate_balloon_scene_evidence.py"
            command = [sys.executable, str(script), str(layout_path), str(evidence_path),
                       "--capture", str(capture), "--output", str(output)]
            bad = subprocess.run(command, capture_output=True)
            self.assertNotEqual(bad.returncode, 0)
            self.assertFalse(output.exists())
            capture.write_bytes(data)
            subprocess.run(command, capture_output=True, check=True)
            self.assertFalse(json.loads(output.read_text())["runtime_anchor_verified"])



if __name__ == "__main__":
    unittest.main()
