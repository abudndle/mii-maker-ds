"""Exercise the actual bounded RGB555 eye-pair geometry cue.

Synthetic contrast geometry does NOT demonstrate real-world face recognition.
"""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class AdaptiveEyePairTests(unittest.TestCase):
    def test_variable_positions_single_spot_and_horizontal_stripe(self):
        with tempfile.TemporaryDirectory() as td:
            binary=str(Path(td)/"eye-pair-host")
            subprocess.run([os.environ.get("CC","cc"),"-std=c11",
                            "-Wall","-Wextra","-Werror","-Isource",
                            "tests/eye_pair_host.c","source/face_hint.c",
                            "-o",binary],cwd=ROOT,check=True,timeout=30)
            subprocess.run([binary],cwd=ROOT,check=True,timeout=30)
    def test_integration_is_experimental_not_identity_detection(self):
        header=(ROOT/"source/face_hint.h").read_text()
        source=(ROOT/"source/photo_suggest.c").read_text()
        self.assertIn("NOT face detection",header)
        self.assertIn("mds_eye_pair_locate_rgb555",source)
        self.assertIn("value[13]",source)
        self.assertIn("value[14]",source)

if __name__=="__main__":
    unittest.main()
