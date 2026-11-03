"""Compile and execute release-validated photo candidate touch gestures."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
class PhotoTouchReleaseTests(unittest.TestCase):
    def test_native_touch_gesture(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = Path(tmp) / "photo-touch"
            subprocess.run(
                [os.environ.get("CC", "cc"), "-std=c11", "-Wall", "-Wextra",
                 "-Werror", "-Isource", "tests/photo_touch_release_host.c",
                 "source/photo_candidate_input.c", "-o", str(exe)],
                cwd=ROOT, check=True, timeout=30)
            subprocess.run([str(exe)], cwd=ROOT, check=True, timeout=30)

    def test_editor_integration_is_release_only(self):
        source = (ROOT / "source/main.c").read_text()
        candidate = source.split(
            "}else if(screen==MDS_SCREEN_PHOTO_CANDIDATES){", 1)[1].split(
            "}else if(screen==MDS_SCREEN_GENDER){", 1)[0]
        self.assertIn("mds_photo_touch_begin(", candidate)
        self.assertIn("mds_photo_touch_hold(", candidate)
        self.assertIn("mds_photo_touch_release(", candidate)
        self.assertIn("input.up&KEY_TOUCH", candidate)
        self.assertNotIn("action=mds_photo_candidate_touch(", candidate)
        self.assertIn("mds_photo_touch_reset(", candidate)

if __name__=="__main__":
    unittest.main()
