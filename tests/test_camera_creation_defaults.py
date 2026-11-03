"""Native C tests for different create-from-scratch defaults and camera keys."""
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]

class CameraCreationDefaults(unittest.TestCase):
    def test_male_female_presets_and_simultaneous_keys(self):
        with tempfile.TemporaryDirectory() as directory:
            exe=Path(directory)/"creation"
            subprocess.run([os.environ.get("CC","cc"),"-std=c11",
                            "-Wall","-Wextra","-Werror","-Isource",
                            "tests/camera_creation_defaults_host.c",
                            "source/avatar.c","source/camera_action.c",
                            "-o",str(exe)],
                           cwd=ROOT,check=True,timeout=30)
            subprocess.run([str(exe)],cwd=ROOT,check=True,timeout=30)
    def test_first_personal_mii_and_optional_creation_routes(self):
        main=(ROOT/"source/main.c").read_text()
        first=main.split("if(save_ready&&mds_gallery_empty(&gallery)&&",1)[1].split("int saved_selected",1)[0]
        chosen=main.split("}else if(screen==MDS_SCREEN_GENDER){",1)[1].split("}else if(screen==MDS_SCREEN_PROFILE){",1)[0]
        self.assertIn("mds_editor_create(&editor,0)",first)
        self.assertIn("mds_creation_default(&editor.draft,(unsigned)chosen);",chosen)
        self.assertIn("mds_profile_done(&profile,&editor.draft)",chosen)
        self.assertIn("screen=MDS_SCREEN_EDITOR;",chosen)
        self.assertIn("mds_camera_action((unsigned)down,camera_qr)",main)
        self.assertIn("MDS_CAMERA_ACTION_CAPTURE",main)
        self.assertIn("MDS_CAMERA_ACTION_SUGGEST",main)
        self.assertIn("MDS_CAMERA_ACTION_CLOSE",main)

if __name__=="__main__":
    unittest.main()
