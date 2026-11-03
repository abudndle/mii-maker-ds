"""BlocksDS/Maxmod audio integration is optional and menu-scoped."""
from pathlib import Path
import re
import unittest
ROOT=Path(__file__).resolve().parents[1]
class AudioIntegration(unittest.TestCase):
 def test_maxmod_and_optional_bank(self):
  mk=(ROOT/"Makefile").read_text()
  implementation=(ROOT/"source/audio_ds.c").read_text()
  self.assertIn("-lmm9",mk)
  self.assertIn("#include <maxmod9.h>",implementation)
  self.assertIn('fopen("nitro:/soundbank.bin","rb")',implementation)
  self.assertIn('if(!f)return 0;',implementation)
  self.assertIn('mmInitDefault("nitro:/soundbank.bin")',implementation)
  self.assertIn("mmLoadEffect(i)",implementation)
  self.assertIn("mmEffect((unsigned)event)",implementation)
  self.assertIn("if(!ready",implementation)
 def test_home_menu_hooks_only_after_arbitration(self):
  m=(ROOT/"source/main.c").read_text()
  self.assertIn('#include "audio_ds.h"',m)
  self.assertIn("mds_audio_init();",m)
  start=m.index("MdsHomeResult home_result=mds_home_input(home_input)")
  end=m.index("if(action==MDS_HOME_VIEW)",start)
  block=m[start:end]
  self.assertIn("mds_audio_play(MDS_AUDIO_MOVE)",block)
  self.assertIn("mds_audio_play(MDS_AUDIO_CANCEL)",block)
  self.assertIn("mds_audio_play(MDS_AUDIO_CONFIRM)",block)
  self.assertLess(block.index("MdsHomeResult home_result"),block.index("mds_audio_play"))
  self.assertEqual(block.count("mds_audio_play(MDS_AUDIO_CONFIRM)"),1)
 def test_audio_bank_not_checked_into_repo(self):
  ignore=(ROOT/".gitignore").read_text()
  self.assertIn("/nitrofiles/",ignore)
  hdr=(ROOT/"source/audio_ds.h").read_text()
  self.assertIn("MDS_AUDIO_EVENT_COUNT=3",hdr)
if __name__=="__main__":
 unittest.main()
