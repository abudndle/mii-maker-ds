"""Asset-free regression checks for DSi camera purpose routing.

These source guards complement (but do not replace) BlocksDS compile and
physical DSi camera testing.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
CAMERA = (ROOT / "source" / "camera_ds.c").read_text()
HEADER = (ROOT / "source" / "camera_ds.h").read_text()
MAIN = (ROOT / "source" / "main.c").read_text()


class CameraRoutingTests(unittest.TestCase):
    def test_explicit_camera_purposes(self):
        self.assertIn("MDS_CAMERA_PHOTO_PREVIEW = 0", HEADER)
        self.assertIn("MDS_CAMERA_QR_SCAN = 1", HEADER)
        self.assertRegex(CAMERA, r"selected\s*=\s*purpose\s*==\s*MDS_CAMERA_QR_SCAN\s*\?\s*CAMERA_OUTER\s*:\s*CAMERA_INNER")

    def test_qr_scanner_uses_outward_camera(self):
        self.assertIn("camera_open=mds_camera_open_for(MDS_CAMERA_QR_SCAN)", MAIN)
        self.assertIn("camera_open=mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW)", MAIN)

    def test_qr_mode_cannot_switch_sensor(self):
        self.assertIn("if(!camera_qr&&(down&KEY_X))mds_camera_switch();", MAIN)
        self.assertRegex(CAMERA, r"if\s*\(!active\s*\|\|\s*camera_purpose\s*==\s*MDS_CAMERA_QR_SCAN\)\s*return 0")

    def test_dsi_gate_is_preserved(self):
        self.assertIn("if(!isDSiMode())", CAMERA)
        self.assertIn("if((down&KEY_X)&&isDSiMode())action=4;", MAIN)

    def test_compatibility_open_uses_photo_purpose(self):
        self.assertIn("mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW);", CAMERA)


if __name__ == "__main__":
    unittest.main()
