#!/usr/bin/env python3
"""Prevent accidental publication of ROMs embedding private Nintendo resources."""
from pathlib import Path
import re

workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/build-nds.yml").read_text()
if not re.search(r"(?m)^\s+publish_rom_artifact:\s*$", workflow):
    raise SystemExit("FAIL: ROM artifact opt-in input missing")
if not re.search(r"(?ms)^\s+publish_rom_artifact:\s*\n(?:[ \t]+[^\n]*\n)*?[ \t]+default:\s*false\s*$", workflow):
    raise SystemExit("FAIL: ROM artifact publishing must default to false")
lines = workflow.splitlines()
for i, line in enumerate(lines):
    if "uses: actions/upload-artifact@" not in line:
        continue
    # Require a job-step conditional immediately before the upload action.
    previous = "\n".join(lines[max(0, i-8):i])
    if not re.search(r"(?m)^\s+if:\s*\$\{\{\s*inputs\.publish_rom_artifact\s*==\s*true\s*\}\}\s*$", previous):
        raise SystemExit("FAIL: ROM artifact upload is not explicitly opt-in")
if "uses: actions/upload-artifact@" not in workflow:
    raise SystemExit("FAIL: expected ROM upload control missing")
print("PASS: built ROM artifact publishing is explicitly opt-in and disabled by default")
