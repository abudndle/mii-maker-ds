"""Keep the public private-resource checklist aligned with the build gate."""
import importlib.util
import pathlib
import tempfile
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PrivateResourceManifestTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location("mds_check_assets", ROOT / "tools/check_assets.py")
        cls.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.checker)

    def _complete_tree(self, root):
        for relative in self.checker.required:
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(b"synthetic-private-resource")
    def test_manifest_covers_every_check_assets_input(self):
        checker = (ROOT / "tools/check_assets.py").read_text(encoding="utf-8")
        manifest = (ROOT / "docs/PRIVATE_RESOURCE_MANIFEST.md").read_text(encoding="utf-8")
        match = re.search(r"required\s*=\s*\[(.*?)\]", checker, re.S)
        self.assertIsNotNone(match, "check_assets.py required list not found")
        required = re.findall(r"['\"]([^'\"]+)['\"]", match.group(1))
        self.assertTrue(required, "check_assets.py required list is empty")
        for relative_path in required:
            with self.subTest(path=relative_path):
                self.assertIn(f"`{relative_path}`", manifest)

    def test_all_regular_nonempty_resources_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._complete_tree(root)
            self.assertEqual(self.checker.validate(root), [])

    def test_empty_required_resource_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._complete_tree(root)
            (root / "nitrofiles/models/MaleBody.ani").write_bytes(b"")
            self.assertTrue(any("MaleBody.ani: file is empty" in item for item in self.checker.validate(root)))

    def test_symlinked_required_resource_is_rejected(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._complete_tree(root)
            target = root / "owned-resource.bin"
            target.write_bytes(b"private")
            link = root / "nitrofiles/models/FemaleBody.ani"
            link.unlink()
            link.symlink_to(target)
            self.assertTrue(any("FemaleBody.ani: must be a regular private file" in item for item in self.checker.validate(root)))

    def test_test_import_fixture_is_blocked_for_production(self):
        with tempfile.TemporaryDirectory() as temp:
            root = pathlib.Path(temp)
            self._complete_tree(root)
            (root / "nitrofiles/test-import").mkdir()
            self.assertTrue(any("test-import fixture" in item for item in self.checker.validate(root)))
            self.assertEqual(self.checker.validate(root, allow_test_import=True), [])

    def test_discarded_cfl_database_is_not_a_manifest_requirement(self):
        manifest = (ROOT / "docs/PRIVATE_RESOURCE_MANIFEST.md").read_text(encoding="utf-8")
        checker = (ROOT / "tools/check_assets.py").read_text(encoding="utf-8")
        self.assertNotRegex(checker, r"(?i)CFL[._]DB\.dat")
        self.assertIn("does not require `CFL.DB.dat` or `CFL_DB.dat`", manifest)


if __name__ == "__main__":
    unittest.main()
