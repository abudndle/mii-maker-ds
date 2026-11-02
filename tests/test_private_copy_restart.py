"""Ensure the second private melonDS run really restarts and checks Copy."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/run_melonds_copy_restart.sh"
WORKFLOW = ROOT / ".github/workflows/private-original-rom-build.yml"


class CopyRestartRunnerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = SCRIPT.read_text()
        cls.workflow = WORKFLOW.read_text()

    def test_shell_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_second_process_uses_persisted_cartridge_and_touch_copy(self):
        s = self.script
        self.assertIn('cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-copy-before.sav"', s)
        self.assertIn('"$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM"', s)
        self.assertIn('python3 tools/melonds_gallery_probe.py', s)
        self.assertIn('xdotool mousemove --window "$win" 82 "$((touch_origin+71))"', s)
        self.assertIn('xdotool mousemove --window "$win" 128 "$((touch_origin+179))"', s)
        self.assertIn('python3 tools/check_gallery_copy_save.py', s)

    def test_private_workflow_encrypts_copy_capture_and_cleans_saves(self):
        w = self.workflow
        self.assertNotIn("  pull_request:", w)
        self.assertIn('run: bash tools/run_melonds_copy_restart.sh', w)
        self.assertIn("steps.melon_copy.outcome == 'failure'", w)
        self.assertIn('--output melonds-copy.png.gpg --encrypt', w)
        self.assertIn('"$RUNNER_TEMP/melonds-copy-before.sav"', w)
        artifact_block = w.split('name: mii-maker-ds-private-encrypted', 1)[1].split(
            'retention-days:', 1)[0]
        self.assertNotIn('.sav', artifact_block)
        self.assertIn('melonds-copy.png.gpg', artifact_block)


if __name__ == "__main__":
    unittest.main()
