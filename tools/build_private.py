#!/usr/bin/env python3
"""Build and verify Mii Maker DS locally from your own private asset archive.

Examples:
  python3 tools/build_private.py MiiMaker_DS_Resources.zip --validate-only
  python3 tools/build_private.py MiiMaker_DS_Resources.zip

This script never uploads or commits original Nintendo resources.
"""
import argparse
import hashlib
import subprocess
import sys
from pathlib import Path

from restore_asset_zip import validate
from private_validation_cache import cache_hit, cache_store

ROOT = Path(__file__).resolve().parents[1]
ROM = ROOT / "mii-ds.nds"


def run(*command):
    print("+", " ".join(map(str, command)), flush=True)
    subprocess.run([str(c) for c in command], cwd=ROOT, check=True)


def check_zip(archive: Path, use_cache: bool = True) -> None:
    if use_cache and cache_hit(ROOT,archive):
        print('PASS: unchanged private resource ZIP and validation source; reusing prior full verification')
        return
    if validate(archive):
        raise ValueError("private original-resource archive is invalid")
    # Source-only parser validates every animation frame and matching 53-clip
    # catalogs without extracting or needing the Nintendo DS compiler.
    run(sys.executable, "tests/rom_motion_packs.py", "--source-only",
        "--asset-zip", archive)
    # Reject stale/incorrect original GUI animation tables before restoring
    # proprietary files or attempting the BlocksDS build. Reads private ZIP
    # in memory and compares 41 committed Q16.16 keyframe tracks.
    run(sys.executable, "tools/verify_private_clan.py", archive)
    # Validate every source-referenced editor icon and all NitroFS UI bitmaps/sprites.
    # This gate runs before private resource restoration and compiler invocation.
    run(sys.executable, "tools/verify_runtime_assets.py", archive)
    # Only fully successful checks may produce the private, gitignored stamp.
    cache_store(ROOT,archive)


def build(archive: Path, validate_only=False, jobs=2, no_cache=False) -> None:
    if not archive.is_file():
        raise ValueError("private resource archive does not exist: " + str(archive))
    check_zip(archive,use_cache=not no_cache)
    if validate_only:
        print("PASS: private ZIP, original motion catalogs, 41 GUI CLAN tables, and every UI/sprite resource validated.")
        print("No assets were extracted and no ROM was built.")
        return

    # Restores only locally. nitrofiles/ and assets/ are gitignored.
    if validate(archive, ROOT):
        raise ValueError("could not restore the private resource archive")
    run(sys.executable, "tools/check_assets.py")
    run(sys.executable, "tools/validate_body_models.py")
    # Use the user's private assets to execute the real C renderer on host:
    # all male/female original poses and four discrete camera angles.
    run(sys.executable, "tools/test_original_render.py", "--asset-zip", archive)
    run(sys.executable, "tools/build_preflight.py")
    run("make", "-j" + str(jobs))
    if not ROM.is_file() or not ROM.stat().st_size:
        raise ValueError("BlocksDS did not produce mii-ds.nds")

    # Release gate: verify both native binaries and every packed original
    # resource before treating the newly built ROM as usable.
    run(sys.executable, "tests/rom_regions.py")
    run(sys.executable, "tests/rom_nitrofs_assets.py", ROM)
    run(sys.executable, "tests/rom_all_assets.py", ROM, "--asset-zip", archive)
    run(sys.executable, "tests/rom_body_models.py", ROM)
    run(sys.executable, "tests/rom_motion_packs.py", ROM, "--asset-zip", archive)
    run(sys.executable, "tests/rom_arm_sections.py", ROM)

    from private_build_provenance import write_provenance
    write_provenance(ROM, archive, ROOT / "build/private-build-provenance.json")
    digest = hashlib.sha256(ROM.read_bytes()).hexdigest()
    print("PASS: locally built ROM: " + str(ROM))
    print("SHA-256: " + digest)
    print("The ROM embeds private Nintendo resources; do not publish it.")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("asset_zip", type=Path,
                        help="path to your privately extracted Mii Maker resource ZIP")
    parser.add_argument("--no-cache", action="store_true",
                        help="re-run all private resource, motion and CLAN validators")
    parser.add_argument("--validate-only", action="store_true",
                        help="validate archive and original animations without extracting or building")
    parser.add_argument("--jobs", type=int, default=2,
                        help="number of parallel BlocksDS build jobs (1 to 16; default 2)")
    args = parser.parse_args()
    if not 1 <= args.jobs <= 16:
        parser.error("--jobs must be between 1 and 16")
    try:
        build(args.asset_zip.expanduser().resolve(), args.validate_only, args.jobs,
              args.no_cache)
    except (OSError, ValueError, subprocess.CalledProcessError) as error:
        print("FAIL: private build: " + str(error), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
