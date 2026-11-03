"""Real C regression for stylus motion sampled every VBlank, not only key edges."""
import os
import subprocess
import tempfile
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class PhotoTouchVBlankTests(unittest.TestCase):
    def test_held_path_and_release(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"photo-touch-vblank"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11","-Wall",
                            "-Wextra","-Werror","-Isource",
                            "tests/photo_touch_vblank_host.c",
                            "source/photo_candidate_input.c","-o",str(exe)],
                           cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)
    def test_producer_samples_even_without_queued_edge(self):
        main=(ROOT/"source/main.c").read_text()
        vblank=main.split("static void animation_vblank(void)",1)[1].split(
            "static MdsInput next_input(void)",1)[0]
        self.assertIn("mds_photo_touch_sample(",vblank)
        self.assertLess(vblank.index("mds_photo_touch_sample("),
                        vblank.index("if(!(event.down||event.repeat||event.up))return;"))
        self.assertIn("event.touch_stayed=mds_photo_touch_sample(",vblank)
        candidate=main.split("}else if(screen==MDS_SCREEN_PHOTO_CANDIDATES){",1)[1].split(
            "}else if(screen==MDS_SCREEN_GENDER){",1)[0]
        self.assertIn("input.touch_stayed",candidate)
        self.assertIn("mds_photo_touch_reset(&photo_touch)",candidate)
if __name__=="__main__":
    unittest.main()
