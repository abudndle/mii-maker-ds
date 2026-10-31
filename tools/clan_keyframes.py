#!/usr/bin/env python3
"""Extract numeric CLAN animation keyframes from the user's private ZIP.

No copyrighted image/model/audio payloads are exported. Float keys store
(frame,value,tangent); CLVI and CLTP keys store (frame,unsigned value).
"""
import argparse
import json
import math
import struct
from pathlib import PurePosixPath
from zipfile import ZipFile

KINDS = {"CLPA", "CLMC", "CLVC", "CLVI", "CLTP"}
PREFIX = "assets/decoded/layout/"


def parse(data):
    if len(data) < 40 or data[:4] != b"CLAN":
        raise ValueError("invalid CLAN header")
    order = {b"\xff\xfe": "<", b"\xfe\xff": ">"}.get(bytes(data[4:6]))
    if not order:
        raise ValueError("unsupported byte order")

    def bounds(pos, length, end=len(data)):
        if pos < 0 or length < 0 or pos > end or length > end - pos:
            raise ValueError("out-of-bounds animation reference")

    def take(fmt, pos, end=len(data)):
        size = struct.calcsize(order + fmt)
        bounds(pos, size, end)
        return struct.unpack_from(order + fmt, data, pos)

    header, = take("H", 6)
    file_size, = take("I", 12)
    sections, = take("H", 16)
    if header < 20 or header > len(data) or file_size != len(data) or not 1 <= sections <= 16:
        raise ValueError("invalid CLAN size or section count")
    offset, pai = header, None
    for _ in range(sections):
        bounds(offset, 8)
        size, = take("I", offset + 4)
        if size < 8:
            raise ValueError("short section")
        bounds(offset, size)
        if data[offset:offset+4] == b"pai1":
            if pai is not None:
                raise ValueError("duplicate pai1")
            pai = (offset, offset + size)
        offset += size
    if pai is None or offset != len(data):
        raise ValueError("missing pai1 or incomplete section coverage")
    start, end = pai
    bounds(start, 20, end)
    frames, = take("H", start + 8, end)
    looping = data[start + 10]
    count, = take("H", start + 14, end)
    off, = take("I", start + 16, end)
    table = start + off
    if count > 4096 or off < 20:
        raise ValueError("bad pane table")
    bounds(table, count * 4, end)
    tracks = []
    for i in range(count):
        rel, = take("I", table + 4*i, end)
        entry = start + rel
        if entry < table + count*4:
            raise ValueError("pane overlaps table")
        bounds(entry, 28, end)
        raw = data[entry:entry+20].split(b"\x00", 1)[0]
        if not raw or any(c < 32 or c > 126 for c in raw):
            raise ValueError("invalid pane name")
        name = raw.decode("ascii")
        rel, = take("I", entry + 24, end)
        tag = entry + rel
        if rel < 28:
            raise ValueError("invalid pane tag")
        bounds(tag, 8, end)
        kind = bytes(data[tag:tag+4]).decode("ascii", "replace")
        if kind not in KINDS:
            raise ValueError("unsupported CLAN tag " + kind)
        n = data[tag+4]
        if n > 64:
            raise ValueError("excessive channels")
        bounds(tag+8, n*4, end)
        for j in range(n):
            rel, = take("I", tag+8+j*4, end)
            cur = tag + rel
            if rel < 8 + n*4:
                raise ValueError("channel overlaps table")
            bounds(cur, 12, end)
            index, target, dtype, key_count, unused, key_off = take("BBHHHI", cur, end)
            if dtype not in (1, 2) or not 1 <= key_count <= 1024 or key_off < 12:
                raise ValueError("invalid key descriptor")
            if (kind in ("CLVI", "CLTP")) != (dtype == 1):
                raise ValueError("invalid key type")
            stride = 8 if dtype == 1 else 12
            key_start = cur + key_off
            bounds(key_start, key_count * stride, end)
            keys = []
            for k in range(key_count):
                pos = key_start + k*stride
                key = list(take("fI" if dtype == 1 else "fff", pos, end))
                if not math.isfinite(key[0]) or (dtype == 2 and not all(map(math.isfinite, key))):
                    raise ValueError("nonfinite keyframe")
                if keys and key[0] < keys[-1][0]:
                    raise ValueError("decreasing frame order")
                keys.append(key)
            tracks.append({"pane": name, "kind": kind, "index": index,
                           "target": target, "value_type": dtype, "keys": keys})
    return {"frames": frames, "loop_flag": looping, "tracks": tracks}


def inventory(archive):
    clips = []
    with ZipFile(archive) as zipped:
        for item in zipped.infolist():
            name = item.filename
            if not name.startswith(PREFIX) or not name.lower().endswith(".bclan"):
                continue
            path = PurePosixPath(name)
            if item.is_dir() or item.file_size > 4_194_304 or ".." in path.parts or "\\" in name or len(path.parts) < 6:
                raise ValueError("unsafe CLAN ZIP entry")
            record = parse(zipped.read(item))
            record.update({"archive": path.parts[3], "clip": path.stem})
            clips.append(record)
    if len(clips) != 327:
        raise ValueError("expected 327 CLAN clips, got %d" % len(clips))
    clips.sort(key=lambda x: (x["archive"], x["clip"]))
    return {"clip_count": len(clips),
            "channel_count": sum(len(x["tracks"]) for x in clips), "clips": clips}


def evaluate(keys, frame, discrete=False):
    """Floating-point reference for testing the ARM9 fixed-point evaluator."""
    if not keys or not math.isfinite(frame):
        raise ValueError("empty keys or invalid frame")
    i = 0
    while i+1 < len(keys) and keys[i+1][0] <= frame:
        i += 1
    if discrete or i+1 == len(keys) or frame <= keys[0][0]:
        return keys[i][1]
    a, b = keys[i], keys[i+1]
    dt = b[0]-a[0]
    if dt <= 0:
        return b[1]
    t = (frame-a[0])/dt
    t2, t3 = t*t, t*t*t
    return ((2*t3-3*t2+1)*a[1] + (t3-2*t2+t)*dt*a[2]
            + (-2*t3+3*t2)*b[1] + (t3-t2)*dt*b[2])


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("archive")
    p.add_argument("--output", required=True)
    args = p.parse_args()
    info = inventory(args.archive)
    with open(args.output, "w", encoding="utf-8") as out:
        json.dump(info, out, separators=(",", ":"), allow_nan=False)
    print("PASS: %d original CLAN clips, %d keyframe channels" %
          (info["clip_count"], info["channel_count"]))
