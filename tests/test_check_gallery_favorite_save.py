"""Synthetic, asset-free compact EEPROM Favorite persistence regressions."""
import struct
import subprocess
import tempfile
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_gallery_favorite_save import (BODY_SIZE, FAVORITE_BIT, PERSONAL_BIT,
                                         RECORD_SIZE, SAVE_SIZE, verify)


def fixture():
    data = bytearray(b"\xff" * SAVE_SIZE)
    data[:BODY_SIZE] = b"\x00" * BODY_SIZE
    data[:4] = b"MDSC"
    struct.pack_into("<III", data, 4, 2, 1, BODY_SIZE)
    for i in range(10):
        base = 24 + i * RECORD_SIZE
        data[base] = 1
        if i == 0:
            data[base + 1 + PERSONAL_BIT // 8] |= 1 << (PERSONAL_BIT % 8)
        data[base + 35:base + 35 + 8] = "Test".encode("utf-16le")
    struct.pack_into("<I", data, BODY_SIZE, zlib.crc32(data[:BODY_SIZE]))
    return bytes(data)


def modified(original, slot=1, enable=True, extra=None):
    data = bytearray(original)
    struct.pack_into("<I", data, 8, (struct.unpack_from("<I", data, 8)[0] + 1) & 0xffffffff)
    pos = 24 + slot * RECORD_SIZE + 1 + FAVORITE_BIT // 8
    if enable:
        data[pos] ^= 1 << (FAVORITE_BIT % 8)
    if extra is not None:
        data[extra] ^= 1
    struct.pack_into("<I", data, BODY_SIZE, zlib.crc32(data[:BODY_SIZE]))
    return bytes(data)


class FavoriteSaveTests(unittest.TestCase):
    def setUp(self):
        self.before = fixture()
        self.after = modified(self.before)

    def test_exact_favorite_transition(self):
        result = verify(self.before, self.after)
        self.assertTrue(result["unrelated_bytes_unchanged"])
        self.assertEqual(result["saved_miis"], 10)

    def test_real_c_codec_fixture_matches_bit_layout(self):
        # Cross-check offsets against the repository's actual C encoder,
        # not just this Python test's independently fabricated image.
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as temp:
            binary = Path(temp) / "fixture"
            save = Path(temp) / "gallery.sav"
            subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-I", str(root / "source"),
                            *[str(root / p) for p in (
                                "tools/make_gallery_fixture.c",
                                "source/save.c", "source/save_compact.c",
                                "source/avatar.c", "source/unicode.c")],
                            "-o", str(binary)], check=True, capture_output=True)
            subprocess.run([str(binary), str(save)], check=True, capture_output=True)
            baseline = save.read_bytes()
            self.assertTrue(verify(baseline, modified(baseline))["verified"])

    def test_no_change_rejected(self):
        with self.assertRaisesRegex(ValueError, "generation"):
            verify(self.before, self.before)

    def test_generation_only_rejected(self):
        with self.assertRaisesRegex(ValueError, "Favorite"):
            verify(self.before, modified(self.before, enable=False))

    def test_wrong_mii_rejected(self):
        with self.assertRaisesRegex(ValueError, "Favorite"):
            verify(self.before, modified(self.before, slot=2))

    def test_other_mii_corruption_even_with_valid_crc_rejected(self):
        with self.assertRaisesRegex(ValueError, "unrelated"):
            verify(self.before, modified(self.before, extra=24 + 2 * RECORD_SIZE + 36))

    def test_settings_mutation_even_with_valid_crc_rejected(self):
        with self.assertRaisesRegex(ValueError, "unrelated"):
            verify(self.before, modified(self.before, extra=16))

    def test_corrupted_crc_rejected(self):
        damaged = bytearray(self.after)
        damaged[BODY_SIZE] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            verify(self.before, bytes(damaged))

    def test_wrong_size_rejected(self):
        with self.assertRaisesRegex(ValueError, "8192"):
            verify(self.before, self.after[:-1])

    def test_personal_target_rejected(self):
        with self.assertRaisesRegex(ValueError, "Personal"):
            verify(self.before, modified(self.before, slot=0), slot=0)

    def test_wrong_occupancy_rejected(self):
        with self.assertRaisesRegex(ValueError, "saved Miis"):
            verify(self.before, self.after, expected_miis=9)

    def test_generation_rollover(self):
        before = bytearray(self.before)
        struct.pack_into("<I", before, 8, 0xffffffff)
        struct.pack_into("<I", before, BODY_SIZE, zlib.crc32(before[:BODY_SIZE]))
        self.assertTrue(verify(bytes(before), modified(bytes(before)))["verified"])


if __name__ == "__main__":
    unittest.main()
