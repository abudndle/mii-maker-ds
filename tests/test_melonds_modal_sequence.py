"""Synthetic, asset-free settled modal proof. Never use private screenshots."""
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_melonds_modal_sequence import classify


class ModalSequenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.gallery, self.modal = root / "gallery.png", root / "modal.png"
        self.a, self.b = root / "a.png", root / "b.png"
        Image.new("RGB", (256, 384), "black").save(self.gallery)
        self.modal_img = Image.new("RGB", (256, 384), "black")
        for top, bottom in ((71, 103), (111, 143)):
            self.modal_img.paste("white", (28, 192 + top, 228, 192 + bottom))
        self.modal_img.save(self.modal)

    def test_two_stable_dismissed_frames(self):
        Image.new("RGB", (256, 384), "black").save(self.a)
        Image.new("RGB", (256, 384), "black").save(self.b)
        self.assertEqual(classify(self.gallery, self.modal, self.a, self.b), "dismissed")

    def test_two_stable_modal_frames(self):
        self.modal_img.save(self.a)
        self.modal_img.save(self.b)
        self.assertEqual(classify(self.gallery, self.modal, self.a, self.b), "open")

    def test_tiny_highlight_still_open(self):
        frame = self.modal_img.copy()
        frame.paste("gray", (28, 192 + 71, 228, 192 + 74))
        frame.save(self.a)
        frame.save(self.b)
        self.assertEqual(classify(self.gallery, self.modal, self.a, self.b), "open")

    def test_motion_between_frames_is_ambiguous(self):
        self.modal_img.save(self.a)
        Image.new("RGB", (256, 384), "black").save(self.b)
        with self.assertRaisesRegex(ValueError, "still changing"):
            classify(self.gallery, self.modal, self.a, self.b)

    def test_one_choice_pane_disappearing_is_ambiguous(self):
        frame = self.modal_img.copy()
        frame.paste("black", (28, 192 + 111, 228, 192 + 143))
        frame.save(self.a)
        frame.save(self.b)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            classify(self.gallery, self.modal, self.a, self.b)

    def test_single_stable_replacement_dialog_is_not_gallery(self):
        Image.new("RGB", (256, 384), "gray").save(self.a)
        Image.new("RGB", (256, 384), "gray").save(self.b)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            classify(self.gallery, self.modal, self.a, self.b)

    def test_mismatched_sizes_are_rejected(self):
        self.modal_img.save(self.a)
        Image.new("RGB", (256, 400), "black").save(self.b)
        with self.assertRaisesRegex(ValueError, "incompatible"):
            classify(self.gallery, self.modal, self.a, self.b)

    def test_bad_tolerance_rejected(self):
        self.modal_img.save(self.a)
        self.modal_img.save(self.b)
        for tolerance in (float("nan"), -1, 20, True):
            with self.assertRaisesRegex(ValueError, "invalid stability"):
                classify(self.gallery, self.modal, self.a, self.b, tolerance)


if __name__ == "__main__":
    unittest.main()
