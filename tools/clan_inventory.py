"""Read-only validation of original CLAN UI animation files.

This inventories private source assets; it does not redistribute animation bytes.
"""
import argparse
import json
import struct
import zipfile
from collections import Counter
from pathlib import PurePosixPath

PREFIX = "assets/decoded/layout/"

def parse_clan(data):
    if len(data) < 28 or data[:4] != b"CLAN":
        raise ValueError("missing CLAN header")
    if data[4:6] == b"\xff\xfe":
        endian = "<"
    elif data[4:6] == b"\xfe\xff":
        endian = ">"
    else:
        raise ValueError("invalid byte order")
    header = struct.unpack_from(endian + "H", data, 6)[0]
    version, file_size, blocks = struct.unpack_from(endian + "IIH", data, 8)
    if header < 20 or header > len(data) or file_size != len(data) or not 1 <= blocks <= 32:
        raise ValueError("invalid CLAN length/header")
    position, tags = header, []
    for _ in range(blocks):
        if position + 8 > len(data):
            raise ValueError("truncated block")
        tag = data[position:position + 4].decode("ascii")
        length = struct.unpack_from(endian + "I", data, position + 4)[0]
        if length < 8 or position + length > len(data):
            raise ValueError("out-of-bounds CLAN block")
        tags.append(tag)
        position += length
    if position != len(data) or "pai1" not in tags:
        raise ValueError("invalid section coverage or missing pai1")
    return {"version": version, "bytes": len(data), "sections": tags}

def inventory(resource_zip):
    results, counts = [], Counter()
    with zipfile.ZipFile(resource_zip) as archive:
        for entry in archive.infolist():
            name = entry.filename
            if not name.startswith(PREFIX) or not name.lower().endswith(".bclan"):
                continue
            parts = PurePosixPath(name).parts
            if ".." in parts or entry.is_dir() or entry.file_size > 4 * 1024 * 1024:
                raise ValueError("unsafe entry: " + name)
            if len(parts) < 5 or parts[-2] != "anim":
                raise ValueError("unexpected path: " + name)
            parsed = parse_clan(archive.read(entry))
            counts[parts[3]] += 1
            results.append({"path": name, "archive": parts[3], **parsed})
    if not results:
        raise ValueError("no BCLAN data present")
    return {"count": len(results), "archives": dict(sorted(counts.items())),
            "animations": sorted(results, key=lambda row: row["path"])}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("resource_zip")
    parser.add_argument("--expect", type=int, default=327)
    parser.add_argument("--output", help="optional metadata-only JSON output")
    args = parser.parse_args()
    report = inventory(args.resource_zip)
    if report["count"] != args.expect:
        parser.error("expected %d CLAN files, found %d" % (args.expect, report["count"]))
    if args.output:
        with open(args.output, "w", encoding="utf-8") as output:
            json.dump(report, output, indent=2)
    print("PASS: %d BCLAN files across %d archives" %
          (report["count"], len(report["archives"])))
    for name, count in report["archives"].items():
        print("  %s: %d" % (name, count))

if __name__ == "__main__":
    main()
