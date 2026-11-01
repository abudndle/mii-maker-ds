"""Validate the CI-only 10-Mii EEPROM fixture against BOTH save formats."""
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SOURCES=(
    ROOT/"tools/make_gallery_fixture.c",
    ROOT/"source/save.c",
    ROOT/"source/save_compact.c",
    ROOT/"source/avatar.c",
    ROOT/"source/unicode.c",
)
class EepromGalleryFixtureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp=tempfile.TemporaryDirectory()
        cls.exe=Path(cls.temp.name)/"make_fixture"
        subprocess.run(["cc","-std=c11","-Wall","-Wextra","-Werror",
                        "-I",str(ROOT/"source"),
                        *[str(p) for p in SOURCES],"-o",str(cls.exe)],check=True)
    @classmethod
    def tearDownClass(cls):
        cls.temp.cleanup()
    def test_compact_eeprom_for_emulator(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"mii-ds.sav"
            subprocess.run([str(self.exe),str(dest)],check=True,capture_output=True)
            b=dest.read_bytes()
            self.assertEqual(len(b),8192)
            self.assertEqual(b[:4],b"MDSC")
            self.assertEqual(int.from_bytes(b[4:8],"little"),2)
            self.assertEqual(b[24],1)
    def test_legacy_dualbank_remains_compatible(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"legacy.sav"
            subprocess.run([str(self.exe),str(dest),"--legacy-64k"],check=True,capture_output=True)
            b=dest.read_bytes()
            self.assertEqual(len(b),65536)
            self.assertEqual(b[:4],b"MDSV")
            self.assertEqual(b[32768:32772],b"MDSV")
    def test_no_source_archive_or_rom_required(self):
        with tempfile.TemporaryDirectory() as d:
            dest=Path(d)/"mii-ds.sav"
            subprocess.run([str(self.exe),str(dest)],check=True,capture_output=True)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()),["mii-ds.sav"])

if __name__=="__main__":
    unittest.main()
