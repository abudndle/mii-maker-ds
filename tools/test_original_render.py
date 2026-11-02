#!/usr/bin/env python3
"""Host integration for sampled ANI1 and original full-frame MSP1 Mii renders.

Requires an authorized private CFL, male/female body meshes and animations.
The tests never publish or retain private resources outside a temporary directory.
This is NOT DS emulator or hardware acceptance.
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
MOTION_ASSET_NAMES = (
    "nitrofiles/cfl/CFL_Res.dat",
    "nitrofiles/models/MaleBody.bin",
    "nitrofiles/models/MaleBody.msp",
    "nitrofiles/models/FemaleBody.bin",
    "nitrofiles/models/FemaleBody.msp",
)
REQUIRED = tuple(dict.fromkeys((*ASSET_NAMES, *MOTION_ASSET_NAMES)))
RENDER_MODULES = ("head", "view", "cfl_resource", "avatar", "status")
SUITES = (
    ("sampled", "animation.c", ("animation", *RENDER_MODULES), ASSET_NAMES),
    ("original_msp1", "motion_render.c", ("motion", *RENDER_MODULES), MOTION_ASSET_NAMES),
)


def run(cc: str, asset_zip: Path | None, compile_only: bool = False) -> None:
    with tempfile.TemporaryDirectory(prefix="mii-original-render-") as temp:
        folder = Path(temp)
        resources = {}
        if not compile_only:
            if asset_zip is not None:
                with zipfile.ZipFile(asset_zip) as archive:
                    for name in REQUIRED:
                        # Only exact, known resource names; no arbitrary extraction.
                        target = folder / name
                        target.parent.mkdir(parents=True, exist_ok=True)
                        target.write_bytes(archive.read(name))
                        resources[name] = target
            else:
                resources = {name: ROOT / name for name in REQUIRED}

            missing = [name for name, path in resources.items() if not path.is_file()]
            if missing:
                raise FileNotFoundError("Missing private original resources: " + ", ".join(missing))

        for suite_name, source, modules, required in SUITES:
            executable = folder / ("original_render_" + suite_name)
            command = [
                cc, "-std=c11", "-Wall", "-Wextra", "-O1", "-g",
                "-I", str(ROOT / "source"),
                str(ROOT / "tests" / source),
                *(str(ROOT / "source" / (module + ".c")) for module in modules),
                "-lm", "-o", str(executable),
            ]
            subprocess.run(command, check=True)
            if not compile_only:
                subprocess.run([str(executable), *(str(resources[name]) for name in required)],
                               check=True, timeout=180)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cc", default=os.getenv("CC", "cc"))
    parser.add_argument("--compile-only", action="store_true",
                        help="compile/link both private-resource integration suites without assets")
    parser.add_argument("--asset-zip", type=Path,
                        help="private ZIP containing source CFL, BOD2, ANI1 and MSP1 resources")
    args = parser.parse_args()
    try:
        run(args.cc, args.asset_zip, args.compile_only)
    except (OSError, KeyError, ValueError, subprocess.CalledProcessError,
            subprocess.TimeoutExpired, zipfile.BadZipFile) as exc:
        parser.exit(1, f"FAIL: original renderer integration: {exc}\n")
    print("PASS: sampled ANI1 and original MSP1 full-body renderer links"
          if args.compile_only else
          "PASS: original male/female ANI1 and MSP1 full-body pose rendering integration")


if __name__ == "__main__":
    main()
