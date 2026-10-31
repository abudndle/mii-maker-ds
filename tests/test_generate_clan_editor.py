"""Asset-free original editor CLAN metadata generator tests."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from generate_clan_editor import TRACKS,generate,q16
def fixture():
 clips=[]
 for name in ('EditorCommon_Select','EditHair_Select','EditFace_Select'):
  tracks=[]
  for array,clip,pane,kind,target in TRACKS:
   if clip!=name:continue
   if array=='editor_part_108':keys=[[0,1,0],[1,1.08,0],[2,1.08,0],[3,1,0]]
   elif array=='editor_part_110':keys=[[0,1,0],[1,1.10,0],[4,1.10,0],[5,1,0]]
   else:keys=[[0,18,0],[1,255,0]]
   tracks.append(dict(pane=pane,kind=kind,index=0,target=target,value_type=2,keys=keys))
  clips.append(dict(archive='Editor.arc.files',clip=name,frames=6,tracks=tracks))
 return {'clips':clips}
class Tests(unittest.TestCase):
 def test_eight_tracks(self):self.assertEqual(generate(fixture()).count('static const MdsClanKey'),8)
 def test_missing_track(self):
  d=fixture();d['clips'][0]['tracks'].pop()
  with self.assertRaises(ValueError):generate(d)
 def test_duplicate_track(self):
  d=fixture();d['clips'][0]['tracks'].append(copy.deepcopy(d['clips'][0]['tracks'][0]))
  with self.assertRaises(ValueError):generate(d)
 def test_wrong_frames(self):
  d=fixture();d['clips'][1]['frames']=20
  with self.assertRaises(ValueError):generate(d)
 def test_invalid_scale(self):
  d=fixture();d['clips'][1]['tracks'][0]['keys'][0][1]=2
  with self.assertRaises(ValueError):generate(d)
 def test_unsorted_frames(self):
  d=fixture();d['clips'][2]['tracks'][0]['keys'][1][0]=-1
  with self.assertRaises(ValueError):generate(d)
 def test_invalid_numeric(self):
  for n in (float('nan'),float('inf'),1e12):
   with self.assertRaises(ValueError):q16(n)
if __name__=='__main__':unittest.main()
