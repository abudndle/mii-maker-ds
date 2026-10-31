#!/usr/bin/env python3
"""Regression tests for safe private ZIP restoration; fictional bytes only."""
import os
import sys
import tempfile
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tools"))
from restore_asset_zip import REQUIRED, validate


with tempfile.TemporaryDirectory(prefix="mii-restore-safety-") as temp:
    temp = Path(temp)
    archive = temp / "synthetic.zip"
    with ZipFile(archive, "w") as z:
        for item in REQUIRED:
            z.writestr(item, b"fictional fixture")
    assert validate(archive) == 0
    normal = temp / "normal"
    normal.mkdir()
    assert validate(archive, normal) == 0
    assert (normal / "nitrofiles/cfl/CFL_Res.dat").read_bytes() == b"fictional fixture"

    outside = temp / "outside"
    outside.mkdir()
    linked = temp / "linked"
    linked.mkdir()
    try:
        (linked / "nitrofiles").symlink_to(outside, target_is_directory=True)
    except (OSError, NotImplementedError):
        print("SKIP: symlink creation is restricted on this platform")
    else:
        assert validate(archive, linked) == 1
        assert not (outside / "cfl/CFL_Res.dat").exists()

        # Even a single file link must not be overwritten through restore.
        file_link = temp / "file-link"
        (file_link / "nitrofiles/cfl").mkdir(parents=True)
        victim = temp / "victim"
        victim.write_text("must not be overwritten")
        (file_link / "nitrofiles/cfl/CFL_Res.dat").symlink_to(victim)
        assert validate(archive, file_link) == 1
        assert victim.read_text() == "must not be overwritten"

    traversal = temp / "traversal.zip"
    with ZipFile(traversal, "w") as z:
        for item in REQUIRED:
            z.writestr(item, b"fictional fixture")
        z.writestr("nitrofiles/../escape.dat", b"unsafe")
    assert validate(traversal, temp / "reject") == 1
    assert not (temp / "escape.dat").exists()

print("PASS: private-resource extractor rejects unsafe ZIP paths and symlink destinations")
