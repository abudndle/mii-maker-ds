"""Asset-free original editor arrow/feature adjustment curve generator tests."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from generate_clan_adjust import TRACKS,generate,q16

def fixture():
 clips=[]
 for clip in ["EditEye_Decide","EditHair_Decide"]:
  tracks=[]
  for name,origin,pane,kind,target,count in TRACKS:
   if clip!=origin:continue
   if count==4:
    keys=[[0,0,0],[1,-3,0],[2,-3,0],[3,0,0]]
   elif count==3:
    keys=[[0,-3,0],[1,-3,0],[1,0,0]]
   else:keys=[[0,150,0]]
   tracks.append(dict(pane=pane,kind=kind,index=0,target=target,value_type=2,keys=keys))
  clips.append(dict(archive="Editor.arc.files",clip=clip,frames=6,tracks=tracks))
 return {"clips":clips}

class GeneratorTests(unittest.TestCase):
 def test_nine_tracks(self):
  data=generate(fixture())
  self.assertEqual(data.count("static const MdsClanKey"),9)
  self.assertIn("adjust_arrow_hair_y",data)
 def test_missing_source_clip(self):
  d=fixture();d["clips"].pop()
  with self.assertRaises(ValueError):generate(d)
 def test_duplicate_key_track(self):
  d=fixture();d["clips"][0]["tracks"].append(copy.deepcopy(d["clips"][0]["tracks"][0]))
  with self.assertRaises(ValueError):generate(d)
 def test_changed_clip_frames(self):
  d=fixture();d["clips"][1]["frames"]=3
  with self.assertRaises(ValueError):generate(d)
 def test_malformed_frame(self):
  d=fixture();d["clips"][0]["tracks"][0]["keys"][0][0]=5
  with self.assertRaises(ValueError):generate(d)
 def test_unsorted_keys(self):
  d=fixture();d["clips"][0]["tracks"][0]["keys"][2][0]=-5
  with self.assertRaises(ValueError):generate(d)
 def test_invalid_numerics(self):
  for value in [float("nan"),float("inf"),1e20]:
   with self.assertRaises(ValueError):q16(value)
if __name__=="__main__":unittest.main()
