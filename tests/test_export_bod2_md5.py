"""Synthetic original BOD2 -> Nitro Engine / DSMA MD5 geometry regression."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "export_bod2_md5", ROOT / "tools/export_bod2_md5.py")
mod = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(mod)


def sample(materials=(0, 0, 0, 1, 1, 1), bones=(0, 1, 17, 2, 8, 16)):
    data = bytearray(b"BOD2" + struct.pack("<I", len(materials)) + bytes(48))
    for i, (material, bone) in enumerate(zip(materials, bones)):
        data += mod.VERTEX.pack(i * 128, (i % 3) * 64, -(i % 3) * 32,
                                0, 127, 0, material, bone)
    return bytes(data)


class OriginalBodyDSMATests(unittest.TestCase):
    def test_source_triangles_and_bone_mapping(self):
        text = mod.emit_mesh(sample())
        self.assertIn("numJoints 18", text)
        self.assertIn("numMeshes 2", text)
        self.assertIn("weight 2 17 1.0 ( 2 1 -0.5 )", text)
        self.assertIn("weight 2 16 1.0", text)
        self.assertIn("tri 0 2 1 0", text)
        self.assertEqual(text.count("numtris 1"), 2)
        self.assertEqual(text.count("numweights 3"), 2)

    def test_reject_invalid_or_partial_source_models(self):
        valid = sample()
        for bad in (b"", b"BOD3" + valid[4:], valid[:-1], valid + b"X",
                    valid[:4] + struct.pack("<I", 0) + valid[8:],
                    valid[:4] + struct.pack("<I", 3) + valid[8:],
                    valid[:4] + struct.pack("<I", 12003) + valid[8:]):
            with self.subTest(bad=len(bad)):
                with self.assertRaises(ValueError):
                    mod.emit_mesh(bad)
        bad_bone = bytearray(valid)
        bad_bone[56 + 10] = 18
        with self.assertRaises(ValueError):
            mod.emit_mesh(bytes(bad_bone))
        bad_material = bytearray(valid)
        bad_material[56 + 9] = 3
        with self.assertRaises(ValueError):
            mod.emit_mesh(bytes(bad_material))
        with self.assertRaises(ValueError):
            mod.emit_mesh(sample(materials=(0, 1, 0, 1, 1, 1)))

    def test_export_is_private_and_does_not_fabricate_uv_or_animation(self):
        content = mod.emit_mesh(sample())
        self.assertIn("vert 0 ( 0 0 ) 0 1", content)
        self.assertIn("bone_17", content)
        self.assertNotIn("numFrames", content)
        with self.assertRaises(ValueError):
            mod.emit_mesh(sample(), "invalid/path")
        with tempfile.TemporaryDirectory() as work:
            root = Path(work)
            source = root / "synthetic.bin"
            source.write_bytes(sample())
            dest = root / "models"
            subprocess.run([sys.executable, str(ROOT / "tools/export_bod2_md5.py"),
                            "--input", str(source), "--output", str(dest),
                            "--name", "MiiTest"], cwd=ROOT, check=True,
                           capture_output=True, timeout=30)
            self.assertEqual((dest / "MiiTest.md5mesh").read_text(), content)


if __name__ == "__main__":
    unittest.main()
