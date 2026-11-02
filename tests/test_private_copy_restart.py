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

    def test_in_session_edit_is_real_and_does_not_mutate_copy(self):
        s = self.script
        self.assertIn('export XDG_CONFIG_HOME="$HOME/.config"', s)
        self.assertIn('[Instance0.Keyboard]\\nB = 90\\nTOML', s)
        self.assertIn('cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-copy-postcopy.sav"', s)
        self.assertIn('xdotool mousemove --window "$win" 210 "$((touch_origin+179))"', s)
        self.assertIn('python3 tools/check_melonds_edit_transition.py "$MELONDS_COPY_EDIT_GALLERY" "$MELONDS_COPY_EDIT_IMAGE"', s)
        self.assertIn('xdotool keydown --clearmodifiers z\\n  sleep 0.35\\n  xdotool keyup --clearmodifiers z', s)
        self.assertIn('python3 tools/melonds_gallery_probe.py "$MELONDS_COPY_HOME" "$MELONDS_COPY_EDIT_RETURN"', s)
        self.assertIn('cmp -s "$RUNNER_TEMP/melonds-copy-postcopy.sav" "$PWD/mii-ds.sav"', s)
        self.assertLess(s.index('cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-copy-postcopy.sav"'),
                        s.index('xdotool mousemove --window "$win" 210 "$((touch_origin+179))"'))
        self.assertIn('melonds-edit.png.gpg', self.workflow)
        self.assertIn('"$RUNNER_TEMP/melonds-copy-postcopy.sav"', self.workflow)

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
