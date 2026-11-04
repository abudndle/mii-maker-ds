"""Asset-free tests for the trusted private-repository original-ROM build route."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
WORKFLOW = ROOT / ".github/workflows/private-original-rom-build.yml"
MANIFEST_HASH = "1313407d57226dfe10993a9a16e2f991efa730ecd2f137b0762dbc6927d321ac"


class PrivateAssetCheckoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW.read_text(encoding="utf-8")

    def test_source_selection_is_restricted_to_trusted_build(self):
        text = self.workflow
        self.assertIn("MII_PRIVATE_REPO_READ_TOKEN", text)
        self.assertIn("MII_ASSETS_URL", text)
        self.assertIn("workflow_dispatch:", text)
        self.assertIn("branches:", text)
        self.assertNotIn("pull_request:", text)
        self.assertIn("Select protected original-resource source", text)
        self.assertIn('if [ -n "$PRIVATE_REPO_TOKEN" ]; then', text)

    def test_private_checkout_is_read_only_without_persisted_credentials(self):
        text = self.workflow
        self.assertIn("repository: abudndle/mii-maker-ds-private", text)
        self.assertIn("token: ${{ secrets.MII_PRIVATE_REPO_READ_TOKEN }}", text)
        self.assertIn("persist-credentials: false", text)
        self.assertIn("sparse-checkout-cone-mode: false", text)
        self.assertIn("archives/MiiMaker_DS_Resources.zip", text)
        self.assertIn("path: .private-original-assets", text)

    def test_archive_is_pinned_before_use(self):
        text = self.workflow
        self.assertIn(MANIFEST_HASH, text)
        self.assertIn('test "$(stat -c %s "$source_zip")" -eq 20770477', text)
        self.assertGreaterEqual(text.count("sha256sum --check --status"), 2)
        self.assertIn('rm -rf -- .private-original-assets', text)

    def test_url_fallback_and_private_mode_are_mutually_exclusive(self):
        text = self.workflow
        self.assertIn("steps.asset_source.outputs.private_repo == 'true'", text)
        self.assertIn("steps.asset_source.outputs.private_repo != 'true'", text)
        self.assertIn("private_repo=false", text)
        self.assertIn("private_repo=true", text)
        self.assertIn("python3 tools/restore_asset_zip.py /tmp/mii-private-original.zip", text)

    def test_only_encrypted_artifacts_are_exported(self):
        text = self.workflow
        self.assertIn("mii-ds.nds.gpg", text)
        self.assertIn("name: mii-maker-ds-private-encrypted", text)
        self.assertIn("gpg --batch --yes --trust-model always", text)
        self.assertIn("rm -rf nitrofiles assets/ui", text)


if __name__ == "__main__":
    unittest.main()
