#!/usr/bin/env python3
"""Run the complete private original-resource ROM acceptance sequence.

Never uploads proprietary resources or the generated ROM.
"""
import argparse
import hashlib
import json
import subprocess
import sys
import os
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def commands(archive, docker=False, emulator=None):
    archive = str(Path(archive).expanduser().resolve())
    build_script = "tools/build_private_docker.py" if docker else "tools/build_private.py"
    steps = [[sys.executable, build_script, archive, "--no-cache"]]
    if emulator:
        steps.append([str(emulator), str(ROOT / "mii-ds.nds")])
    return steps


def make_report(rom, archive, emulator_launched=False):
    rom, archive = Path(rom), Path(archive)
    if rom.is_symlink() or not rom.is_file() or rom.stat().st_size == 0:
        raise ValueError("private ROM evidence requires a nonempty regular ROM file")
    if archive.is_symlink() or not archive.is_file() or archive.stat().st_size == 0:
        raise ValueError("private ROM evidence requires a nonempty regular resource archive")
    return {
        "private_rom_sha256": hashlib.sha256(rom.read_bytes()).hexdigest(),
        "private_rom_bytes": rom.stat().st_size,
        "archive_sha256": hashlib.sha256(archive.read_bytes()).hexdigest(),
        "emulator_launched": bool(emulator_launched),
        "gameplay_verified": False,
    }


def write_report(report_path, report):
    """Replace acceptance evidence atomically to avoid partial JSON files."""
    report_path = Path(report_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=report_path.parent,
                                         prefix=".private-acceptance-", suffix=".tmp",
                                         delete=False) as output:
            temporary = Path(output.name)
            output.write(json.dumps(report, indent=2, sort_keys=True) + "\n")
            output.flush()
            os.fsync(output.fileno())
        os.replace(temporary, report_path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def launch_emulator(command, report, report_path):
    """Persist successful process creation before waiting for emulator exit."""
    process = subprocess.Popen(command, cwd=ROOT)
    report["emulator_launched"] = True
    write_report(report_path, report)
    exit_code = process.wait()
    if exit_code != 0:
        raise subprocess.CalledProcessError(exit_code, command)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("--docker", action="store_true")
    parser.add_argument("--emulator", help="optional melonDS executable; manual gameplay inspection is still required")
    args = parser.parse_args()
    if not args.archive.is_file():
        parser.error("private resource archive not found")
    if args.emulator:
        emulator_path = Path(args.emulator).expanduser().resolve()
        if not emulator_path.is_file():
            parser.error("emulator executable not found; provide an existing melonDS executable path")
        args.emulator = str(emulator_path)
    build_command = commands(args.archive, docker=args.docker)[0]
    print("+", " ".join(build_command), flush=True)
    subprocess.run(build_command, cwd=ROOT, check=True)
    rom = ROOT / "mii-ds.nds"
    if rom.is_symlink() or not rom.is_file() or rom.stat().st_size == 0:
        raise ValueError("private ROM build did not produce a valid ROM")
    report = make_report(rom, args.archive, emulator_launched=False)
    report_path = ROOT / "build" / "private-acceptance-report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("PASS: private ROM build and packaged resource acceptance checks completed")
    if args.emulator:
        emulator_command = commands(args.archive, docker=args.docker, emulator=args.emulator)[1]
        print("+", " ".join(emulator_command), flush=True)
        launch_emulator(emulator_command, report, report_path)
    if args.emulator:
        print("NOTE: emulator process started and exited successfully; manual gameplay and save-persistence acceptance remain required")
    else:
        print("NOTE: emulator was not run")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
