"""Asset-free regression tests for the private original animation renderer runner."""
import importlib.util
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location(
    "original_render_runner", ROOT / "tools/test_original_render.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class OriginalMotionRenderRunnerTests(unittest.TestCase):
    def test_compile_only_links_both_rendering_harnesses(self):
        calls = []
        with patch.object(runner.subprocess, "run", side_effect=lambda cmd, **kw: calls.append(cmd)):
            runner.run("synthetic-cc", None, compile_only=True)
        self.assertEqual(len(calls), 2)
        self.assertTrue(any("tests/animation.c" in " ".join(cmd) for cmd in calls))
        self.assertTrue(any("tests/motion_render.c" in " ".join(cmd) for cmd in calls))
        motion = next(cmd for cmd in calls if any(part.endswith("tests/motion_render.c") for part in cmd))
        self.assertTrue(any(part.endswith("source/motion.c") for part in motion))
        self.assertTrue(any(part.endswith("source/head.c") for part in motion))

    def test_private_original_assets_are_staged_only_temporarily(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "synthetic.zip"
            with zipfile.ZipFile(archive, "w") as z:
                for name in runner.REQUIRED:
                    z.writestr(name, b"synthetic private resource bytes")
            invoked = []

            def capture(command, **kw):
                invoked.append(command)
                if command[0] == "synthetic-cc":
                    return
                # Resource paths must be exact from the private archive and
                # never point inside source/, tests/, or a public GitHub path.
                self.assertEqual(len(command), 4 if "sampled" in command[0] else 6)
                for name, staged in zip(
                    runner.ASSET_NAMES if "sampled" in command[0]
                    else runner.MOTION_ASSET_NAMES, command[1:]):
                    path = Path(staged)
                    self.assertTrue(path.is_file())
                    self.assertEqual(path.read_bytes(), b"synthetic private resource bytes")
                    self.assertTrue(str(path).endswith(name))

            with patch.object(runner.subprocess, "run", side_effect=capture):
                runner.run("synthetic-cc", archive)
            self.assertEqual(len(invoked), 4)
            self.assertFalse((ROOT / "nitrofiles/models/MaleBody.msp").exists())

    def test_missing_private_motion_resources_do_not_start_compiler(self):
        with tempfile.TemporaryDirectory() as temp:
            archive = Path(temp) / "missing-msp1.zip"
            with zipfile.ZipFile(archive, "w") as z:
                for name in runner.ASSET_NAMES:
                    z.writestr(name, b"synthetic")
            with patch.object(runner.subprocess, "run") as compiler:
                with self.assertRaises(KeyError):
                    runner.run("synthetic-cc", archive)
                compiler.assert_not_called()


if __name__ == "__main__":
    unittest.main()
