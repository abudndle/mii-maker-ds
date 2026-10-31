#!/usr/bin/env python3
"""Asset-free regression checks for the private, local-only ROM build helper."""
import io
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
        runner.build(archive, validate_only=True)
    assert len(commands) == 1
    assert commands[0][1:] == (
        "tests/rom_motion_packs.py", "--source-only", "--asset-zip", str(archive)
    )
    assert not (work / "mii-ds.nds").exists()

    commands.clear()
    fake_rom = work / "mii-ds.nds"
    fake_rom.write_bytes(b"not a real ROM: test commands are mocked")
    validation_calls = []

    def validate(archive_arg, dest=None):
        validation_calls.append(dest)
        return 0

    with patch.object(runner, "run", side_effect=capture), \
         patch.object(runner, "validate", side_effect=validate), \
         patch.object(runner, "ROM", fake_rom):
        runner.build(archive, jobs=3)
    assert validation_calls == [None, ROOT]
    assert commands[0][1:3] == ("tests/rom_motion_packs.py", "--source-only")
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

    with patch.object(runner, "run", side_effect=capture):
        try:
            runner.build(work / "missing.zip", validate_only=True)
            raise AssertionError("missing ZIP did not fail")
        except ValueError:
            pass

print("PASS: private ZIP validation-only, local build order, full ROM gate, and missing ZIP rejection")
