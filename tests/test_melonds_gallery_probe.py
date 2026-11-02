"""Asset-free regression: emulator capture cannot pass when gallery input failed."""
import tempfile
import unittest
from pathlib import Path
import sys
from PIL import Image
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"tools"))
from melonds_gallery_probe import verify

class GalleryProbeTests(unittest.TestCase):
    def setUp(self):
        d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup)
        self.before=Path(d.name)/"before.png"
        self.after=Path(d.name)/"after.png"
        self.original=Image.new("RGB",(256,403),"white")
        self.original.save(self.before)
    def paint(self,actors=2,with_bottom=True):
        image=self.original.copy()
        from PIL import ImageDraw
        draw=ImageDraw.Draw(image)
        for local in range(actors):
            x=(21,64,107,150,194)[local%5]
            y=49 if local<5 else 97
            draw.rectangle((x+8,y+3+19,x+25,y+40+19),fill=(85+local*25,35,20))
        if with_bottom:draw.rectangle((5,210+30,250,210+165),fill=(45,155,99))
        image.save(self.after)
    def test_real_gallery_panes(self):
        self.paint(3)
        result=verify(self.before,self.after)
        self.assertEqual(result["changed_mii_pane_slots"][:3],[0,1,2])
    def test_identical_capture_fails(self):
        self.original.save(self.after)
        with self.assertRaisesRegex(ValueError,"identical"):verify(self.before,self.after)
    def test_single_actor_is_not_multi_mii_scene(self):
        self.paint(1)
        with self.assertRaisesRegex(ValueError,"independently rendered"):verify(self.before,self.after)
    def test_bottom_only_focus_is_not_gallery(self):
        self.paint(0)
        with self.assertRaisesRegex(ValueError,"proven gallery"):verify(self.before,self.after)
    def test_strict_native_width_accepts_native_capture(self):
        self.paint(2)
        result=verify(self.before,self.after,require_native_width=True)
        self.assertGreaterEqual(len(result["changed_mii_pane_slots"]),2)
    def test_strict_native_width_rejects_wide_capture(self):
        self.paint(2)
        for path in (self.before,self.after):
            with Image.open(path) as source:
                widened=Image.new("RGB",(300,403),"white")
                widened.paste(source,(0,0))
                widened.save(path)
        with self.assertRaisesRegex(ValueError,"not native DS width"):
            verify(self.before,self.after,require_native_width=True)
    def test_legacy_wide_capture_still_supported(self):
        self.paint(2)
        for path in (self.before,self.after):
            with Image.open(path) as source:
                widened=Image.new("RGB",(300,403),"white")
                widened.paste(source,(0,0))
                widened.save(path)
        result=verify(self.before,self.after)
        self.assertGreaterEqual(len(result["changed_mii_pane_slots"]),2)
    def test_window_resize_between_captures_is_rejected(self):
        self.paint(2)
        with Image.open(self.after) as source:
            resized=Image.new("RGB",(300,403),"white")
            resized.paste(source,(0,0))
            resized.save(self.after)
        with self.assertRaisesRegex(ValueError,"capture window geometry changed"):
            verify(self.before,self.after)
    def test_tiny_capture_rejected(self):
        Image.new("RGB",(16,16)).save(self.after)
        with self.assertRaisesRegex(ValueError,"smaller"):verify(self.before,self.after)

if __name__=="__main__":unittest.main()
