"""M121: original-resource build preflight checks without proprietary test data."""
import importlib.util
import pathlib
import tempfile
import unittest
from unittest import mock

ROOT = pathlib.Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("mds_build_preflight", ROOT / "tools" / "build_preflight.py")
preflight = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(preflight)


class PrivateBuildPreflightTests(unittest.TestCase):
    def test_complete_private_resource_layout_is_accepted(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            sdk = root / "sdk"
            toolchain = root / "toolchain"
            required = (
                sdk / "sys/default_makefiles/rom_arm9/Makefile",
                root / "nitrofiles/cfl/CFL_Res.dat",
                root / "nitrofiles/models/MaleBody.bin",
                root / "nitrofiles/models/FemaleBody.bin",
                root / "assets/ui/original-icon.gif",
                toolchain / "bin/arm-none-eabi-gcc",
            )
            for path in required:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic-test-placeholder")
            with mock.patch.object(preflight.shutil, "which", return_value="/usr/bin/synthetic"):
                self.assertEqual(preflight.check(root, sdk, toolchain), [])

    def test_missing_and_zero_length_original_resources_are_reported(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            (root / "nitrofiles/cfl").mkdir(parents=True)
            (root / "nitrofiles/cfl/CFL_Res.dat").touch()
            with mock.patch.object(preflight.shutil, "which", return_value="/usr/bin/synthetic"):
                errors = preflight.check(root, root / "sdk", root / "toolchain")
            self.assertTrue(any("original Mii head resource is empty" in item for item in errors))
            self.assertTrue(any("original male body resource" in item for item in errors))
            self.assertTrue(any("original female body resource" in item for item in errors))
            self.assertTrue(any("original game banner" in item for item in errors))

    def test_symlinked_original_resource_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            sdk = root / "sdk"
            toolchain = root / "toolchain"
            required = (
                sdk / "sys/default_makefiles/rom_arm9/Makefile",
                root / "nitrofiles/models/MaleBody.bin",
                root / "nitrofiles/models/FemaleBody.bin",
                root / "assets/ui/original-icon.gif",
                toolchain / "bin/arm-none-eabi-gcc",
            )
            for path in required:
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(b"synthetic-test-placeholder")
            target = root / "private-original-resource.bin"
            target.write_bytes(b"synthetic-test-placeholder")
            head = root / "nitrofiles/cfl/CFL_Res.dat"
            head.parent.mkdir(parents=True)
            head.symlink_to(target)
            with mock.patch.object(preflight.shutil, "which", return_value="/usr/bin/synthetic"):
                errors = preflight.check(root, sdk, toolchain)
            self.assertTrue(any("original Mii head resource must be a regular private file, not a symlink" in error for error in errors))

    def test_discarded_database_is_not_a_build_requirement(self):
        source = (ROOT / "tools/build_preflight.py").read_text(encoding="utf-8")
        self.assertNotIn("CFL.DB.dat", source)
        self.assertNotIn("CFL_DB.dat", source)


if __name__ == "__main__":
    unittest.main()
