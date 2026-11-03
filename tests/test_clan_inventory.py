"""Asset-free tests for the private BCLAN metadata validator."""
import io
import struct
import sys
import unittest
import zipfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from clan_inventory import inventory, parse_clan

def fixture(endian="<"):
    section = b"pai1" + struct.pack(endian + "I", 8)
    marker = b"\xff\xfe" if endian == "<" else b"\xfe\xff"
    return b"CLAN" + marker + struct.pack(
        endian + "HIIHH", 20, 0x2020000, 20 + len(section), 1, 0
    ) + section

class TestClanInventory(unittest.TestCase):
    def test_little_endian(self):
        self.assertEqual(parse_clan(fixture())["sections"], ["pai1"])

    def test_big_endian(self):
        self.assertEqual(parse_clan(fixture(">"))["sections"], ["pai1"])

    def test_corrupted_section_bounds(self):
        data = bytearray(fixture())
        data[24:28] = struct.pack("<I", 999)
        with self.assertRaises(ValueError):
            parse_clan(data)

    def test_trailing_payload_rejected(self):
        with self.assertRaises(ValueError):
            parse_clan(fixture() + b"xx")

    def test_inventory_from_zip(self):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr(
                "assets/decoded/layout/Test.arc.files/anim/Intro.bclan",
                fixture(),
            )
        stream.seek(0)
        report = inventory(stream)
        self.assertEqual(report["count"], 1)
        self.assertEqual(report["archives"], {"Test.arc.files": 1})

    def test_missing_animation_section(self):
        with self.assertRaises(ValueError):
            parse_clan(fixture().replace(b"pai1", b"pat1"))

if __name__ == "__main__":
    unittest.main()
