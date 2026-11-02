import hashlib
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from private_rom_acceptance import commands, make_report, ROOT


class AcceptanceTests(unittest.TestCase):
    def test_evidence_hashes_and_unverified_gameplay(self):
        with tempfile.TemporaryDirectory() as d:
            rom, archive = Path(d) / "rom.nds", Path(d) / "private.zip"
            rom.write_bytes(b"synthetic rom")
            archive.write_bytes(b"synthetic resources")
            report = make_report(rom, archive, emulator_launched=True)
            self.assertEqual(report["private_rom_sha256"], hashlib.sha256(rom.read_bytes()).hexdigest())
            self.assertEqual(report["archive_sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual(report["private_rom_bytes"], len(b"synthetic rom"))
            self.assertTrue(report["emulator_launched"])
            self.assertFalse(report["gameplay_verified"])

    def test_missing_rom_evidence_fails(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "missing.nds"
            archive = Path(d) / "archive.zip"
            archive.write_bytes(b"fixture")
            with self.assertRaises(FileNotFoundError):
                make_report(missing, archive)

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
