#!/usr/bin/env python3
"""Verify checked-in numeric CLAN animation tables against a private asset ZIP.

Read original BCLAN clips in memory; never extract, publish, or commit original
Nintendo assets. Compare numeric Q16.16 C keyframes, not whitespace/comments.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from clan_keyframes import inventory
from generate_clan_home_visual import generate as generate_home
from generate_clan_dialog import generate as generate_dialog
from generate_clan_editor import generate as generate_editor
from generate_clan_adjust import generate as generate_adjust

SOURCE = Path(__file__).resolve().parents[1] / "source"
EXPECTED_CLIPS = 327
EXPECTED_CHANNELS = 13366
GENERATORS = (
    ("clan_home_generated.h", generate_home),
    ("clan_dialog_generated.h", generate_dialog),
    ("clan_editor_generated.h", generate_editor),
    ("clan_adjust_generated.h", generate_adjust),
)
ARRAY = re.compile(
    r"\bstatic\s+const\s+MdsClanKey\s+([A-Za-z_]\w*)\s*\[\s*\]\s*=\s*\{(.*?)\}\s*;",
    re.S,
)
KEY = re.compile(r"\{\s*(-?\d+)\s*,\s*(-?\d+)\s*,\s*(-?\d+)\s*\}")


def arrays(content):
    result = {}
    for match in ARRAY.finditer(content):
        name, raw = match.groups()
        if name in result:
            raise ValueError("duplicate CLAN table: " + name)
        keys = [tuple(map(int, key.groups())) for key in KEY.finditer(raw)]
        residue = KEY.sub("", raw)
        if not keys or re.sub(r"[\s,]", "", residue):
            raise ValueError("invalid numeric key list: " + name)
        result[name] = keys
    if not result:
        raise ValueError("no CLAN tables in header")
    return result


def verify_tables(catalog, source=SOURCE, generators=GENERATORS):
    if catalog.get("clip_count") != EXPECTED_CLIPS or catalog.get("channel_count") != EXPECTED_CHANNELS:
        raise ValueError("private CLAN inventory differs from expected 327 clips / 13366 channels")
    report = {}
    for filename, generator in generators:
        expected = arrays(generator(catalog))
        actual = arrays((source / filename).read_text(encoding="utf-8"))
        if actual.keys() != expected.keys():
            raise ValueError(f"{filename}: missing or unexpected numeric CLAN channel tables")
        for name, keys in expected.items():
            if keys != actual[name]:
                raise ValueError(f"{filename}: source CLAN keyframes differ: {name}")
        canonical = json.dumps(expected, sort_keys=True, separators=(",", ":")).encode("ascii")
        report[filename] = {
            "channels": len(expected),
            "keys": sum(map(len, expected.values())),
            "numeric_sha256": hashlib.sha256(canonical).hexdigest(),
        }
    if sum(section["channels"] for section in report.values()) != 41:
        raise ValueError("expected exactly 41 checked-in GUI CLAN channels")
    return report


def check(archive, source=SOURCE):
    catalog = inventory(archive)
    return {
        "clips": catalog["clip_count"], "channels": catalog["channel_count"],
        "headers": verify_tables(catalog, source),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_zip", type=Path)
    parser.add_argument("--source-dir", type=Path, default=SOURCE)
    parser.add_argument("--report", type=Path, help="optional metadata-only report output")
    args = parser.parse_args()
    try:
        summary = check(args.private_zip, args.source_dir)
        if args.report:
            args.report.write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    except (OSError, ValueError, KeyError, TypeError, EOFError) as exc:
        parser.exit(1, f"FAIL: private CLAN table parity: {exc}\n")
    print("PASS: %d original CLAN clips / %d channels / %d committed animation tables" % (
        summary["clips"], summary["channels"],
        sum(entry["channels"] for entry in summary["headers"].values()),
    ))


if __name__ == "__main__":
    main()
