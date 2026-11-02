#!/usr/bin/env python3
"""Run the complete private original-resource ROM acceptance sequence.

Never uploads proprietary resources or the generated ROM.
"""
import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def commands(archive, docker=False, emulator=None):
    archive = str(Path(archive).expanduser().resolve())
    build_script = "tools/build_private_docker.py" if docker else "tools/build_private.py"
    steps = [[sys.executable, build_script, archive, "--no-cache"]]
    if emulator:
        steps.append([str(emulator), str(ROOT / "mii-ds.nds")])
    return steps


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--emulator", help="optional melonDS executable; manual gameplay inspection is still required")
    args = parser.parse_args()
    if not args.archive.is_file():
        parser.error("private resource archive not found")
    for command in commands(args.archive, docker=args.docker, emulator=args.emulator):
        print("+", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)
    print("PASS: private ROM build and packaged resource acceptance checks completed")
    if args.emulator:
        print("NOTE: emulator was launched; manual gameplay and save-persistence acceptance remain required")
    else:
        print("NOTE: emulator was not run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
