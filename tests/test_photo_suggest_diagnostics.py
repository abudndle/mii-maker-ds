"""Typed photo suggestion failures; no draft or candidate mutation on rejection."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class PhotoSuggestDiagnosticsTests(unittest.TestCase):
    def test_native_rejection_reasons_and_success(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"photo-diagnostics"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11",
                            "-Wall","-Wextra","-Werror","-Isource",
                            "tests/photo_suggest_diagnostics_host.c",
                            "source/photo_suggest.c","source/photo_quality.c",
                            "source/face_hint.c","source/avatar.c",
                            "-o",str(exe)],cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)
    def test_camera_status_is_not_misleading(self):
        camera=(ROOT/"source/camera_ds.c").read_text()
        main=(ROOT/"source/main.c").read_text()
        self.assertIn('status="Photo ready. X suggest / A retake"',camera)
        self.assertIn("mds_camera_photo_suggestion_notice(suggestion);",main)
        self.assertIn("mds_photo_suggest_diagnose(",main)
        self.assertIn("Suggestion stage unavailable. B back",camera)
        self.assertIn("No framing cue. A retake",camera)
        self.assertNotIn("Photo captured. X framing",camera)
if __name__=="__main__":
    unittest.main()
