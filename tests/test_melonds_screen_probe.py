"""Synthetic-only emulator screenshot probes; no Nintendo images required."""
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from melonds_screen_probe import measure
class Tests(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        self.p=Path(t.name)/"screen.png"
    def test_distinct_pixels(self):
        image=Image.new("RGB",(256,384))
        image.putdata([((x*13+y*5)%256,(x*17+y*11)%256,(x+y*3)%256)
                       for y in range(384) for x in range(256)])
        image.save(self.p)
        self.assertGreater(measure(self.p)["sampled_unique_colors"],32)
    def test_black_screen_rejected(self):
        Image.new("RGB",(256,384)).save(self.p)
        with self.assertRaisesRegex(ValueError,"uniform"):measure(self.p)
    def test_too_small_rejected(self):
        Image.new("RGB",(16,16)).save(self.p)
        with self.assertRaisesRegex(ValueError,"small"):measure(self.p)
    def test_white_screen_rejected(self):
        Image.new("RGB",(400,800),"white").save(self.p)
        with self.assertRaisesRegex(ValueError,"uniform"):measure(self.p)
if __name__=="__main__":unittest.main()
