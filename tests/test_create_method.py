"""Portable selection and source-wiring checks for the create method menu."""
import ctypes
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class CreateMethodTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory()
        out=Path(cls.tmp.name)/"create.so"
        subprocess.run(["cc","-std=c11","-Wall","-Wextra","-Werror",
                        "-shared","-fPIC",str(ROOT/"source/create_method.c"),
                        "-o",str(out)],check=True)
        lib=ctypes.CDLL(str(out))
        cls.select=lib.mds_create_method_select
        cls.select.argtypes=[ctypes.c_int,ctypes.c_int]
        cls.select.restype=ctypes.c_int
        cls.touch=lib.mds_create_method_touch
        cls.touch.argtypes=[ctypes.c_int,ctypes.c_int,ctypes.c_int]
        cls.touch.restype=ctypes.c_int
    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()
    def test_ds_blocks_camera_and_retains_scratch(self):
        self.assertEqual(self.select(0,0),1)
        self.assertEqual(self.select(1,0),0)
        self.assertEqual(self.touch(100,140,0),0)
        self.assertEqual(self.touch(100,70,0),1)
    def test_dsi_opens_preview_only(self):
        self.assertEqual(self.select(1,1),2)
        self.assertEqual(self.touch(100,140,1),2)
    def test_boundaries_are_not_actions(self):
        for x,y in [(-1,60),(19,60),(236,60),(245,150),(25,105),(25,168)]:
            self.assertEqual(self.touch(x,y,1),0)
    def test_main_wiring_and_first_boot(self):
        main=(ROOT/"source/main.c").read_text()
        self.assertIn("screen=MDS_SCREEN_CREATE_METHOD;",main)
        self.assertIn("mds_create_method_input(create_input)",main)
        self.assertIn("create_result.selection",main)
        self.assertIn("create_result.choice",main)
        self.assertIn("mds_camera_open_for(MDS_CAMERA_PHOTO_PREVIEW)",main)
        self.assertIn("if(save_ready&&mds_gallery_empty(&gallery)&&",main)
        self.assertIn("screen=MDS_SCREEN_GENDER;",main)
        self.assertIn("Photo preview only. Face recognition unavailable.",main)
if __name__=="__main__":
    unittest.main()
