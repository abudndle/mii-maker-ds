"""Execute portable, real-C photo candidate draft/rollback tests."""
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]

class PhotoCandidateHostTests(unittest.TestCase):
    def test_draft_transaction(self):
        with tempfile.TemporaryDirectory() as tmp:
            exe = str(Path(tmp) / "candidates")
            compiler = os.environ.get("CC", "cc")
            subprocess.run([
                compiler, "-std=c11", "-Wall", "-Wextra", "-Werror",
                "-Isource", "tests/photo_candidates_host.c",
                "source/photo_candidates.c", "source/avatar.c",
                "-o", exe,
            ], cwd=ROOT, check=True, timeout=30)
            subprocess.run([exe], cwd=ROOT, check=True, timeout=30)

if __name__ == "__main__":
    unittest.main()
