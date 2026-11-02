"""Keep the public private-resource checklist aligned with the build gate."""
import pathlib
import re
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]


class PrivateResourceManifestTests(unittest.TestCase):
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

    def test_discarded_cfl_database_is_not_a_manifest_requirement(self):
        manifest = (ROOT / "docs/PRIVATE_RESOURCE_MANIFEST.md").read_text(encoding="utf-8")
        checker = (ROOT / "tools/check_assets.py").read_text(encoding="utf-8")
        self.assertNotRegex(checker, r"(?i)CFL[._]DB\.dat")
        self.assertIn("does not require `CFL.DB.dat` or `CFL_DB.dat`", manifest)


if __name__ == "__main__":
    unittest.main()
