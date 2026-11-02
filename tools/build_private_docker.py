#!/usr/bin/env python3
"""Compile a PRIVATE DS ROM with the official BlocksDS Docker image.

Python validation runs on the host: the official slim SDK image does NOT
contain Python. Only ARM9/ARM7 compilation and ROM assembly run in Docker.
The private resource ZIP is read only by Python on the owner's computer and
is NEVER mounted into Docker, committed, or uploaded.
"""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import subprocess
import sys

from build_private import ROOT, ROM, check_zip, run
from restore_asset_zip import validate
from private_rom_freshness import clear_old_rom, require_new_rom

IMAGE = "skylyrac/blocksds:slim-latest"


def command(archive, root=ROOT, image=IMAGE, jobs=2, environ=None):
    env = os.environ if environ is None else environ
    root = Path(root).resolve(strict=True)
    archive = Path(archive).expanduser().resolve(strict=True)
    if not archive.is_file() or archive.stat().st_size <= 0:
        raise ValueError("private ZIP does not exist or is empty")
    if not 1 <= jobs <= 16:
        raise ValueError("jobs must be between 1 and 16")
    if not image or any(c.isspace() for c in image) or image.startswith("-"):
        raise ValueError("invalid Docker image identifier")
    if root == archive.parent:
        raise ValueError("keep private resource ZIP outside the project root")
    args = [
        "docker", "run", "--rm", "--network", "none",
        "--security-opt", "no-new-privileges", "--cap-drop", "ALL",
        "--workdir", "/work", "--entrypoint", "make",
        "--mount", f"type=bind,source={root},target=/work",
    ]
    if hasattr(os, "getuid") and env.get("MDS_DOCKER_RUN_AS_ROOT") != "1":
        args += ["--user", f"{os.getuid()}:{os.getgid()}"]
    args += [image, "SDK_STAGE=1", f"-j{jobs}", "mii-ds.nds"]
    return args


def build(archive, jobs=2, validate_only=False, image=IMAGE, no_cache=False):
    archive = Path(archive).expanduser().resolve(strict=True)
    # Fail missing SDK access before extracting any owner-private content.
    cmd = command(archive, image=image, jobs=jobs)
    if not validate_only and shutil.which("docker") is None:
        raise ValueError("Docker is not installed; see official BlocksDS Docker documentation")
    check_zip(archive,use_cache=not no_cache)
    if validate_only:
        print("PASS: private original archives, model motions, CLAN and NitroFS UI verified")
        print("No original resources extracted and no ROM generated")
        return
    # Original resources are restored locally, never exposed via a mounted ZIP.
    if validate(archive, ROOT):
        raise ValueError("private ZIP extraction failed")
    run(sys.executable, "tools/check_assets.py")
    run(sys.executable, "tools/validate_body_models.py")
    if shutil.which("gcc") or shutil.which("clang") or shutil.which("cc"):
        run(sys.executable, "tools/test_original_render.py", "--asset-zip", archive)
    else:
        print("NOTE: host C compiler unavailable; original renderer host check skipped")
    # Makefile SDK_STAGE avoids Python-dependent host preflight in slim container.
    print("+ BlocksDS compiler stage inside offline Docker container", flush=True)
    clear_old_rom(ROM)
    subprocess.run(cmd, cwd=ROOT, check=True)
    run(sys.executable, "tools/fix_nds_regions.py", ROM)
    require_new_rom(ROM)
    for extra in [
        ("tests/rom_regions.py",),
        ("tests/rom_nitrofs_assets.py", ROM),
        ("tests/rom_all_assets.py", ROM, "--asset-zip", archive),
        ("tests/rom_body_models.py", ROM),
        ("tests/rom_motion_packs.py", ROM, "--asset-zip", archive),
        ("tests/rom_arm_sections.py", ROM),
    ]:
        run(sys.executable, *extra)
    from private_build_provenance import write_provenance
    write_provenance(ROM, archive, ROOT / "build/private-build-provenance.json")
    digest = hashlib.sha256(ROM.read_bytes()).hexdigest()
    print("PASS: original-resource ROM passed packaged payload and ARM sections")
    print("SHA-256:", digest)
    print("Keep this private ROM off public GitHub and release artifacts")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_zip", type=Path)
    parser.add_argument("--jobs", type=int, default=2)
    parser.add_argument("--image", default=IMAGE)
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--no-cache", action="store_true",
                        help="force full source and private resource validation")
    parser.add_argument("--dry-run", action="store_true",
                        help="show compiler invocation without running or reading ZIP bytes")
    args = parser.parse_args()
    try:
        cmd = command(args.private_zip, image=args.image, jobs=args.jobs)
        if args.dry_run:
            print("Compiler invocation prepared (private ZIP stays on host):")
            print(" ".join(shlex_quote(part) for part in cmd))
            return 0
        build(args.private_zip, args.jobs, args.validate_only, args.image,
              args.no_cache)
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f"FAIL: private BlocksDS Docker build: {exc}\n")
    return 0


def shlex_quote(item):
    import shlex
    return shlex.quote(str(item))


if __name__ == "__main__":
    raise SystemExit(main())
