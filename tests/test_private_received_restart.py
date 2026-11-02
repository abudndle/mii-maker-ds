"""Guard the trusted received-Mii melonDS acceptance and asset isolation."""
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "tools/run_melonds_received_restart.sh"
WORKFLOW = ROOT / ".github/workflows/private-original-rom-build.yml"


class ReceivedRunnerTests(unittest.TestCase):
    def test_shell_syntax(self):
        subprocess.run(["bash", "-n", str(SCRIPT)], check=True)

    def test_uses_fresh_synthetic_received_save_and_real_touch(self):
        s = SCRIPT.read_text()
        self.assertIn('"$RUNNER_TEMP/make_gallery_fixture" mii-ds.sav --received', s)
        self.assertIn('cp mii-ds.sav "$RUNNER_TEMP/melonds-received-before.sav"', s)
        self.assertIn('setsid -w "$MELONDS_APP" --appimage-extract-and-run "$MELONDS_ROM"', s)
        self.assertIn('tap 82 "$((touch_origin+71))"', s)
        self.assertEqual(s.count('tap 210 "$((touch_origin+179))"'), 2)
        self.assertIn('tap 128 "$((touch_origin+127))"', s)
        self.assertIn('tap 128 "$((touch_origin+87))"', s)
        self.assertIn('tools/check_melonds_confirm_modal.py', s)
        self.assertIn('tools/check_melonds_edit_transition.py', s)

    def test_exact_cancel_and_confirm_save_gates(self):
        s = SCRIPT.read_text()
        self.assertIn('cmp -s "$RUNNER_TEMP/melonds-received-before.sav" "$PWD/mii-ds.sav"', s)
        self.assertIn('tools/check_gallery_received_copy_save.py', s)
        self.assertIn('mii-ds.sav --mode cancel', s)
        self.assertIn('mii-ds.sav --mode copy', s)
        self.assertLess(s.index('mii-ds.sav --mode cancel'),
                        s.index('tap 210 "$((touch_origin+179))"'))
        self.assertLess(s.index('tap 128 "$((touch_origin+127))"'),
                        s.index('tap 128 "$((touch_origin+87))"'))

    def test_no_touch_retry_is_bounded_and_preserves_received_source(self):
        s = SCRIPT.read_text()
        # A transient dropped No touch must not fail a real private run, but
        # only an unchanged modal AND byte-identical EEPROM authorize retry.
        self.assertEqual(s.count('tap 128 "$((touch_origin+127))"'), 2)
        retry = s[s.index('if ! timeout 15s python3 tools/check_melonds_confirm_modal.py '
                          '"$MELONDS_RECEIVED_MODAL" "$MELONDS_RECEIVED_CANCEL"'):
                  s.index('timeout 15s python3 tools/melonds_gallery_probe.py '
                          '"$MELONDS_RECEIVED_HOME" "$MELONDS_RECEIVED_CANCEL"')]
        self.assertIn('cmp -s "$RUNNER_TEMP/melonds-received-before.sav" "$PWD/mii-ds.sav"', retry)
        self.assertIn('kill -0 "$emu_pid"', retry)
        self.assertIn('xdotool search --onlyvisible --name "melonDS"', retry)
        self.assertIn('win="$candidate"', retry)
        self.assertIn('tap 128 "$((touch_origin+127))"', retry)
        self.assertIn('capture_received "$MELONDS_RECEIVED_CANCEL"', retry)
        self.assertIn('fi\n  timeout 15s python3 tools/check_melonds_confirm_modal.py', retry)
        self.assertNotIn('|| true\n  timeout 15s python3 tools/check_melonds_confirm_modal.py', retry)

    def test_received_editor_b_return_is_persistently_read_only(self):
        s = SCRIPT.read_text()
        self.assertIn('cp "$PWD/mii-ds.sav" "$MELONDS_RECEIVED_POSTCOPY"', s)
        self.assertIn('xdotool keydown --clearmodifiers z', s)
        self.assertIn('xdotool keyup --clearmodifiers z', s)
        self.assertIn('capture_received "$MELONDS_RECEIVED_RETURN"', s)
        self.assertIn('tools/check_melonds_edit_transition.py "$MELONDS_RECEIVED_RETURN" "$MELONDS_RECEIVED_EDITOR"', s)
        self.assertIn('cmp -s "$MELONDS_RECEIVED_POSTCOPY" "$PWD/mii-ds.sav"', s)
        self.assertLess(s.index('Received acceptance: confirmed copy opened editor'),
                        s.index('Received acceptance: B returned from editable copy'))

    def test_private_runtime_is_bounded_and_no_raw_artifacts(self):
        s = SCRIPT.read_text()
        self.assertIn('timeout 170s xvfb-run', s)
        self.assertIn('timeout 12s import -window root -depth 8 -crop', s)
        self.assertIn('x + width <= 1280 && y + height <= 960', s)
        self.assertIn('unset XDG_CONFIG_HOME', s)
        self.assertIn('[Instance0]\n[Instance0.Keyboard]\nB = 90\nTOML', s)
        self.assertIn('tools/verify_melonds_input_config.py', s)
        self.assertNotIn('cat "$RUNNER_TEMP/melonds-received-before.sav"', s)
        self.assertNotIn('upload-artifact', s)
        self.assertNotIn('set -x', s)

    def test_workflow_encrypts_only_private_frames(self):
        w = WORKFLOW.read_text()
        self.assertIn('bash tools/run_melonds_received_restart.sh', w)
        self.assertIn('steps.melon_received.outcome', w)
        for name in ("modal", "cancel", "editor", "return"):
            self.assertIn('melonds-received-' + name + '.png.gpg', w)
        self.assertNotIn('            mii-ds.sav\n', w)


if __name__ == "__main__":
    unittest.main()
