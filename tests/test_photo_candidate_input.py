"""Portable actual-C touch geometry plus camera retry source wiring."""
import ctypes
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class PhotoCandidateInputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        so=Path(cls.temp.name)/"candidate-input.so"
        subprocess.run([os.environ.get("CC","cc"),"-std=c11","-Wall","-Wextra","-Werror",
                        "-shared","-fPIC",str(ROOT/"source/photo_candidate_input.c"),
                        "-o",str(so)],check=True)
        lib=ctypes.CDLL(str(so))
        cls.touch=lib.mds_photo_candidate_touch
        cls.touch.argtypes=[ctypes.c_int,ctypes.c_int]
        cls.touch.restype=ctypes.c_int
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()
    def test_five_actions_and_edges(self):
        for x,expected in [(0,1),(47,1),(48,2),(95,2),(96,3),
                           (143,3),(144,4),(191,4),(192,5),(255,5)]:
            with self.subTest(x=x):
                self.assertEqual(self.touch(x,164),expected)
                self.assertEqual(self.touch(x,191),expected)
        for x,y in [(-1,175),(256,175),(20,163),(20,192),(48,-1),
                    (200,140),(400,400)]:
            self.assertEqual(self.touch(x,y),0)
    def test_retry_restores_draft_before_open(self):
        main=(ROOT/"source/main.c").read_text()
        part=main.split("}else if(screen==MDS_SCREEN_PHOTO_CANDIDATES){",1)[1].split("}else if(screen==MDS_SCREEN_GENDER){",1)[0]
        self.assertIn("mds_photo_touch_release(",part)
        self.assertIn("if(down&KEY_Y)",part)
        self.assertIn("mds_photo_candidates_cancel(&photo_candidates);",part)
        self.assertIn("screen=photo_return_screen;",part)
        self.assertIn("camera_open=mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW);",part)
        self.assertLess(part.index("mds_photo_candidates_cancel(&photo_candidates);",part.index("MDS_PHOTO_INPUT_RETRY")),part.index("camera_open=mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW);"))
        self.assertIn("mds_photo_candidates_accept(&photo_candidates)",part)
        self.assertIn("mds_photo_candidates_step(&photo_candidates",part)
    def test_selection_strip_drawn(self):
        ui=(ROOT/"source/ui.c").read_text()
        self.assertIn('label(146,173,"Retry")',ui)
        self.assertIn('label(195,173,"Back")',ui)
        self.assertIn('label(100,173,"Use")',ui)

if __name__=="__main__":
    unittest.main()
