#!/usr/bin/env python3
"""Synthetic regression coverage for the private build provenance tool."""
import hashlib
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from private_build_provenance import record

class ProvenanceTests(unittest.TestCase):
    def test_hashes_without_disclosing_content_or_paths(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            rom = root / "private-rom.nds"
            assets = root / "private-assets.zip"
            rom.write_bytes(b"synthetic ROM payload")
            assets.write_bytes(b"synthetic assets")
            result = record(rom, assets)
            self.assertEqual(result["rom_sha256"], hashlib.sha256(rom.read_bytes()).hexdigest())
            self.assertEqual(result["asset_zip_sha256"], hashlib.sha256(assets.read_bytes()).hexdigest())
            self.assertFalse(result["private_assets_included"])
            self.assertNotIn("synthetic", str(result))
            self.assertNotIn(str(root), str(result))
            assets.write_bytes(b"modified assets")
            self.assertNotEqual(result["asset_zip_sha256"], record(rom, assets)["asset_zip_sha256"])
            rom.write_bytes(b"")
            with self.assertRaises(ValueError):
                record(rom, assets)

if __name__ == "__main__":
    unittest.main()
