"""Asset-free generator validation for original CLAN home selection track tables."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from generate_clan_home_visual import TRACKS,generate,q16

def fixture():
    tracks=[]
    for _,pane,kind,index,target in TRACKS:
        tracks.append({"pane":pane,"kind":kind,"index":index,"target":target,
                       "value_type":2,"keys":[[0.0,255.0,-255.0],[1.0,0.0,-255.0]]})
    return {"clips":[{"archive":"Plaza.arc.files","clip":"PlazaTop_Select",
                      "frames":6,"tracks":tracks}]}

class TestGenerator(unittest.TestCase):
    def test_nine_channels(self):
        source=generate(fixture())
        self.assertEqual(source.count("static const MdsClanKey"),9)
        self.assertIn("home_shadow[]",source)
    def test_missing_rejected(self):
        obj=fixture();obj["clips"][0]["tracks"].pop()
        with self.assertRaises(ValueError):generate(obj)
    def test_duplicate_rejected(self):
        obj=fixture()
        obj["clips"][0]["tracks"].append(copy.deepcopy(obj["clips"][0]["tracks"][0]))
        with self.assertRaises(ValueError):generate(obj)
    def test_clip_mismatch_rejected(self):
        obj=fixture();obj["clips"][0]["frames"]=99
        with self.assertRaises(ValueError):generate(obj)
    def test_invalid_numbers_rejected(self):
        for n in (float("nan"),float("inf"),1e10):
            with self.assertRaises(ValueError):q16(n)
    def test_key_interval_rejected(self):
        obj=fixture();obj["clips"][0]["tracks"][0]["keys"][-1][0]=2
        with self.assertRaises(ValueError):generate(obj)
if __name__=="__main__":unittest.main()
