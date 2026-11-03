"""Native C regression for atomic first-boot / new-Mii gender actions."""
import os
import subprocess
import tempfile
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
class GenderInputTests(unittest.TestCase):
    def test_action_priority_native(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"gender-input"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11","-Wall",
                            "-Wextra","-Werror","-Isource",
                            "tests/gender_input_host.c","source/gender_input.c",
                            "-o",str(exe)],cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)
    def test_atomic_gender_screen_flow(self):
        main=(ROOT/"source/main.c").read_text()
        gender=main.split("}else if(screen==MDS_SCREEN_GENDER){",1)[1].split(
            "}else if(screen==MDS_SCREEN_PROFILE){",1)[0]
        self.assertIn("mds_gender_input(",gender)
        self.assertIn("MDS_GENDER_CANCEL",gender)
        self.assertIn("MDS_GENDER_MALE",gender)
        self.assertIn("MDS_GENDER_FEMALE",gender)
        self.assertIn("else if(action==MDS_GENDER_CANCEL)",gender)
        self.assertIn("mds_creation_default(&editor.draft,(unsigned)chosen)",gender)
        self.assertIn("mds_profile_done(&profile,&editor.draft)",gender)
        self.assertNotIn("if(down&KEY_B){",gender)
        self.assertNotIn("if(down&KEY_A)chosen=",gender)
if __name__=="__main__":
    unittest.main()
