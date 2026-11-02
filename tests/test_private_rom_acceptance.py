import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from private_rom_acceptance import commands, ROOT


class AcceptanceTests(unittest.TestCase):
    def test_native_build(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "private.zip"
            result = commands(p)
            self.assertEqual(result, [[sys.executable, "tools/build_private.py", str(p.resolve()), "--no-cache"]])

    def test_docker_and_emulator(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "private.zip"
            result = commands(p, docker=True, emulator="/usr/bin/melonDS")
            self.assertEqual(result[0][1], "tools/build_private_docker.py")
            self.assertEqual(result[1], ["/usr/bin/melonDS", str(ROOT / "mii-ds.nds")])


if __name__ == "__main__":
    unittest.main()
