"""Require real private Edit/cancel testing without exporting raw saves."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/run_melonds_edit_restart.sh"
WORKFLOW = ROOT / ".github/workflows/private-original-rom-build.yml"


class EditRestartRunnerTests(unittest.TestCase):
    def test_shell_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_third_process_uses_touch_edit_and_byte_exact_rollback(self):
        s = SCRIPT.read_text()
        self.assertIn('"$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM"', s)
        self.assertIn('xdotool mousemove --window "$win" 210 "$((touch_origin+179))"', s)
        self.assertIn('python3 tools/check_melonds_edit_transition.py', s)
        self.assertIn('export XDG_CONFIG_HOME="$HOME/.config"', s)
        self.assertIn('mkdir -p "$XDG_CONFIG_HOME/melonDS"', s)
        self.assertIn('[Instance0.Keyboard]\nB = 90\nTOML', s)
        # DS keys are sampled at VBlank; a short synthetic X11 key event
        # may be missed even when Qt maps it correctly. Require a held B.
        self.assertIn('timeout 5s xdotool windowfocus --sync "$win" || true\\n  # A one-shot xdotool key', s)
        self.assertIn('xdotool keydown --clearmodifiers z\\n  sleep 0.35\\n  xdotool keyup --clearmodifiers z', s)
        self.assertNotIn('xdotool key --clearmodifiers z', s)
        self.assertIn('python3 tools/melonds_gallery_probe.py "$MELONDS_EDIT_HOME" "$MELONDS_EDIT_RETURN"', s)
        self.assertIn('cmp -s "$RUNNER_TEMP/melonds-edit-before.sav" "$PWD/mii-ds.sav"', s)

    def test_workflow_private_and_encrypted(self):
        w = WORKFLOW.read_text()
        self.assertNotIn("  pull_request:", w)
        self.assertIn("run: timeout 180s bash tools/run_melonds_edit_restart.sh", w)
        self.assertIn("steps.melon_edit.outcome == 'failure'", w)
        self.assertIn('--output melonds-edit.png.gpg --encrypt', w)
        self.assertIn('melonds-edit.png.gpg', w)
        self.assertIn('rm -f "$RUNNER_TEMP/melonds-edit-before.sav"', w)
        artifact = w.split('name: mii-maker-ds-private-encrypted', 1)[1].split(
            'retention-days:', 1)[0]
        self.assertNotIn('.sav', artifact)
        for line in artifact.splitlines():
            line = line.strip()
            if line.startswith(("mii-ds.", "melonds-")):
                self.assertTrue(line.endswith(".gpg"), line)


if __name__ == "__main__":
    unittest.main()
