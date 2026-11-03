"""Run a real C synthetic eye-pair framing-cue regression.

This algorithm does not prove face detection on actual DSi photographs.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class FaceHintTests(unittest.TestCase):
    def test_portable_framing_cue(self):
        with tempfile.TemporaryDirectory() as temp:
            exe=str(Path(temp)/"face-hint-test")
            subprocess.run(
                [os.environ.get("CC","cc"),"-std=c11","-Wall","-Wextra",
                 "-Werror","-Isource","tests/face_hint_host.c",
                 "source/face_hint.c","-o",exe],
                check=True,cwd=ROOT,timeout=30)
            subprocess.run([exe],check=True,cwd=ROOT,timeout=30)

    def test_no_recognition_claim(self):
        hdr=(ROOT/"source/face_hint.h").read_text()
        self.assertIn("NOT face detection",hdr)
        self.assertIn("False positives and negatives",hdr)

if __name__=="__main__":
    unittest.main()
