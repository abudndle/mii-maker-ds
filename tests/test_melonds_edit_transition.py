"""Asset-free regression tests for real Edit framebuffer transition gate."""
import tempfile
import unittest
from pathlib import Path
from PIL import Image
from tools.check_melonds_edit_transition import verify


class EditTransitionTests(unittest.TestCase):
    def test_detects_both_screens_and_rejects_ignored_touch(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "gallery.png"
            after = Path(tmp) / "editor.png"
            a = Image.new("RGB", (256, 384), (0, 0, 0))
            b = Image.new("RGB", (256, 384), (0, 0, 0))
            a.save(before)
            b.save(after)
            with self.assertRaises(ValueError):
                verify(before, after)
            for y in range(30, 80):
                for x in range(30, 90):
                    b.putpixel((x, y), (200, 100, 80))
            for y in range(220, 280):
                for x in range(30, 90):
                    b.putpixel((x, y), (200, 100, 80))
            b.save(after)
            self.assertGreater(verify(before, after)["top_changed_pixels"], 200)

    def test_rejects_one_screen_only_and_geometry_change(self):
        with tempfile.TemporaryDirectory() as tmp:
            before = Path(tmp) / "gallery.png"
            after = Path(tmp) / "editor.png"
            Image.new("RGB", (256, 384), (0, 0, 0)).save(before)
            Image.new("RGB", (256, 384), (255, 255, 255)).save(after)
            verify(before, after)
            one_screen = Image.new("RGB", (256, 384), (0, 0, 0))
            for y in range(192):
                for x in range(256):
                    one_screen.putpixel((x, y), (255, 255, 255))
            one_screen.save(after)
            with self.assertRaises(ValueError):
                verify(before, after)
            Image.new("RGB", (256, 384), (0, 0, 0)).save(after)
            with self.assertRaises(ValueError):
                verify(before, after)
            Image.new("RGB", (255, 384), (255, 255, 255)).save(after)
            with self.assertRaises(ValueError):
                verify(before, after)


if __name__ == "__main__":
    unittest.main()
