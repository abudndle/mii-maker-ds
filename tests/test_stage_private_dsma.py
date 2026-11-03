"""Synthetic regression coverage for the opt-in private DSMA NitroFS stage."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "stage_private_dsma", ROOT / "tools/stage_private_dsma.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


class PrivateDSMAStagingTests(unittest.TestCase):
    def test_public_tree_has_no_private_models(self):
        self.assertIn("/hardware3d/nitrofiles/", (ROOT / ".gitignore").read_text())
        source = (ROOT / "hardware3d/source/main.c").read_text()
        for filename in mod.NAMES:
            self.assertIn(filename, source)
        self.assertFalse((ROOT / "hardware3d/nitrofiles").exists())

    def test_stage_synthetic_files_into_ignored_tree(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model, anim = root / "synthetic.dsm", root / "synthetic.dsa"
            model.write_bytes(b"synthetic model")
            anim.write_bytes(b"synthetic animation")
            dest = root / "hardware3d/nitrofiles/models"
            with patch.object(mod, "ROOT", root):
                result = mod.stage(model, anim, dest)
                self.assertEqual([name for name, _ in result], list(mod.NAMES))
                self.assertEqual((dest / mod.NAMES[0]).read_bytes(), model.read_bytes())
                self.assertEqual((dest / mod.NAMES[1]).read_bytes(), anim.read_bytes())
                self.assertEqual(result[0][1], mod.digest(model.read_bytes()))
                self.assertEqual(result[1][1], mod.digest(anim.read_bytes()))
                model.write_bytes(b"updated synthetic")
                mod.stage(model, anim, dest)
                self.assertEqual((dest / mod.NAMES[0]).read_bytes(), model.read_bytes())
                self.assertFalse(list(dest.glob(".staging-*")))

    def test_reject_empty_oversize_escape_and_symlinks(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            model, anim = root / "synthetic.dsm", root / "synthetic.dsa"
            model.write_bytes(b"model")
            anim.write_bytes(b"anim")
            dest = root / "hardware3d/nitrofiles/models"
            with patch.object(mod, "ROOT", root):
                with self.assertRaises(ValueError):
                    mod.stage(model, anim, root / "public")
                model.write_bytes(b"")
                with self.assertRaises(ValueError):
                    mod.stage(model, anim, dest)
                model.write_bytes(b"model")
                with patch.object(mod, "MAX_BYTES", 3):
                    with self.assertRaises(ValueError):
                        mod.stage(model, anim, dest)
                alias = root / "alias"
                alias.symlink_to(model)
                with self.assertRaises(ValueError):
                    mod.stage(alias, anim, dest)
                dest.parent.mkdir(parents=True)
                dest.symlink_to(root, target_is_directory=True)
                with self.assertRaises(ValueError):
                    mod.stage(model, anim, dest)
            self.assertFalse((root / "public").exists())


if __name__ == "__main__":
    unittest.main()
