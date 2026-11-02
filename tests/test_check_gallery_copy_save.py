"""Asset-free regressions for persisted Mii Copy after emulator restart."""
import struct
import sys
import unittest
import zlib
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from check_gallery_copy_save import verify, IMPORT_BIT
from check_gallery_favorite_save import BODY_SIZE, FAVORITE_BIT, PERSONAL_BIT, RECORD_SIZE
from test_check_gallery_favorite_save import fixture, modified


def copied(before, source=1, dest=10, reset_flags=True, extra=None):
    after = bytearray(before)
    struct.pack_into("<I", after, 8, (struct.unpack_from("<I", after, 8)[0] + 1) & 0xffffffff)
    src = 24 + source * RECORD_SIZE
    dst = 24 + dest * RECORD_SIZE
    after[dst:dst + RECORD_SIZE] = before[src:src + RECORD_SIZE]
    if reset_flags:
        for bit in (FAVORITE_BIT, PERSONAL_BIT, IMPORT_BIT, IMPORT_BIT + 1):
            after[dst + 1 + bit // 8] &= ~(1 << (bit % 8))
    if extra is not None:
        after[extra] ^= 1
    struct.pack_into("<I", after, BODY_SIZE, zlib.crc32(after[:BODY_SIZE]))
    return bytes(after)


class CopySaveTests(unittest.TestCase):
    def setUp(self):
        self.before = modified(fixture())
        self.after = copied(self.before)

    def test_exact_copy_after_favorite(self):
        self.assertTrue(verify(self.before, self.after)["original_unchanged"])

    def test_missing_copy_rejected(self):
        with self.assertRaisesRegex(ValueError, "generation"):
            verify(self.before, self.before)

    def test_copy_wrong_slot_rejected(self):
        with self.assertRaisesRegex(ValueError, "unrelated"):
            verify(self.before, copied(self.before, dest=11))

    def test_copy_retains_favorite_rejected(self):
        with self.assertRaisesRegex(ValueError, "unrelated"):
            verify(self.before, copied(self.before, reset_flags=False))

    def test_other_mii_changed_rejected(self):
        with self.assertRaisesRegex(ValueError, "unrelated"):
            verify(self.before, copied(self.before, extra=24 + 2 * RECORD_SIZE + 37))

    def test_invalid_crc_rejected(self):
        damaged = bytearray(self.after)
        damaged[BODY_SIZE] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            verify(self.before, bytes(damaged))

    def test_wrong_source_rejected(self):
        with self.assertRaisesRegex(ValueError, "Personal"):
            verify(self.before, copied(self.before, source=0), source=0)

    def test_requires_favorite_baseline(self):
        with self.assertRaisesRegex(ValueError, "Favorite"):
            verify(fixture(), copied(fixture()))

    def test_occupied_destination_rejected(self):
        with self.assertRaisesRegex(ValueError, "occupied"):
            verify(self.before, self.after, destination=1)

    def test_generation_rollover(self):
        before = bytearray(self.before)
        struct.pack_into("<I", before, 8, 0xffffffff)
        struct.pack_into("<I", before, BODY_SIZE, zlib.crc32(before[:BODY_SIZE]))
        self.assertTrue(verify(bytes(before), copied(bytes(before)))["verified"])


if __name__ == "__main__":
    unittest.main()
