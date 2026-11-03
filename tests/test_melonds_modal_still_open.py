"""Synthetic proof that received Yes retries cannot replay an accepted choice."""
import sys
import tempfile
import unittest
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_melonds_modal_still_open import verify


class ModalStillOpenTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        root = Path(self.temp.name)
        self.modal = root / "modal.png"
        self.after = root / "after.png"
        img = Image.new("RGB", (256, 384), "black")
        for top, bottom in ((71, 103), (111, 143)):
            img.paste("white", (28, 192 + top, 228, 192 + bottom))
        img.save(self.modal)

    def test_unchanged_modal_allows_retry(self):
        self.after.write_bytes(self.modal.read_bytes())
        self.assertTrue(verify(self.modal, self.after)["modal_still_open"])

    def test_small_button_highlight_allows_retry(self):
        img = Image.open(self.modal).convert("RGB")
        img.paste("gray", (28, 192 + 71, 228, 192 + 76))
        img.save(self.after)
        self.assertTrue(verify(self.modal, self.after)["modal_still_open"])

    def test_full_selection_highlight_in_one_pane_allows_retry(self):
        img = Image.open(self.modal).convert("RGB")
        # Simulate a substantial highlight repaint in the first pane while
        # the second original choice pane remains visibly present.
        img.paste("gray", (28, 192 + 71, 228, 192 + 103))
        img.save(self.after)
        self.assertTrue(verify(self.modal, self.after)["modal_still_open"])

    def test_dismissed_modal_blocks_retry(self):
        Image.new("RGB", (256, 384), "black").save(self.after)
        with self.assertRaisesRegex(ValueError,
                                    r"changed=12800, area=12800"):
            verify(self.modal, self.after)

    def test_one_replaced_choice_pane_blocks_retry(self):
        img = Image.open(self.modal).convert("RGB")
        img.paste("black", (28, 192 + 111, 228, 192 + 143))
        img.save(self.after)
        with self.assertRaisesRegex(ValueError, "no longer looks open"):
            verify(self.modal, self.after)

    def test_unrelated_screen_blocks_retry(self):
        Image.new("RGB", (256, 384), "gray").save(self.after)
        with self.assertRaisesRegex(ValueError, "no longer looks open"):
            verify(self.modal, self.after)

    def test_mismatched_frame_blocks_retry(self):
        Image.new("RGB", (256, 400), "black").save(self.after)
        with self.assertRaisesRegex(ValueError, "incompatible"):
            verify(self.modal, self.after)


if __name__ == "__main__":
    unittest.main()
