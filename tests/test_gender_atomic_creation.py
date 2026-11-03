"""Creation gender choice must not confirm when B is pressed simultaneously."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
class GenderAtomicCreationTests(unittest.TestCase):
    def test_native_priority_and_mandatory_guard(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe=Path(tmp)/"gender-input"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11",
                            "-Wall","-Wextra","-Werror","-Isource",
                            "tests/gender_input_host.c","source/gender_input.c",
                            "-o",str(exe)],cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)

    def test_gender_selection_is_single_transaction(self):
        main=(ROOT/"source/main.c").read_text()
        gender=main.split("}else if(screen==MDS_SCREEN_GENDER){",1)[1].split(
            "}else if(screen==MDS_SCREEN_PROFILE){",1)[0]
        self.assertIn("mds_gender_action(",gender)
        self.assertIn("MDS_GENDER_CHOOSE",gender)
        self.assertIn("MDS_GENDER_MANDATORY",gender)
        self.assertIn("MDS_GENDER_BACK",gender)
        self.assertIn("mds_creation_default(&editor.draft,(unsigned)chosen)",gender)
        self.assertIn("mds_profile_done(&profile,&editor.draft)",gender)
        self.assertIn("else if(action==MDS_GENDER_BACK",gender)

    def test_personal_mii_baseline_tracks_crown_and_favorite(self):
        editor=(ROOT/"source/editor.c").read_text()
        create=editor.split("int mds_editor_create(",1)[1].split(
            "int mds_editor_move(",1)[0]
        self.assertIn("if(!personal){e->draft.value[51]=1;e->draft.value[46]=1;}",create)
        self.assertLess(create.index("if(!personal){"),create.index("e->baseline=e->draft;"))
        self.assertIn("e->baseline=e->draft;",create)

if __name__=="__main__":
    unittest.main()
