"""Portable C test and source-wiring checks for experimental photo variants.

This is not authentic 3DS photo-to-Mii recognition or real-face acceptance.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class PhotoSuggestTests(unittest.TestCase):
    def test_generated_variants_preserve_identity_and_reject_invalid_frames(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=str(Path(temp)/"photo-suggest")
            subprocess.run(
                [os.environ.get("CC","cc"),"-std=c11","-Wall","-Wextra",
                 "-Werror","-Isource","tests/photo_suggest_host.c",
                 "source/photo_suggest.c","source/photo_quality.c",
                 "source/face_hint.c","source/avatar.c","-o",exe],
                cwd=ROOT,check=True,timeout=30)
            subprocess.run([exe],cwd=ROOT,check=True,timeout=30)

    def test_candidate_screen_and_cam_wiring(self):
        main=(ROOT/"source/main.c").read_text()
        menu=(ROOT/"source/menu.h").read_text()
        self.assertIn("MDS_SCREEN_PHOTO_CANDIDATES",menu)
        self.assertIn("mds_photo_suggest_diagnose(",main)
        self.assertIn("mds_photo_candidates_begin(",main)
        self.assertIn("mds_photo_candidates_step(",main)
        self.assertIn("mds_photo_candidates_cancel(",main)
        self.assertIn("mds_photo_candidates_accept(",main)
        self.assertIn("Photo suggestions are experimental",main)
        self.assertIn("if(!camera_qr&&(down&KEY_X))",main)
        self.assertIn("mds_camera_photo_frozen()",main)

if __name__=="__main__":
    unittest.main()
