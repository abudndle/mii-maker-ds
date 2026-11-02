"""Private-safe regressions for received Mii copy-before-edit EEPROM semantics."""
import struct
import subprocess
import sys
import tempfile
import unittest
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from check_gallery_received_copy_save import (
    verify_cancel, verify_copy, COPY_ALLOWED_BIT, IMPORT_BIT,
)
from check_gallery_favorite_save import (
    _bit, BODY_SIZE, FAVORITE_BIT, PERSONAL_BIT, RECORD_SIZE,
)
from test_check_gallery_favorite_save import fixture
from test_check_gallery_copy_save import copied


def with_received(before, source=1, status=1, permission=1):
    result = bytearray(before)
    base = 24 + source * RECORD_SIZE + 1
    for bit in (IMPORT_BIT, IMPORT_BIT + 1, COPY_ALLOWED_BIT):
        result[base + bit // 8] &= ~(1 << (bit % 8))
    for bit, value in ((IMPORT_BIT, status & 1),
                       (IMPORT_BIT + 1, (status >> 1) & 1),
                       (COPY_ALLOWED_BIT, permission)):
        result[base + bit // 8] |= value << (bit % 8)
    struct.pack_into("<I", result, BODY_SIZE, zlib.crc32(result[:BODY_SIZE]))
    return bytes(result)


class ReceivedCopySaveTests(unittest.TestCase):
    def setUp(self):
        self.before = with_received(fixture())
        self.after = copied(self.before)

    def test_cancel_is_exactly_unchanged(self):
        self.assertTrue(verify_cancel(self.before, self.before)["cancel_unchanged"])

    def test_received_copy_preserves_source_and_resets_status(self):
        result = verify_copy(self.before, self.after)
        self.assertTrue(result["source_unchanged"])
        self.assertEqual(result["new_slot"], 10)
        self.assertFalse(_bit(self.after, 10, IMPORT_BIT))
        self.assertFalse(_bit(self.after, 10, IMPORT_BIT + 1))
        self.assertTrue(_bit(self.after, 1, IMPORT_BIT))
        self.assertTrue(_bit(self.after, 10, COPY_ALLOWED_BIT))

    def test_c_encoder_fixture_and_roundtrip(self):
        sources = ("tools/make_gallery_fixture.c", "source/save.c",
                   "source/save_compact.c", "source/avatar.c", "source/unicode.c")
        with tempfile.TemporaryDirectory() as folder:
            binary = Path(folder) / "fixture"
            output = Path(folder) / "synthetic.sav"
            subprocess.run(["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                            "-I", str(ROOT / "source"),
                            *(str(ROOT / p) for p in sources),
                            "-o", str(binary)], check=True, capture_output=True)
            subprocess.run([str(binary), str(output), "--received"],
                           check=True, capture_output=True)
            before = output.read_bytes()
            self.assertEqual(len(before), 8192)
            self.assertTrue(_bit(before, 1, IMPORT_BIT))
            self.assertFalse(_bit(before, 1, IMPORT_BIT + 1))
            self.assertTrue(_bit(before, 1, COPY_ALLOWED_BIT))
            self.assertTrue(verify_cancel(before, before)["verified"])
            self.assertTrue(verify_copy(before, copied(before))["verified"])

    def test_cancel_rejects_any_mutation_even_valid_crc(self):
        with self.assertRaisesRegex(ValueError, "cancel changed"):
            verify_cancel(self.before, self.after)

    def test_copy_requires_received_source(self):
        with self.assertRaisesRegex(ValueError, "received"):
            verify_copy(fixture(), copied(fixture()))

    def test_copy_rejects_special_received_source(self):
        before = with_received(fixture(), status=3)
        with self.assertRaisesRegex(ValueError, "special"):
            verify_copy(before, copied(before))

    def test_copy_rejects_permission_denied(self):
        before = with_received(fixture(), permission=0)
        with self.assertRaisesRegex(ValueError, "permit"):
            verify_copy(before, copied(before))

    def test_copy_rejects_personal_source(self):
        with self.assertRaisesRegex(ValueError, "Personal"):
            verify_copy(self.before, self.after, source=0)

    def test_copy_rejects_source_mutation(self):
        changed = bytearray(self.after)
        changed[24 + RECORD_SIZE + 35] ^= 1
        struct.pack_into("<I", changed, BODY_SIZE, zlib.crc32(changed[:BODY_SIZE]))
        with self.assertRaisesRegex(ValueError, "original"):
            verify_copy(self.before, bytes(changed))

    def test_copy_rejects_unrelated_settings(self):
        changed = bytearray(self.after)
        changed[16] ^= 1
        struct.pack_into("<I", changed, BODY_SIZE, zlib.crc32(changed[:BODY_SIZE]))
        with self.assertRaisesRegex(ValueError, "unrelated"):
            verify_copy(self.before, bytes(changed))

    def test_copy_rejects_received_flag_retained(self):
        with self.assertRaisesRegex(ValueError, "EEPROM"):
            verify_copy(self.before, copied(self.before, reset_flags=False))

    def test_copy_rejects_wrong_destination(self):
        with self.assertRaisesRegex(ValueError, "EEPROM"):
            verify_copy(self.before, copied(self.before, dest=11))

    def test_copy_rejects_invalid_crc(self):
        bad = bytearray(self.after)
        bad[BODY_SIZE] ^= 1
        with self.assertRaisesRegex(ValueError, "CRC"):
            verify_copy(self.before, bytes(bad))

    def test_copy_rejects_generation_only(self):
        changed = bytearray(self.before)
        struct.pack_into("<I", changed, 8, 2)
        struct.pack_into("<I", changed, BODY_SIZE, zlib.crc32(changed[:BODY_SIZE]))
        with self.assertRaisesRegex(ValueError, "EEPROM"):
            verify_copy(self.before, bytes(changed))

    def test_generation_rollover(self):
        before = bytearray(self.before)
        struct.pack_into("<I", before, 8, 0xffffffff)
        struct.pack_into("<I", before, BODY_SIZE, zlib.crc32(before[:BODY_SIZE]))
        before = bytes(before)
        self.assertTrue(verify_copy(before, copied(before))["verified"])


if __name__ == "__main__":
    unittest.main()
