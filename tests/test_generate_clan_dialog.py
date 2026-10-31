"""Asset-free regressions for three original DS dialog motion clips."""
import copy
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from generate_clan_dialog import generate,q16

def fixture():
    def clip(name,keys):
        return {"archive":"Dialog.arc.files","clip":name,"frames":21,
                "tracks":[{"pane":"W_Dialog","kind":"CLPA","index":0,
                           "target":1,"value_type":2,"keys":keys}]}
    return {"clips":[
        clip("DialogBase00_DialogIn",[[0,-240,0],[17,2,0],[20,0,-2/3]]),
        clip("DialogBase00_DialogOut",[[0,0,-14.117647171020508],[17,-240,0]]),
        clip("DialogBase00_DialogOutUp",[[0,0,0],[17,240,0]])]}

class DialogGeneratorTests(unittest.TestCase):
    def test_original_three_curves(self):
        result=generate(fixture())
        self.assertIn("dialog_in_y[]",result)
        self.assertIn("dialog_out_y[]",result)
        self.assertIn("dialog_out_up_y[]",result)
        self.assertIn("1114112,-15728640,0",result)
        self.assertIn("1114112,15728640,0",result)
        self.assertEqual(result.count("static const MdsClanKey"),3)
    def test_missing_track(self):
        source=fixture();source["clips"][0]["tracks"]=[]
        with self.assertRaises(ValueError):generate(source)
    def test_missing_exit_clip(self):
        source=fixture();source["clips"].pop()
        with self.assertRaises(ValueError):generate(source)
    def test_duplicate_track(self):
        source=fixture()
        source["clips"][1]["tracks"].append(copy.deepcopy(source["clips"][1]["tracks"][0]))
        with self.assertRaises(ValueError):generate(source)
    def test_wrong_clip_length(self):
        source=fixture();source["clips"][2]["frames"]=30
        with self.assertRaises(ValueError):generate(source)
    def test_bad_endpoint(self):
        source=fixture();source["clips"][1]["tracks"][0]["keys"][-1][1]=-80
        with self.assertRaises(ValueError):generate(source)
    def test_bad_frame_order(self):
        source=fixture();source["clips"][0]["tracks"][0]["keys"][1][0]=21
        with self.assertRaises(ValueError):generate(source)
    def test_invalid_floats(self):
        for value in [float("nan"),float("inf"),1e12]:
            with self.assertRaises(ValueError):q16(value)

if __name__=="__main__":unittest.main()
