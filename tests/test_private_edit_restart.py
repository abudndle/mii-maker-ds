"""Require real private Edit/cancel testing without exporting raw saves."""
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/run_melonds_edit_restart.sh"
WORKFLOW = ROOT / ".github/workflows/private-original-rom-build.yml"


class EditRestartRunnerTests(unittest.TestCase):
    def test_shell_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_edit_touch_commands_are_real_shell_lines(self):
        # A previous patch accidentally embedded literal backslash-n text
        # inside a shell comment, silently commenting out both touch moves.
        # bash -n accepts that script, so verify executable line boundaries.
        lines = SCRIPT.read_text().splitlines()
        focus = '  timeout 5s xdotool windowfocus --sync "$win" || true'
        for command in (
            '  timeout 5s xdotool mousemove --window "$win" 82 "$((touch_origin+71))"',
            '  timeout 5s xdotool mousemove --window "$win" 210 "$((touch_origin+179))"',
        ):
            self.assertEqual(lines.count(command), 1)
            self.assertEqual(lines[lines.index(command) - 1], focus)
        self.assertNotIn(r'\n  timeout 5s xdotool', SCRIPT.read_text())

    def test_private_startup_diagnostics_never_echo_raw_paths(self):
        classifier = ROOT / "tools/classify_melonds_startup.py"
        samples = {
            "qt-platform-plugin": "qt.qpa.plugin: Could not load the Qt platform plugin xcb",
            "x11-display": "QXcbConnection: Could not connect to display",
            "missing-shared-library": "error while loading shared libraries: libtest.so",
            "existing-emulator-instance": "Another instance is already running",
            "process-abort": "terminate called after throwing an exception",
            "unclassified": "Private startup failure without recognized signature",
        }
        with tempfile.TemporaryDirectory() as folder:
            logfile = Path(folder) / "private.log"
            for category, message in samples.items():
                # The real emulator log can contain an owner-private ROM path.
                logfile.write_text(message + "\\nSECRET_ROM_PATH=/owner/ROM.nds\\n")
                result = subprocess.run(
                    [sys.executable, str(classifier), str(logfile)],
                    check=True, capture_output=True, text=True)
                self.assertEqual(result.stdout.strip(),
                                 "melonDS startup category: " + category)
                self.assertNotIn("SECRET_ROM_PATH", result.stdout)
                self.assertNotIn("/owner/", result.stdout)
                self.assertNotIn(message, result.stdout)
        self.assertIn(
            'python3 tools/classify_melonds_startup.py "$MELONDS_EDIT_LOG"',
            SCRIPT.read_text())

    def test_third_process_uses_touch_edit_and_byte_exact_rollback(self):
        s = SCRIPT.read_text()
        # The first two real private emulator stages use the AppImage runtime.
        # Direct AppRun aborted with status 134 even after restoring its env.
        self.assertIn('export MELONDS_APP="$appimage"', s)
        self.assertIn('setsid -w "$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM"', s)
        self.assertNotIn('export MELONDS_APP="$APPDIR/AppRun"', s)
        self.assertNotIn('timeout 60s "$appimage" --appimage-extract', s)
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

    def test_orphan_emulator_reaper_is_bounded_and_exact_name(self):
        s = SCRIPT.read_text()
        self.assertIn("if pgrep -x melonDS >/dev/null 2>&1; then", s)
        self.assertIn("pkill -TERM -x melonDS 2>/dev/null || true", s)
        self.assertIn("for attempt in 1 2 3 4 5; do", s)
        self.assertIn("pkill -KILL -x melonDS 2>/dev/null || true", s)
        self.assertIn("previous melonDS process survived cleanup; refusing Edit test", s)
        self.assertLess(s.index("pkill -TERM -x melonDS"),
                        s.index('export MELONDS_APP="$appimage"'))
        self.assertNotIn("pkill -f", s)
        self.assertNotIn("killall", s)

    def test_every_emulator_stage_reaps_appimage_children(self):
        # Three separate xvfb-run sessions must not leave a Qt child behind:
        # a later launcher may exit cleanly after handing its ROM to an orphan.
        for name in ("run_melonds_headless.sh", "run_melonds_copy_restart.sh",
                     "run_melonds_edit_restart.sh"):
            script = (ROOT / "tools" / name).read_text()
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
        # Third-process startup has repeatedly aborted. The trusted gate
        # now performs real Edit/cancel in the stable second process instead.
        self.assertIn("run: timeout 180s bash tools/run_melonds_copy_restart.sh", w)
        self.assertNotIn("run: timeout 180s bash tools/run_melonds_edit_restart.sh", w)
        self.assertIn("steps.melon_copy.outcome == 'failure'", w)
        self.assertNotIn("steps.melon_edit.outcome == 'failure'", w)
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
