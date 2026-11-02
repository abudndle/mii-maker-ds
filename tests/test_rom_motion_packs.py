#!/usr/bin/env python3
"""Synthetic regression tests for original MSP1 animation-pack validation."""
import importlib.util
import math
import struct
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rom_motion_packs", ROOT / "tests/rom_motion_packs.py")
MOTION = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOTION)

def make_pack(prefix=b""):
    names = [b"Wait00", b"Wait01", b"Wait02", b"Wait03Pre", b"Wait03", b"Wait04"]
    names += [f"Clip{i:02d}".encode() for i in range(MOTION.EXPECTED_CLIPS-len(names))]
    start = 32 + MOTION.EXPECTED_CLIPS * 40
    frames = bytes(MOTION.FRAME_BYTES)
    out = bytearray(struct.pack("<4s7I", b"MSP1", 1, MOTION.EXPECTED_CLIPS, 18,
                                MOTION.FRAME_BYTES, 32, start + len(frames)*len(names), 0))
    for name in names:
        out += name + bytes(24-len(name))
        out += struct.pack("<4I", start, 1, 1, 30)
        start += len(frames)
    for _ in names:
        out += frames
    return bytearray(out)

class MotionPackTests(unittest.TestCase):
    def test_valid_pack_and_required_gallery_clips(self):
        pack = make_pack()
        self.assertEqual(MOTION.validate(pack, "fixture"), MOTION.EXPECTED_CLIPS)
        MOTION.ensure_gallery_clips(pack, "fixture")

    def test_bad_signature_and_header_rejected(self):
        pack = make_pack()
        pack[0:4] = b"BAD!"
        with self.assertRaisesRegex(ValueError, "signature"):
            MOTION.validate(pack, "fixture")
        pack = make_pack()
        struct.pack_into("<I", pack, 4, 2)
        with self.assertRaisesRegex(ValueError, "header mismatch"):
            MOTION.validate(pack, "fixture")

    def test_duplicate_clip_names_rejected(self):
        pack = make_pack()
        pack[32+40:32+64] = pack[32:56]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            MOTION.validate(pack, "fixture")

    def test_noncontiguous_clip_offsets_rejected(self):
        pack = make_pack()
        struct.pack_into("<I", pack, 32+24+4, 1)
        with self.assertRaisesRegex(ValueError, "directory entry"):
            MOTION.validate(pack, "fixture")

    def test_nan_head_matrix_rejected(self):
        pack = make_pack()
        data_start = 32 + MOTION.EXPECTED_CLIPS*40
        struct.pack_into("<f", pack, data_start, math.nan)
        with self.assertRaisesRegex(ValueError, "head matrix"):
            MOTION.validate(pack, "fixture")

    def test_out_of_range_bone_matrix_rejected(self):
        pack = make_pack()
        data_start = 32 + MOTION.EXPECTED_CLIPS*40
        struct.pack_into("<i", pack, data_start+48, 4097*65536)
        with self.assertRaisesRegex(ValueError, "bone matrix"):
            MOTION.validate(pack, "fixture")

    def test_trailing_bytes_rejected(self):
        pack = make_pack() + b"x"
        with self.assertRaisesRegex(ValueError, "trailing"):
            MOTION.validate(pack, "fixture")

    def test_missing_idle_clip_rejected(self):
        pack = make_pack()
        pack[32:56] = b"Other" + bytes(19)
        with self.assertRaisesRegex(ValueError, "missing gallery"):
            MOTION.ensure_gallery_clips(pack, "fixture")

    def test_male_female_catalog_timing_mismatch_rejected(self):
        male, female = make_pack(), make_pack()
        struct.pack_into("<I", female, 32+24+12, 60)
        with self.assertRaisesRegex(ValueError, "timing mismatch"):
            MOTION.compare_rig_catalogs(male, female)

    def test_different_clip_catalogs_rejected(self):
        male, female = make_pack(), make_pack()
        female[32:56] = b"Different" + bytes(15)
        with self.assertRaisesRegex(ValueError, "catalog mismatch"):
            MOTION.compare_rig_catalogs(male, female)

if __name__ == "__main__":
    unittest.main()
