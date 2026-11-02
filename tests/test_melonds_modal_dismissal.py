"""Synthetic checks for fail-closed received-Mii modal dismissal."""
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_melonds_modal_dismissal import verify


class ModalDismissalTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.gallery = root / "gallery.png"
        self.modal = root / "modal.png"
        self.after = root / "after.png"
        Image.new("RGB", (256, 384), "black").save(self.gallery)
        img = Image.new("RGB", (256, 384), "black")
        for top, bottom in ((71, 103), (111, 143)):
            img.paste("white", (28, 192 + top, 228, 192 + bottom))
        img.save(self.modal)

    def test_real_dismissal_returns_both_panes_to_gallery(self):
        Image.new("RGB", (256, 384), "black").save(self.after)
        result = verify(self.gallery, self.modal, self.after)
        self.assertTrue(result["verified"])
        self.assertEqual(result["choice_panes"], 2)

    def test_unchanged_modal_is_not_a_dismissal(self):
        self.after.write_bytes(self.modal.read_bytes())
        with self.assertRaisesRegex(ValueError, "remains visible"):
            verify(self.gallery, self.modal, self.after)

    def test_button_press_highlight_is_not_a_dismissal(self):
        img = Image.open(self.modal).convert("RGB")
        img.paste("gray", (28, 192 + 71, 228, 192 + 77))
        img.save(self.after)
        with self.assertRaisesRegex(ValueError, "remains visible"):
            verify(self.gallery, self.modal, self.after)

    def test_one_button_cleared_but_other_stuck_is_rejected(self):
        img = Image.open(self.modal).convert("RGB")
        img.paste("black", (28, 192 + 71, 228, 192 + 103))
        img.save(self.after)
        with self.assertRaisesRegex(ValueError, "remains visible"):
            verify(self.gallery, self.modal, self.after)

    def test_unrelated_fullscreen_change_is_not_gallery_return(self):
        Image.new("RGB", (256, 384), "gray").save(self.after)
        with self.assertRaisesRegex(ValueError, "remains visible"):
            verify(self.gallery, self.modal, self.after)

    def test_incompatible_frame_rejected(self):
        Image.new("RGB", (256, 400), "black").save(self.after)
        with self.assertRaisesRegex(ValueError, "incompatible"):
            verify(self.gallery, self.modal, self.after)


if __name__ == "__main__":
    unittest.main()
