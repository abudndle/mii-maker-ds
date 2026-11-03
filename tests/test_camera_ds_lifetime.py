"""Host-compiled real DSi camera lifecycle and buffer cleanup regression."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest
ROOT=Path(__file__).resolve().parents[1]
class CameraDsLifetimeTests(unittest.TestCase):
    def test_mocked_dsi_sensor_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"camera-lifetime"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11","-Wall",
                            "-Wextra","-Werror","-Itests/camera_mock","-Isource",
                            "tests/camera_ds_mock_host.c","source/camera_ds.c",
                            "source/photo_quality.c","source/face_hint.c",
                            "-o",str(exe)],cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)
if __name__=="__main__":
    unittest.main()
