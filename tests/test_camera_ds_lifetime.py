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
    def test_scrubbing_survives_optimized_lto_build(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"camera-optimized"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11","-O3",
                            "-flto","-Wall","-Wextra","-Werror",
                            "-Itests/camera_mock","-Isource",
                            "tests/camera_ds_mock_host.c","source/camera_ds.c",
                            "source/photo_quality.c","source/face_hint.c",
                            "-o",str(exe)],cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)

    def test_preview_clears_old_image_if_frame_is_unavailable(self):
        code=(ROOT/"source/ui.c").read_text()
        start=code.index("void mds_ui_camera(const uint16_t *frame)")
        end=code.index("void mds_ui_restore_top(void)",start)
        body=code[start:end]
        self.assertIn("if(frame)memcpy(top,frame,256*192*2)",body)
        self.assertIn("memset(top,0,256*192*2)",body)
        camera=(ROOT/"source/camera_ds.c").read_text()
        self.assertIn("scrub_captured_frames();",camera)
        self.assertIn("volatile uint16_t *p=(volatile uint16_t *)pixels;",camera)
        self.assertNotIn("memset(display,0,sizeof display);",camera)
        self.assertNotIn("memset(frame,0,sizeof frame);",camera)

if __name__=="__main__":
    unittest.main()
