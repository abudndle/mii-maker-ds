"""Check the separate original-source Nitro Engine/DSMA 3D port target."""
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
class Hardware3DPreview(unittest.TestCase):
 def test_uses_nitro_engine_dsma_not_software_or_replacement_models(self):
  source=(ROOT/"hardware3d/source/main.c").read_text()
  for api in ("#include <NEMain.h>","NE_Init3D()",
              "NE_ModelCreate(NE_Animated)",
              "NE_ModelLoadDSMFAT", "NE_AnimationLoadFAT",
              "NE_ModelSetAnimation","NE_ModelDraw",
              "NE_ProcessArg","NE_WaitForVBL"):
   self.assertIn(api,source)
  self.assertIn('nitro:/models/MiiBody_dsm.bin',source)
  self.assertIn('nitro:/models/MiiBody_dsa.bin',source)
  self.assertIn("consoleDemoInit()",source)
  self.assertNotIn("glBegin",source)
  self.assertNotIn("createCube",source)
 def test_separate_opt_in_build_does_not_break_main_renderer(self):
  make=(ROOT/"hardware3d/Makefile").read_text()
  game=(ROOT/"Makefile").read_text()
  self.assertIn("LIBS := -lNE -lnds9 -lm",make)
  self.assertIn("$(BLOCKSDSEXT)/nitro-engine",make)
  self.assertIn("NITROFSDIR := nitrofiles",make)
  self.assertNotIn("-lNE",game.split("LIBS :=",1)[1].split("\n",1)[0])
  self.assertIn("nitro-3d-preview:",game)
  self.assertIn("make -C hardware3d",game.replace("$(MAKE)","make"))
  ignore=(ROOT/".gitignore").read_text()
  self.assertIn("/hardware3d/nitrofiles/",ignore)
 def test_no_proprietary_data_in_public_hardware_preview(self):
  folder=ROOT/"hardware3d"
  self.assertFalse((folder/"nitrofiles").exists())
  self.assertFalse((folder/"source/3ds_model.h").exists())
if __name__=="__main__":unittest.main()
