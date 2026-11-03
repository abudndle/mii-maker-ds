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
        # Two intended Edit actions plus one guarded retry of the first.
        self.assertEqual(s.count('tap 210 "$((touch_origin+179))"'), 3)
        retry = s[s.index('if ! timeout 15s python3 tools/check_melonds_confirm_modal.py '
                          '"$MELONDS_RECEIVED_GALLERY" "$MELONDS_RECEIVED_MODAL"'):
                  s.index('Received acceptance: rejecting copy-to-edit')]
        self.assertIn('cmp -s "$RUNNER_TEMP/melonds-received-before.sav" "$PWD/mii-ds.sav"', retry)
        self.assertIn('kill -0 "$emu_pid"', retry)
        self.assertIn('tap 210 "$((touch_origin+179))"', retry)
        self.assertIn('capture_received "$MELONDS_RECEIVED_MODAL"', retry)
        self.assertIn('tools/check_melonds_confirm_modal.py "$MELONDS_RECEIVED_GALLERY" "$MELONDS_RECEIVED_MODAL"', retry)
        self.assertNotIn('|| true', retry)
        self.assertIn('tap 128 "$((touch_origin+127))"', s)
        self.assertIn('tap 128 "$((touch_origin+87))"', s)
        self.assertIn('tools/check_melonds_confirm_modal.py', s)
        self.assertIn('tools/check_melonds_edit_transition.py', s)
        # Initial dismissal probe, guarded retry probe, and final settled-state proof.
        self.assertEqual(s.count('tools/check_melonds_modal_dismissal.py'), 3)

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
        # One initial touch plus at most two guarded retries; the loop must
        # not replay No after an observed dismissal or a cartridge write.
        self.assertEqual(s.count('tap 128 "$((touch_origin+127))"'), 2)
        retry = s[s.index('for no_retry in 1 2; do'):
                  s.index('timeout 15s python3 tools/melonds_gallery_probe.py '
                          '"$MELONDS_RECEIVED_HOME" "$MELONDS_RECEIVED_CANCEL"')]
        self.assertIn('for no_retry in 1 2; do', retry)
        self.assertIn('if timeout 15s python3 tools/check_melonds_modal_dismissal.py', retry)
        self.assertIn('      break', retry)
        self.assertIn('cmp -s "$RUNNER_TEMP/melonds-received-before.sav" "$PWD/mii-ds.sav"', retry)
        self.assertIn('tools/check_melonds_modal_still_open.py', retry)
        self.assertLess(retry.index('cmp -s'), retry.index('tools/check_melonds_modal_still_open.py'))
        self.assertLess(retry.index('tools/check_melonds_modal_still_open.py'),
                        retry.index('tap 128 "$((touch_origin+127))"'))
        self.assertIn('kill -0 "$emu_pid"', retry)
        self.assertIn('xdotool search --onlyvisible --name "melonDS"', retry)
        self.assertIn('win="$candidate"', retry)
        self.assertIn('xdotool mousemove --window "$win" 128 60', retry)
        self.assertIn('tap 128 "$((touch_origin+127))"', retry)
        self.assertIn('capture_received "$MELONDS_RECEIVED_CANCEL"', retry)
        self.assertIn('  done' + chr(10) + '  timeout 15s python3 tools/check_melonds_modal_dismissal.py', retry)
        self.assertNotIn('|| true' + chr(10) + '  timeout 15s python3 tools/check_melonds_modal_dismissal.py', retry)

    def test_second_received_modal_reselects_source_and_matches_first(self):
        s = SCRIPT.read_text()
        self.assertIn('export MELONDS_RECEIVED_FIRST_MODAL=', s)
        self.assertIn('cp "$MELONDS_RECEIVED_MODAL" "$MELONDS_RECEIVED_FIRST_MODAL"', s)
        after_no = s[s.index('Received acceptance: cancellation left cartridge byte-identical'):
                     s.index('Received acceptance: confirming copy-to-edit via original Yes pane')]
        self.assertIn('tap 82 "$((touch_origin+71))"', after_no)
        self.assertLess(after_no.index('tap 82 "$((touch_origin+71))"'),
                        after_no.index('tap 210 "$((touch_origin+179))"'))
        self.assertIn('tools/check_melonds_modal_still_open.py "$MELONDS_RECEIVED_FIRST_MODAL" "$MELONDS_RECEIVED_MODAL"', after_no)
        self.assertLess(after_no.index('capture_received "$MELONDS_RECEIVED_MODAL"'),
                        after_no.index('tools/check_melonds_modal_still_open.py'))
        tap = s[s.index('  tap() {'):s.index('  sleep 12', s.index('  tap() {'))]
        self.assertLess(tap.index('timeout 5s xdotool mousemove --window'),
                        tap.index('sleep 0.15'))
        self.assertLess(tap.index('sleep 0.15'),
                        tap.index('timeout 5s xdotool mousedown 1'))

    def test_yes_retry_requires_unchanged_eeprom_and_same_visible_modal(self):
        s = SCRIPT.read_text()
        self.assertEqual(s.count('tap 128 "$((touch_origin+87))"'), 2)
        begin = s.index('Received acceptance: confirming copy-to-edit via original Yes pane')
        end = s.index('Received acceptance: confirmed copy opened editor', begin)
        yes = s[begin:end]
        self.assertIn('if cmp -s "$RUNNER_TEMP/melonds-received-before.sav" "$PWD/mii-ds.sav"; then', yes)
        self.assertIn('tools/check_melonds_modal_still_open.py "$MELONDS_RECEIVED_MODAL" "$MELONDS_RECEIVED_EDITOR"', yes)
        self.assertIn('kill -0 "$emu_pid"', yes)
        self.assertIn('Received acceptance: retrying unobserved Yes touch once', yes)
        self.assertEqual(yes.count('tap 128 "$((touch_origin+87))"'), 2)
        self.assertIn('tools/check_gallery_received_copy_save.py "$RUNNER_TEMP/melonds-received-before.sav" "$PWD/mii-ds.sav" --mode copy', yes)
        self.assertLess(yes.index('--mode copy'),
                        yes.index('tools/check_melonds_edit_transition.py'))
        self.assertNotIn('|| true', yes)

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
