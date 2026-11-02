"""Synthetic framebuffer tests for received-Mii confirmation acceptance."""
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_melonds_confirm_modal import verify


class ReceivedModalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.before = Path(self.temp.name) / "gallery.png"
        self.modal = Path(self.temp.name) / "modal.png"
        Image.new("RGB", (256, 384), "black").save(self.before)

    def test_real_lower_screen_transition(self):
        img = Image.new("RGB", (256, 384), "black")
        img.paste("white", (28, 192 + 71, 228, 192 + 143))
        img.save(self.modal)
        self.assertTrue(verify(self.before, self.modal)["verified"])

    def test_top_only_transition_is_not_a_modal(self):
        img = Image.new("RGB", (256, 384), "black")
        img.paste("white", (28, 20, 228, 120))
        img.save(self.modal)
        with self.assertRaisesRegex(ValueError, "bottom screen"):
            verify(self.before, self.modal)

    def test_unchanged_frame_rejected(self):
        Image.new("RGB", (256, 384), "black").save(self.modal)
        with self.assertRaisesRegex(ValueError, "bottom screen"):
            verify(self.before, self.modal)

    def test_tiny_cursor_change_rejected(self):
        img = Image.new("RGB", (256, 384), "black")
        img.paste("white", (80, 250, 85, 255))
        img.save(self.modal)
        with self.assertRaisesRegex(ValueError, "bottom screen"):
            verify(self.before, self.modal)

    def test_mismatched_frame_rejected(self):
        Image.new("RGB", (256, 400), "black").save(self.modal)
        with self.assertRaisesRegex(ValueError, "incompatible"):
            verify(self.before, self.modal)


if __name__ == "__main__":
    unittest.main()
