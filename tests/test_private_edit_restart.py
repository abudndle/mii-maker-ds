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
        self.assertIn('timeout 60s "$appimage" --appimage-extract >/dev/null', s)
        self.assertIn('test -x "$edit_appdir/squashfs-root/AppRun"', s)
        self.assertIn('export APPDIR="$edit_appdir/squashfs-root"', s)
        self.assertIn('export MELONDS_APP="$APPDIR/AppRun"', s)
        self.assertIn('setsid -w "$MELONDS_APP" "$MELONDS_ROM"', s)
        self.assertNotIn('setsid -w "$MELONDS_APP" --appimage-extract-and-run', s)
        self.assertIn('xdotool mousemove --window "$win" 210 "$((touch_origin+179))"', s)
        self.assertIn('python3 tools/check_melonds_edit_transition.py', s)
        self.assertIn('export XDG_CONFIG_HOME="$HOME/.config"', s)
        self.assertIn('mkdir -p "$XDG_CONFIG_HOME/melonDS"', s)
        self.assertIn('[Instance0.Keyboard]\nB = 90\nTOML', s)
        # DS keys are sampled at VBlank; a short synthetic X11 key event
        # may be missed even when Qt maps it correctly. Require a held B.
        self.assertIn('timeout 5s xdotool windowfocus --sync "$win" || true\n  # A one-shot xdotool key', s)
        self.assertIn('timeout 5s xdotool keydown --clearmodifiers z\n  sleep 0.35\n  timeout 5s xdotool keyup --clearmodifiers z', s)
        self.assertNotIn('xdotool key --clearmodifiers z', s)
        self.assertIn('python3 tools/melonds_gallery_probe.py "$MELONDS_EDIT_HOME" "$MELONDS_EDIT_RETURN"', s)
        self.assertIn('cmp -s "$RUNNER_TEMP/melonds-edit-before.sav" "$PWD/mii-ds.sav"', s)

    def test_bounded_emulator_capture_and_safe_stage_diagnostics(self):
        s = SCRIPT.read_text()
        self.assertIn('timeout 150s xvfb-run', s)
        self.assertEqual(s.count('capture_edit "$MELONDS_EDIT_'), 5)
        self.assertNotIn('import -window "$win"', s)
        self.assertNotIn('capture_method=window', s)
        self.assertIn('timeout 12s import -window root -depth 8 -crop', s)
        self.assertIn('candidate="$(timeout 5s xdotool search --onlyvisible --name "melonDS"', s)
        self.assertIn('geometry="$(timeout 5s xdotool getwindowgeometry --shell "$candidate"', s)
        self.assertIn('win="$candidate"', s)
        self.assertIn('no stable visible melonDS window for bounded Edit capture', s)
        self.assertIn('x + width <= 1280 && y + height <= 960', s)
        self.assertNotIn('import -window root -depth 8 "$destination"', s)
        self.assertEqual(s.count('timeout 5s xdotool mousemove --window "$win"'), 3)
        self.assertEqual(s.count('timeout 5s xdotool mousedown 1'), 3)
        self.assertEqual(s.count('timeout 5s xdotool mouseup 1'), 3)
        self.assertIn('timeout 15s python3 tools/check_melonds_edit_transition.py', s)
        for stage in ('launching isolated emulator', 'window ready',
                      'verifying gallery entry', 'selected ordinary Mii',
                      'verifying editor transition', 'verifying B return'):
            self.assertIn('Edit acceptance: ' + stage, s)
        # Diagnostics must not print the owner archive, raw save or screenshots.
        self.assertNotIn('cat "$RUNNER_TEMP/melonds-edit-before.sav"', s)

    def test_every_emulator_stage_reaps_appimage_children(self):
        # Three separate xvfb-run sessions must not leave a Qt child behind:
        # a later launcher may exit cleanly after handing its ROM to an orphan.
        for name in ("run_melonds_headless.sh", "run_melonds_copy_restart.sh",
                     "run_melonds_edit_restart.sh"):
            script = (ROOT / "tools" / name).read_text()
            if name == "run_melonds_edit_restart.sh":
                self.assertIn('setsid -w "$MELONDS_APP" "$MELONDS_ROM"', script)
            else:
                self.assertIn('setsid -w "$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM"', script)
            self.assertIn('kill -- "-$emu_pid" 2>/dev/null || true', script)
            self.assertIn('wait "$emu_pid" 2>/dev/null || true', script)
            self.assertIn('trap cleanup_emulator EXIT', script)
            subprocess.run(["bash", "-n", str(ROOT / "tools" / name)], check=True)
        edit = SCRIPT.read_text()
        self.assertIn('if wait "$emu_pid"; then', edit)
        self.assertIn('Edit emulator launcher exited cleanly before capture', edit)
        self.assertIn('Edit emulator exited before capture (status $status)', edit)

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
