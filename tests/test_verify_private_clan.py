"""Asset-free CLAN source-table parity checks (no Nintendo files)."""
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from verify_private_clan import arrays, verify_tables, check, EXPECTED_CLIPS, EXPECTED_CHANNELS


class Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.source = Path(self.tmp.name)
        self.catalog = {"clip_count": EXPECTED_CLIPS, "channel_count": EXPECTED_CHANNELS}
        self.specs = tuple(
            (f"{i}.h", (lambda catalog, i=i:
             f"static const MdsClanKey k{i}[] = {{{{0,{i},0}},{{65536,{i+1},0}}}};"))
            for i in range(41)
        )
        for filename, generate in self.specs:
            (self.source / filename).write_text(generate(self.catalog), encoding="utf-8")

    def test_all_41_channels(self):
        report = verify_tables(self.catalog, self.source, self.specs)
        self.assertEqual(sum(v["channels"] for v in report.values()), 41)
        self.assertEqual(sum(v["keys"] for v in report.values()), 82)

    def test_formatting_does_not_change_parity(self):
        (self.source / "0.h").write_text(
            "static const MdsClanKey k0[]={{0, 0, 0}, {65536, 1, 0}};")
        verify_tables(self.catalog, self.source, self.specs)

    def test_wrong_key_rejected(self):
        path = self.source / "1.h"
        path.write_text(path.read_text().replace("65536,2,0", "65536,3,0"))
        with self.assertRaisesRegex(ValueError, "source CLAN keyframes differ"):
            verify_tables(self.catalog, self.source, self.specs)

    def test_missing_channel_rejected(self):
        (self.source / "0.h").write_text("static const MdsClanKey wrong[]={{0,0,0}};")
        with self.assertRaisesRegex(ValueError, "missing or unexpected"):
            verify_tables(self.catalog, self.source, self.specs)

    def test_extra_channel_rejected(self):
        path = self.source / "0.h"
        path.write_text(path.read_text() + "\nstatic const MdsClanKey extra[]={{0,0,0}};")
        with self.assertRaisesRegex(ValueError, "missing or unexpected"):
            verify_tables(self.catalog, self.source, self.specs)

    def test_duplicate_rejected(self):
        with self.assertRaisesRegex(ValueError, "duplicate CLAN table"):
            arrays("static const MdsClanKey x[]={{0,0,0}};" * 2)

    def test_malformed_initializer_rejected(self):
        for text in ("static const MdsClanKey x[]={{0,999,0},oops};",
                     "static const MdsClanKey x[]={};"):
            with self.subTest(text=text), self.assertRaises(ValueError):
                arrays(text)

    def test_changed_inventory_rejected(self):
        for name in ("clip_count", "channel_count"):
            catalog = dict(self.catalog)
            catalog[name] += 1
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "inventory differs"):
                verify_tables(catalog, self.source, self.specs)

    def test_invalid_catalog_blocks_read(self):
        with patch("verify_private_clan.inventory",
                   return_value={"clip_count": 0, "channel_count": 0}):
            with self.assertRaisesRegex(ValueError, "inventory differs"):
                check(self.source / "fictional.zip", self.source)


if __name__ == "__main__":
    unittest.main()
