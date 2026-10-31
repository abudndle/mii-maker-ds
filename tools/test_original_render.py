#!/usr/bin/env python3
"""Render original male/female Mii sample poses on the host before a DS build.

Requires private CFL + ANI resources. Never uploads or embeds those assets.
This is an integration test, not an emulator or a Nintendo DS build.
"""
import argparse
import os
import subprocess
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSET_NAMES = (
    "nitrofiles/cfl/CFL_Res.dat",
    "nitrofiles/models/MaleBody.ani",
    "nitrofiles/models/FemaleBody.ani",
)
MODULES = ("animation", "head", "cfl_resource", "avatar", "status")


def run(cc: str, asset_zip: Path | None) -> None:
    with tempfile.TemporaryDirectory(prefix="mii-original-render-") as temp:
        folder = Path(temp)
        if asset_zip is not None:
            with zipfile.ZipFile(asset_zip) as archive:
                for name in ASSET_NAMES:
                    # Extract only known paths, never arbitrary ZIP member names.
                    target = folder / name
                    target.parent.mkdir(parents=True, exist_ok=True)
                    target.write_bytes(archive.read(name))
            assets = [folder / name for name in ASSET_NAMES]
        else:
            assets = [ROOT / name for name in ASSET_NAMES]

        missing = [str(p) for p in assets if not p.is_file()]
        if missing:
            raise FileNotFoundError("Missing private original resources: " + ", ".join(missing))

        executable = folder / "original_render_test"
        command = [
            cc, "-std=c11", "-Wall", "-Wextra", "-O1", "-g",
            "-I", str(ROOT / "source"),
            str(ROOT / "tests/animation.c"),
            *(str(ROOT / "source" / (module + ".c")) for module in MODULES),
            "-lm", "-o", str(executable),
        ]
        subprocess.run(command, check=True)
        subprocess.run([str(executable), *(str(p) for p in assets)],
                       check=True, timeout=180)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", default=os.getenv("CC", "cc"))
    parser.add_argument("--asset-zip", type=Path,
                        help="private ZIP containing the three NitroFS originals")
    args = parser.parse_args()
    try:
        run(args.cc, args.asset_zip)
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, zipfile.BadZipFile) as exc:
        parser.exit(1, f"FAIL: original renderer integration: {exc}\n")
    print("PASS: original male/female pose rendering integration")


if __name__ == "__main__":
    main()
