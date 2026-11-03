"""Native menu arbitration: navigation never changes the A-confirmed method."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]

class CreateMethodAtomicTests(unittest.TestCase):
    def test_simultaneous_touch_and_physical_controls(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"create-method-atomic"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11","-Wall",
                            "-Wextra","-Werror","-Isource",
                            "tests/create_method_atomic_host.c",
                            "source/create_method.c","-o",str(exe)],
                           cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)

    def test_disabled_camera_and_invalid_touch_are_atomic(self):
        source=(ROOT/"source/create_method.c").read_text()
        decision=source.split("MdsCreateOutcome mds_create_method_input(",1)[1]
        self.assertIn("result.selection=input.dsi_enabled?(input.selection^1):0;",decision)
        touch=decision.split("if(input.touch){",1)[1].split("if(input.confirm){",1)[0]
        self.assertIn("return result;",touch)
        self.assertNotIn("if(result.choice!=MDS_CREATE_NONE)return result;",touch)

    def test_main_uses_single_input_decision_before_routing(self):
        main=(ROOT/"source/main.c").read_text()
        menu=main.split("}else if(screen==MDS_SCREEN_CREATE_METHOD){",1)[1].split(
            "}else if(screen==MDS_SCREEN_PHOTO_CANDIDATES){",1)[0]
        self.assertIn("mds_create_method_input(create_input)",menu)
        self.assertIn("MdsCreateChoice method=create_result.choice;",menu)
        self.assertIn("create_method_selection=create_result.selection;",menu)
        self.assertNotIn("create_method_selection^=1;",menu)
        self.assertIn("method==MDS_CREATE_BACK",menu)
        self.assertIn("method==MDS_CREATE_PHOTO_PREVIEW",menu)

if __name__=="__main__":
    unittest.main()
