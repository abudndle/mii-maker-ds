import hashlib
import json
import subprocess
from unittest import mock
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from private_rom_acceptance import commands, make_report, launch_emulator, write_report, sha256_file, ROOT


class AcceptanceTests(unittest.TestCase):
    def test_evidence_hashes_and_unverified_gameplay(self):
        with tempfile.TemporaryDirectory() as d:
            rom, archive = Path(d) / "rom.nds", Path(d) / "private.zip"
            rom.write_bytes(b"synthetic rom")
            archive.write_bytes(b"synthetic resources")
            report = make_report(rom, archive, emulator_launched=True)
            self.assertEqual(report["private_rom_sha256"], hashlib.sha256(rom.read_bytes()).hexdigest())
            self.assertEqual(report["archive_sha256"], hashlib.sha256(archive.read_bytes()).hexdigest())
            self.assertEqual(report["private_rom_bytes"], len(b"synthetic rom"))
            self.assertEqual(report["archive_bytes"], len(b"synthetic resources"))
            self.assertTrue(report["emulator_launched"])
            self.assertFalse(report["gameplay_verified"])

    def test_streaming_hash_matches_standard_sha256_across_chunks(self):
        with tempfile.TemporaryDirectory() as d:
            sample = Path(d) / "large-private-fixture.bin"
            data = (b"private synthetic fixture" * 50000) + b"tail"
            sample.write_bytes(data)
            self.assertGreater(len(data), 1024 * 1024)
            self.assertEqual(sha256_file(sample), hashlib.sha256(data).hexdigest())

    def test_hash_rejects_archive_modified_while_reading(self):
        with tempfile.TemporaryDirectory() as d:
            archive = Path(d) / "synthetic-archive.bin"
            archive.write_bytes(b"A" * (2 * 1024 * 1024))
            original_open = Path.open
            class MutatingReader:
                def __init__(self, wrapped):
                    self.wrapped = wrapped
                    self.changed = False
                def __enter__(self):
                    self.wrapped.__enter__()
                    return self
                def __exit__(self, *args):
                    return self.wrapped.__exit__(*args)
                def fileno(self):
                    return self.wrapped.fileno()
                def read(self, size):
                    data = self.wrapped.read(size)
                    if not self.changed:
                        self.changed = True
                        with original_open(archive, "ab") as output:
                            output.write(b"changed")
                    return data
            def patched_open(path, *args, **kwargs):
                opened = original_open(path, *args, **kwargs)
                return MutatingReader(opened) if Path(path) == archive else opened
            with mock.patch.object(Path, "open", patched_open):
                with self.assertRaisesRegex(ValueError, "changed while hashing"):
                    sha256_file(archive)

    def test_missing_rom_evidence_fails(self):
        with tempfile.TemporaryDirectory() as d:
            missing = Path(d) / "missing.nds"
            archive = Path(d) / "archive.zip"
            archive.write_bytes(b"fixture")
            with self.assertRaises(ValueError):
                make_report(missing, archive)

    def test_empty_and_symlinked_evidence_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            rom, archive = Path(d) / "rom.nds", Path(d) / "archive.zip"
            rom.write_bytes(b"valid synthetic rom")
            archive.write_bytes(b"")
            with self.assertRaises(ValueError):
                make_report(rom, archive)
            archive.write_bytes(b"valid synthetic archive")
            rom.write_bytes(b"")
            with self.assertRaises(ValueError):
                make_report(rom, archive)
            rom.unlink()
            rom.symlink_to(archive)
            with self.assertRaises(ValueError):
                make_report(rom, archive)

    def test_emulator_start_recorded_even_if_exit_fails(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "report.json"
            report = {"emulator_launched": False, "gameplay_verified": False}
            with self.assertRaises(subprocess.CalledProcessError):
                launch_emulator([sys.executable, "-c", "import sys; sys.exit(7)"], report, path)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(saved["emulator_launched"])
            self.assertFalse(saved["gameplay_verified"])

    def test_emulator_success_still_requires_gameplay_verification(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "report.json"
            report = {"emulator_launched": False, "gameplay_verified": False}
            launch_emulator([sys.executable, "-c", "pass"], report, path)
            saved = json.loads(path.read_text(encoding="utf-8"))
            self.assertTrue(saved["emulator_launched"])
            self.assertFalse(saved["gameplay_verified"])

    def test_failed_process_creation_does_not_mark_launch(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "report.json"
            report = {"emulator_launched": False, "gameplay_verified": False}
            with self.assertRaises(OSError):
                launch_emulator([str(Path(d) / "nonexistent-emulator")], report, path)
            self.assertFalse(report["emulator_launched"])
            self.assertFalse(path.exists())

    def test_atomic_report_replacement(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "build" / "private-acceptance-report.json"
            write_report(path, {"emulator_launched": False})
            write_report(path, {"emulator_launched": True, "gameplay_verified": False})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")),
                             {"emulator_launched": True, "gameplay_verified": False})
            self.assertEqual(list(path.parent.glob("*.tmp")), [])

    def test_atomic_report_failure_preserves_existing_report(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "build" / "private-acceptance-report.json"
            write_report(path, {"status": "previous"})
            with mock.patch("private_rom_acceptance.os.replace", side_effect=OSError("synthetic failure")):
                with self.assertRaises(OSError):
                    write_report(path, {"status": "new"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"status": "previous"})
            self.assertEqual(list(path.parent.glob(".private-acceptance-*.tmp")), [])

    def test_symlinked_report_destination_rejected(self):
        with tempfile.TemporaryDirectory() as d:
            original = Path(d) / "protected.json"
            original.write_text("protected", encoding="utf-8")
            destination = Path(d) / "report.json"
            destination.symlink_to(original)
            with self.assertRaises(ValueError):
                write_report(destination, {"gameplay_verified": False})
            self.assertEqual(original.read_text(encoding="utf-8"), "protected")
            self.assertTrue(destination.is_symlink())

    def test_atomic_report_directory_sync(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d) / "build" / "private-acceptance-report.json"
            with mock.patch("private_rom_acceptance.os.fsync", wraps=__import__("os").fsync) as sync:
                write_report(path, {"status": "persisted"})
            self.assertEqual(json.loads(path.read_text(encoding="utf-8")), {"status": "persisted"})
            if hasattr(__import__("os"), "O_DIRECTORY"):
                self.assertGreaterEqual(sync.call_count, 2)

    def test_native_build(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "private.zip"
            result = commands(p)
            self.assertEqual(result, [[sys.executable, "tools/build_private.py", str(p.resolve()), "--no-cache"]])

    def test_docker_and_emulator(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "private.zip"
            result = commands(p, docker=True, emulator="/usr/bin/melonDS")
            self.assertEqual(result[0][1], "tools/build_private_docker.py")
            self.assertEqual(result[1], ["/usr/bin/melonDS", str(ROOT / "mii-ds.nds")])


if __name__ == "__main__":
    unittest.main()
