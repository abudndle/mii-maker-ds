"""Asset-free wiring checks for trusted, owner-private melonDS Favorite acceptance."""
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
RUNNER = ROOT / "tools/run_melonds_headless.sh"
WORKFLOW = ROOT / ".github/workflows/private-original-rom-build.yml"


class PrivateFavoriteRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.runner = RUNNER.read_text()
        cls.workflow = WORKFLOW.read_text()

    def test_shell_parses(self):
        subprocess.run(["bash", "-n", str(RUNNER)], check=True)

    def test_real_touch_targets_source_gallery_and_favorite_strip(self):
        runner = self.runner
        self.assertIn('xdotool mousemove --window "$win" 82 "$((touch_origin+71))"', runner)
        self.assertIn('xdotool mousemove --window "$win" 50 "$((touch_origin+179))"', runner)
        self.assertIn('touch_origin=$((capture_height-192))', runner)
        self.assertIn('import -window "$win" -depth 8 "$MELONDS_FAVORITE_IMAGE"', runner)
        self.assertLess(runner.index('echo "PASS: emulator entered gallery'),
                        runner.index('Favorite touch dispatched'))

    def test_actual_eeprom_checked_after_emulator_ends(self):
        runner = self.runner
        self.assertIn('cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-favorite-before.sav"', runner)
        self.assertIn('python3 tools/check_gallery_favorite_save.py', runner)
        self.assertIn('"$RUNNER_TEMP/melonds-favorite-before.sav" "$PWD/mii-ds.sav"', runner)
        self.assertLess(runner.index("'\npython3 tools/melonds_screen_probe.py"),
                        runner.index('python3 tools/check_gallery_favorite_save.py'))

    def test_only_encrypted_favorite_image_exported(self):
        workflow = self.workflow
        self.assertNotIn("  pull_request:", workflow)
        self.assertIn('--output melonds-favorite.png.gpg --encrypt', workflow)
        self.assertIn('melonds-favorite.png.gpg', workflow)
        self.assertIn('rm -f "$RUNNER_TEMP/melonds-favorite-before.sav"', workflow)
        self.assertIn('rm -f /tmp/mii-private-original.zip', workflow)
        artifact_block = workflow.split('name: mii-maker-ds-private-encrypted', 1)[1].split(
            'retention-days:', 1)[0]
        self.assertNotIn('.sav', artifact_block)
        for line in artifact_block.splitlines():
            stripped = line.strip()
            if stripped.startswith(("mii-ds.", "melonds-")):
                self.assertTrue(stripped.endswith(".gpg"), stripped)


if __name__ == "__main__":
    unittest.main()
