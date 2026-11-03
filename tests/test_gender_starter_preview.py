"""Test side-effect-free male/female default Mii preview and chooser wiring."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
class GenderStarterPreviewTests(unittest.TestCase):
    def test_compiled_presets_are_visual_only(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"preview"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11",
                            "-Wall","-Wextra","-Werror","-Isource",
                            "tests/gender_starter_preview_host.c",
                            "source/avatar.c","-o",str(exe)],
                           cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)
    def test_gender_screen_draws_selected_default_without_committing_it(self):
        main=(ROOT/"source/main.c").read_text()
        gender=main.split("}else if(screen==MDS_SCREEN_GENDER){",1)[1].split(
            "}else if(screen==MDS_SCREEN_PROFILE){",1)[0]
        self.assertIn("mds_creation_default(&editor.draft,(unsigned)chosen)",gender)
        self.assertIn("mds_profile_done(&profile,&editor.draft)",gender)
        self.assertIn("if(k&KEY_LEFT){mds_profile_choice_step(&profile,-1);drawn_screen=-1;}",gender)
        self.assertIn("if(k&KEY_RIGHT){mds_profile_choice_step(&profile,1);drawn_screen=-1;}",gender)
        self.assertIn("mds_creation_preview(&editor.draft,(unsigned)profile.choice,",main)
        self.assertIn("mds_ui_info(shown,editor.slot,45,",main)
        self.assertIn("const MdsAvatar *shown=&editor.draft;",main)
if __name__=="__main__":
    unittest.main()
