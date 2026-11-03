"""Compile and execute a portable RGB555 photo exposure regression suite."""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]


class PhotoQualityHostTests(unittest.TestCase):
    def test_portable_exposure_gate(self):
        with tempfile.TemporaryDirectory() as temp:
            binary = str(Path(temp) / "photo-quality-host")
            subprocess.run(
                ["cc", "-std=c11", "-Wall", "-Wextra", "-Werror",
                 "-Isource", "tests/photo_quality_host.c",
                 "source/photo_quality.c", "-o", binary],
                cwd=ROOT, check=True, timeout=30,
            )
            subprocess.run([binary], cwd=ROOT, check=True, timeout=30)


if __name__ == "__main__":
    unittest.main()
