#!/usr/bin/env python3
"""Asset-free regression checks for the private, local-only ROM build helper."""
import io
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
import build_private as runner
from restore_asset_zip import REQUIRED


def make_archive(path):
    with zipfile.ZipFile(path, "w") as archive:
        for name in REQUIRED:
            archive.writestr(name, b"private test fixture only")


with tempfile.TemporaryDirectory(prefix="mii-private-build-") as work:
    work = Path(work)
    archive = work / "private-fixture.zip"
    make_archive(archive)
    commands = []

    def capture(*command):
        commands.append(tuple(map(str, command)))

    with patch.object(runner, "run", side_effect=capture):
        runner.build(archive, validate_only=True, no_cache=True)
    assert len(commands) == 3
    assert commands[0][1:] == (
        "tests/rom_motion_packs.py", "--source-only", "--asset-zip", str(archive)
    )
    assert commands[1] == (
        sys.executable, "tools/verify_private_clan.py", str(archive)
    )
    assert commands[2] == (
        sys.executable, "tools/verify_runtime_assets.py", str(archive)
    )
    assert not (work / "mii-ds.nds").exists()

    commands.clear()
    fake_rom = work / "mii-ds.nds"
    fake_rom.write_bytes(b"not a real ROM: test commands are mocked")
    validation_calls = []

    def validate(archive_arg, dest=None):
        validation_calls.append(dest)
        return 0

    def capture_with_new_rom(*command):
        capture(*command)
        if command and str(command[0]) == "make":
            fake_rom.write_bytes(b"new synthetic ROM after make")

    with patch.object(runner, "run", side_effect=capture_with_new_rom), \
         patch.object(runner, "validate", side_effect=validate), \
         patch.object(runner, "ROM", fake_rom):
        runner.build(archive, jobs=3, no_cache=True)
    assert validation_calls == [None, ROOT]
    assert commands[0][1:3] == ("tests/rom_motion_packs.py", "--source-only")
    assert (sys.executable, "tools/verify_private_clan.py", str(archive)) in commands
    assert (sys.executable, "tools/verify_runtime_assets.py", str(archive)) in commands
    assert commands.index((sys.executable, "tools/verify_private_clan.py", str(archive))) < commands.index(("make", "-j3"))
    assert commands.index((sys.executable, "tools/verify_runtime_assets.py", str(archive))) < commands.index(("make", "-j3"))
    assert ("make", "-j3") in commands
    renderer_command = (sys.executable, "tools/test_original_render.py",
                        "--asset-zip", str(archive))
    assert renderer_command in commands
    assert commands.index(renderer_command) < commands.index(("make", "-j3"))
    assert (sys.executable, "tests/rom_all_assets.py", str(fake_rom),
            "--asset-zip", str(archive)) in commands
    assert (sys.executable, "tests/rom_arm_sections.py", str(fake_rom)) in commands
    assert (sys.executable, "tests/rom_body_models.py", str(fake_rom)) in commands
    assert (sys.executable, "tests/rom_motion_packs.py", str(fake_rom),
            "--asset-zip", str(archive)) in commands
    assert commands.index(("make", "-j3")) < commands.index((
        sys.executable, "tests/rom_all_assets.py", str(fake_rom),
        "--asset-zip", str(archive)))
    assert not any(any("upload" in arg or "github" in arg for arg in cmd)
                   for cmd in commands)

    # A mismatched source-derived CLAN table must stop the build before
    # restoring Nintendo assets or invoking make.
    failure_commands = []
    def reject_bad_clan(*command):
        failure_commands.append(tuple(map(str, command)))
        if len(command) > 1 and str(command[1]) == "tools/verify_private_clan.py":
            raise subprocess.CalledProcessError(1, command)
    with patch.object(runner, "run", side_effect=reject_bad_clan), \
         patch.object(runner, "validate", wraps=runner.validate) as verifier:
        try:
            runner.build(archive, jobs=3, no_cache=True)
            raise AssertionError("mismatched CLAN tables did not prevent build")
        except subprocess.CalledProcessError:
            pass
    assert len(failure_commands) == 2
    assert not any(cmd and cmd[0] == "make" for cmd in failure_commands)

    def reject_bad_resource(*command):
        failure_commands.append(tuple(map(str, command)))
        if len(command) > 1 and str(command[1]) == "tools/verify_runtime_assets.py":
            raise subprocess.CalledProcessError(1, command)
    failure_commands.clear()
    with patch.object(runner, "run", side_effect=reject_bad_resource):
        try:
            runner.build(archive, jobs=3, no_cache=True)
            raise AssertionError("missing UI sprite did not prevent build")
        except subprocess.CalledProcessError:
            pass
    assert len(failure_commands) == 3
    assert not any(cmd and cmd[0] == "make" for cmd in failure_commands)

    with patch.object(runner, "run", side_effect=capture):
        try:
            runner.build(work / "missing.zip", validate_only=True)
            raise AssertionError("missing ZIP did not fail")
        except ValueError:
            pass

print("PASS: private ZIP validation, CLAN and NitroFS UI parity before extraction/build, full ROM gates and missing ZIP rejection")
