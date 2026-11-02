import tempfile
import unittest
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from private_rom_freshness import clear_old_rom, require_new_rom

class FreshnessTests(unittest.TestCase):
    def test_stale_output_removed_and_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mii-ds.nds"
            p.write_bytes(b"old")
            clear_old_rom(p)
            self.assertFalse(p.exists())
            with self.assertRaises(ValueError):
                require_new_rom(p)
            p.write_bytes(b"new")
            require_new_rom(p)

    def test_empty_output_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "mii-ds.nds"
            p.touch()
            with self.assertRaises(ValueError):
                require_new_rom(p)

    def test_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            target = Path(d) / "target"
            target.write_bytes(b"data")
            link = Path(d) / "mii-ds.nds"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                clear_old_rom(link)
            with self.assertRaises(ValueError):
                require_new_rom(link)
