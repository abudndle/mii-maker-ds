"""Asset-free tests for melonDS 1.1's actual effective config resolution."""
import hashlib
import tempfile
import unittest
from pathlib import Path

from tools.verify_melonds_input_config import inspect


class ConfigOriginTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.home = root / "isolated-home"
        self.home.mkdir()
        self.proc = root / "proc"
        (self.proc / "1234").mkdir(parents=True)
        self.exe = root / "app" / "usr" / "bin" / "melonDS"
        self.exe.parent.mkdir(parents=True)
        self.exe.write_bytes(b"synthetic")
        (self.proc / "1234" / "exe").symlink_to(self.exe)
        self.config = self.home / ".config" / "melonDS" / "melonDS.toml"
        self.config.parent.mkdir(parents=True)
        self.config.write_text("[Instance0.Keyboard]\nB = 90\n")
        self.environment({"HOME": str(self.home)})

    def environment(self, values):
        raw = b"\0".join((key + "=" + value).encode() for key, value in values.items())
        (self.proc / "1234" / "environ").write_bytes(raw + b"\0")

    def test_running_process_uses_isolated_home_and_b(self):
        self.assertEqual(inspect(1234, self.home, self.proc), "isolated-home")

    def test_portable_directory_takes_precedence_over_home(self):
        (self.exe.parent / "portable").mkdir()
        with self.assertRaisesRegex(ValueError, "portable config"):
            inspect(1234, self.home, self.proc)

    def test_xdg_override_is_rejected_even_if_home_is_correct(self):
        self.environment({"HOME": str(self.home),
                          "XDG_CONFIG_HOME": str(self.home / "alternate")})
        with self.assertRaisesRegex(ValueError, "XDG config root"):
            inspect(1234, self.home, self.proc)

    def test_process_home_mismatch_is_rejected(self):
        self.environment({"HOME": str(self.home.parent / "other")})
        with self.assertRaisesRegex(ValueError, "HOME does not match"):
            inspect(1234, self.home, self.proc)

    def test_missing_and_unmapped_b_fail_closed(self):
        self.config.unlink()
        with self.assertRaisesRegex(ValueError, "effective TOML is absent"):
            inspect(1234, self.home, self.proc)
        self.config.write_text("[Instance0.Keyboard]\nB = -1\n")
        with self.assertRaisesRegex(ValueError, "not Qt::Key_Z"):
            inspect(1234, self.home, self.proc)
        self.config.write_text("[Instance0.Keyboard]\nB = true\n")
        with self.assertRaisesRegex(ValueError, "not Qt::Key_Z"):
            inspect(1234, self.home, self.proc)

    def test_malformed_toml_is_rejected(self):
        self.config.write_text("[Instance0.Keyboard\nB = 90\n")
        with self.assertRaisesRegex(ValueError, "unreadable"):
            inspect(1234, self.home, self.proc)

    def test_prelaunch_fingerprint_detects_emulator_rewrite(self):
        expected = hashlib.sha256(self.config.read_bytes()).hexdigest()
        self.assertEqual(inspect(1234, self.home, self.proc, expected),
                         "isolated-home")
        self.config.write_text("[Instance0.Keyboard]\nA = 90\n")
        with self.assertRaisesRegex(ValueError, "changed isolated B config"):
            inspect(1234, self.home, self.proc, expected)
        # No fingerprint: report the missing mapping distinctly from
        # malformed TOML, without printing the configuration path.
        with self.assertRaisesRegex(ValueError, "effective B mapping is missing"):
            inspect(1234, self.home, self.proc)

    def test_invalid_fingerprint_fails_closed(self):
        with self.assertRaisesRegex(ValueError, "invalid expected config fingerprint"):
            inspect(1234, self.home, self.proc, "not-a-sha")

    def test_invalid_pid_rejected(self):
        with self.assertRaisesRegex(ValueError, "invalid emulator PID"):
            inspect(0, self.home, self.proc)


if __name__ == "__main__":
    unittest.main()
