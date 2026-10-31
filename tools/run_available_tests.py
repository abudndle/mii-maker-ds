#!/usr/bin/env python3
"""Run the source-only checks that require neither Nintendo assets nor BlocksDS."""
import argparse
import os
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parents[1]
parser = argparse.ArgumentParser()
parser.add_argument("--cc", default=os.environ.get("CC", "cc"))
parser.add_argument("--no-sanitizers", action="store_true")
args = parser.parse_args()

flags = ["-std=c11", "-Wall", "-Wextra", "-Werror", "-g", "-I", str(root / "source")]
if not args.no_sanitizers:
    flags += ["-fsanitize=address,undefined", "-fno-omit-frame-pointer"]

env = os.environ.copy()
env["ASAN_OPTIONS"] = "detect_leaks=0"

with tempfile.TemporaryDirectory(prefix="mii-ds-portable-") as temporary:
    for name in ("animation", "gui_tween"):
        target = Path(temporary) / name
        subprocess.run(
            [args.cc, *flags, str(root / "tests" / (name + ".c")),
             str(root / "source" / (name + ".c")), "-o", str(target)],
            check=True,
        )
        subprocess.run([str(target)], env=env, check=True)

subprocess.run([sys.executable, str(root / "tools/test_build_preflight.py")], check=True)
print("PASS: all three source-only checks")
