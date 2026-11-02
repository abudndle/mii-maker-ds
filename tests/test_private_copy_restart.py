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

    def test_early_copy_captures_are_bounded_and_diagnosable(self):
        s = self.script
        # The previous trusted run timed out before reaching the Edit marker.
        # Initial Home, saved gallery and post-Copy captures must not hang
        # indefinitely in ImageMagick's XGetImage.
        for capture in ("HOME", "GALLERY", "IMAGE"):
            self.assertIn('capture_copy_edit "$MELONDS_COPY_' + capture + '"', s)
            self.assertNotIn('import -window "$win" -depth 8 "$MELONDS_COPY_' + capture + '"', s)
        self.assertEqual(s.count('capture_copy_edit "$MELONDS_COPY_'), 6)
        self.assertEqual(s.count('timeout 5s xdotool windowfocus --sync "$win" || true'), 4)
        self.assertNotIn('  xdotool windowfocus --sync "$win" || true', s)
        for marker in ("capturing reopened Home", "capturing saved gallery",
                       "capturing post-Copy gallery"):
            self.assertIn("Copy acceptance: " + marker, s)
        self.assertNotIn('import -window "$win"', s)
        self.assertIn('timeout 12s import -window root -depth 8 -crop', s)
        self.assertIn('x + width <= 1280 && y + height <= 960', s)
        # The first real post-merge run showed the initial Home capture
        # hanging in XGetImage, then the title-based re-search found no
        # visible "melonDS" window. Use the stable original XID first.
        self.assertIn('candidate="$win" geometry=""', s)
        self.assertIn('geometry="$(timeout 5s xdotool getwindowgeometry --shell "$candidate"', s)
        self.assertLess(s.index('geometry="$(timeout 5s xdotool getwindowgeometry --shell "$candidate"'),
                        s.index('candidate="$(timeout 5s xdotool search --onlyvisible --name "melonDS"'))
        self.assertIn('win="$candidate"', s)
        self.assertIn('timeout 5s identify -format "%wx%h" "$destination"', s)
        self.assertNotIn('import -window "$win"', s)


    def test_second_launch_reaps_orphans_and_classifies_early_exit(self):
        s = self.script
        # The previous private run lost the second Qt window before the
        # first Home capture. Do not assume a briefly visible XID stays live.
        self.assertIn('if pgrep -x melonDS >/dev/null 2>&1; then', s)
        self.assertIn('pkill -TERM -x melonDS 2>/dev/null || true', s)
        self.assertIn('pkill -KILL -x melonDS 2>/dev/null || true', s)
        self.assertIn('prior melonDS process survived cleanup; refusing Copy test', s)
        self.assertLess(s.index('pkill -TERM -x melonDS'),
                        s.index('export MELONDS_APP="$appimage"'))
        self.assertNotIn('pkill -f', s)
        self.assertNotIn('killall', s)
        self.assertIn('if ! kill -0 "$emu_pid" 2>/dev/null; then\n    echo "FAIL: restarted emulator launcher exited before Home capture"', s)
        self.assertEqual(s.count('python3 tools/classify_melonds_startup.py "$MELONDS_COPY_LOG"'), 2)
        self.assertLess(s.index('restarted emulator launcher exited before Home capture'),
                        s.index('Copy acceptance: capturing reopened Home'))

    def test_in_session_edit_is_real_and_does_not_mutate_copy(self):
        s = self.script
        # The real main-run Edit screenshot stayed unchanged after z/B:
        # melonDS 1.1 uses -1 for unconfigured keyboard bindings. Bind B
        # explicitly without the XDG_CONFIG_HOME override that preceded
        # earlier launcher aborts. The trusted ROM run still decides success.
        self.assertIn('export HOME="$RUNNER_TEMP/melonds-home-restart"', s)
        self.assertIn('mkdir -p "$HOME/.config/melonDS"', s)
        self.assertIn('cat >"$HOME/.config/melonDS/melonDS.toml"', s)
        self.assertIn('[Instance0.Keyboard]', s)
        self.assertIn('B = 90', s)
        self.assertLess(s.index('[Instance0.Keyboard]'), s.index('B = 90'))
        self.assertIn('tomllib.loads(pathlib.Path(sys.argv[1]).read_text())', s)
        self.assertIn('cfg["Instance0"]["Keyboard"]["B"] == 90', s)
        self.assertNotIn('export XDG_CONFIG_HOME=', s)
        self.assertIn('cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-copy-postcopy.sav"', s)
        self.assertIn('xdotool mousemove --window "$win" 210 "$((touch_origin+179))"', s)
        self.assertIn('python3 tools/check_melonds_edit_transition.py "$MELONDS_COPY_EDIT_GALLERY" "$MELONDS_COPY_EDIT_IMAGE"', s)
        self.assertIn('xdotool keydown --clearmodifiers z\n  sleep 0.35\n  xdotool keyup --clearmodifiers z', s)
        self.assertIn('python3 tools/melonds_gallery_probe.py "$MELONDS_COPY_HOME" "$MELONDS_COPY_EDIT_RETURN"', s)
        self.assertIn('cmp -s "$RUNNER_TEMP/melonds-copy-postcopy.sav" "$PWD/mii-ds.sav"', s)
        self.assertLess(s.index('cp "$PWD/mii-ds.sav" "$RUNNER_TEMP/melonds-copy-postcopy.sav"'),
                        s.index('xdotool mousemove --window "$win" 210 "$((touch_origin+179))"'))
        self.assertEqual(s.count('capture_copy_edit "$MELONDS_COPY_EDIT_'), 3)
        self.assertNotIn('import -window "$win"', s)
        self.assertIn('timeout 12s import -window root -depth 8 -crop', s)
        self.assertIn('x + width <= 1280 && y + height <= 960', s)
        self.assertNotIn('import -window root -depth 8 "$destination"', s)
        for marker in ("capturing selected gallery", "capturing editor", "capturing B return"):
            self.assertIn("Edit acceptance: " + marker, s)
        # The previous private run proved Edit entry but B returned an
        # identical bottom-screen image. Retry only after a failed visual
        # return check, otherwise a second B could exit the gallery.
        self.assertIn('if ! python3 tools/check_melonds_edit_transition.py "$MELONDS_COPY_EDIT_RETURN" "$MELONDS_COPY_EDIT_IMAGE"; then', s)
        self.assertIn('B not observed; focusing game surface and retrying once', s)
        self.assertIn('xdotool mousemove --window "$win" 128 65', s)
        self.assertIn('sleep 0.6', s)
        self.assertLess(s.index('B not observed; focusing game surface and retrying once'),
                        s.index('sleep 0.6'))
        self.assertIn('kill -0 "$emu_pid"\\n    capture_copy_edit "$MELONDS_COPY_EDIT_RETURN"', s)
        self.assertIn('melonds-edit.png.gpg', self.workflow)
        self.assertIn('"$RUNNER_TEMP/melonds-copy-postcopy.sav"', self.workflow)

    def test_private_workflow_encrypts_copy_capture_and_cleans_saves(self):
        w = self.workflow
        self.assertNotIn("  pull_request:", w)
        self.assertIn('run: timeout 180s bash tools/run_melonds_copy_restart.sh', w)
        self.assertIn("steps.melon_copy.outcome == 'failure'", w)
        self.assertIn('--output melonds-copy.png.gpg --encrypt', w)
        self.assertIn('"$RUNNER_TEMP/melonds-copy-before.sav"', w)
        artifact_block = w.split('name: mii-maker-ds-private-encrypted', 1)[1].split(
            'retention-days:', 1)[0]
        self.assertNotIn('.sav', artifact_block)
        self.assertIn('melonds-copy.png.gpg', artifact_block)


if __name__ == "__main__":
    unittest.main()
