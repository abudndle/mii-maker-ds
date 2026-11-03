"""Compile and exercise the actual portable RGB555 photo-quality classifier."""
import ctypes
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "source" / "photo_quality.c"
WIDTH, HEIGHT = 256, 192
INVALID, DARK, BRIGHT, FLAT, USABLE = range(5)


def pixel(level):
    return level | (level << 5) | (level << 10)


class PhotoQualityTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory()
        binary = Path(cls.temp.name) / "photo_quality.so"
        compiler = os.environ.get("CC", "cc")
        subprocess.run([compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                        "-fPIC", "-shared", str(SRC), "-o", str(binary)], check=True)
        lib = ctypes.CDLL(str(binary))
        cls.classify = lib.mds_photo_quality
        cls.classify.argtypes = [ctypes.POINTER(ctypes.c_uint16),
                                 ctypes.c_uint, ctypes.c_uint]
        cls.classify.restype = ctypes.c_int

    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()

    def check_frame(self, sample):
        buf = (ctypes.c_uint16 * (WIDTH * HEIGHT))()
        for y in range(0, HEIGHT, 8):
            for x in range(0, WIDTH, 8):
                buf[y * WIDTH + x] = sample(x, y)
        return self.classify(buf, WIDTH, HEIGHT)

    def test_rejects_uninitialized_and_bad_dimensions(self):
        self.assertEqual(self.classify(None, WIDTH, HEIGHT), INVALID)
        buf = (ctypes.c_uint16 * 1)()
        self.assertEqual(self.classify(buf, 0, HEIGHT), INVALID)
        self.assertEqual(self.classify(buf, WIDTH, 999999), INVALID)

    def test_rejects_dark_even_with_contrast(self):
        self.assertEqual(self.check_frame(lambda x, y: pixel(0 if x < 128 else 7)), DARK)

    def test_rejects_overexposed_even_with_contrast(self):
        self.assertEqual(self.check_frame(lambda x, y: pixel(26 if x < 128 else 31)), BRIGHT)

    def test_rejects_uniform_midtones(self):
        self.assertEqual(self.check_frame(lambda x, y: pixel(15)), FLAT)

    def test_rejects_isolated_extremes_in_uniform_frame(self):
        # Two extreme pixels must not trick a flat portrait into passing.
        def image(x, y):
            if (x, y) == (0, 0):
                return pixel(0)
            if (x, y) == (8, 0):
                return pixel(31)
            return pixel(16)
        self.assertEqual(self.check_frame(image), FLAT)

    def test_rejects_sparse_noise_even_with_large_range(self):
        def image(x, y):
            return pixel(0 if (x + y) % 128 == 0 else 16)
        self.assertEqual(self.check_frame(image), FLAT)

    def test_accepts_well_exposed_contrast(self):
        self.assertEqual(self.check_frame(lambda x, y: pixel(9 if x < 128 else 23)), USABLE)

    def test_ignores_rgb555_alpha_bit(self):
        self.assertEqual(self.check_frame(lambda x, y: pixel(9 if x < 128 else 23) | 0x8000), USABLE)

    def test_no_face_detection_claim(self):
        header = (ROOT / "source" / "photo_quality.h").read_text()
        self.assertIn("does NOT detect a face", header)
        camera = (ROOT / "source" / "camera_ds.c").read_text()
        self.assertIn("mds_photo_quality(display,256u,192u)", camera)
        self.assertIn("Keep live preview", camera)


if __name__ == "__main__":
    unittest.main()
