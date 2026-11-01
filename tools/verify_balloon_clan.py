#!/usr/bin/env python3
"""Validate original SelectBalloonButton CLAN curves against portable DS code.

Original BCLAN bytes are read by the private catalog builder in memory.
Only source Q16 keyframes and metadata-only hashes are compared. Never export
the original Nintendo clip files, images, ROMs or ZIP member contents.
"""
import hashlib
import json
import math
import re
from pathlib import Path

CLIPS = {
    "SelectBalloonButton_Select": (11, (
        ("P_Favorite", "CLPA", 0, 6, "favorite_parent_scale"),
        ("P_Favorite", "CLPA", 0, 7, "favorite_parent_scale"),
        ("I_Favorite", "CLPA", 0, 6, "favorite_scale"),
        ("I_Favorite", "CLPA", 0, 7, "favorite_scale"),
        ("N_Touch", "CLPA", 0, 1, "touch_y"),
        ("N_Balloon", "CLVC", 0, 16, "balloon_alpha"),
    )),
    "SelectBalloonButton_Unselect": (6, (
        ("I_Favorite", "CLVC", 0, 16, "fade_out"),
        ("N_Balloon", "CLVC", 0, 16, "fade_out"),
    )),
    "SelectBalloonButton_Decide": (6, (
        ("I_Favorite", "CLVC", 0, 16, None),
    )),
    "SelectBalloonButton_UnDecide": (6, (
        ("I_Favorite", "CLVC", 0, 16, "fade_out"),
    )),
}
TOKEN = r"(?:-?Q\(\s*-?\d+\s*\)|-?\d+)"
KEY = re.compile(r"\{\s*(" + TOKEN + r")\s*,\s*(" + TOKEN + r")\s*,\s*(" + TOKEN + r")\s*\}")
ARRAY = re.compile(r"\bstatic\s+const\s+MdsClanKey\s+([A-Za-z_]\w*)\s*\[\s*\]\s*=\s*\{(.*?)\}\s*;", re.S)


def q_token(token):
    token = token.replace(" ", "")
    if "Q(" not in token:
        return int(token)
    sign = -1 if token.startswith("-") else 1
    return sign * int(token.lstrip("-")[2:-1]) * 65536


def parse_balloon_tables(content):
    result = {}
    for match in ARRAY.finditer(content):
        name, raw = match.groups()
        if name in result:
            raise ValueError("duplicate balloon table: " + name)
        keys = [tuple(q_token(t) for t in k.groups()) for k in KEY.finditer(raw)]
        if not keys or re.sub(r"[\s,]", "", KEY.sub("", raw)):
            raise ValueError("invalid balloon CLAN table: " + name)
        result[name] = keys
    expected = {"favorite_parent_scale", "favorite_scale", "touch_y", "balloon_alpha", "fade_out"}
    if result.keys() != expected:
        raise ValueError("missing or unexpected balloon CLAN tables")
    return result


def q_float(value):
    if not isinstance(value, (float, int)) or not math.isfinite(value):
        raise ValueError("nonfinite source CLAN key")
    fixed = round(value * 65536)
    if not -(1 << 31) <= fixed < (1 << 31):
        raise ValueError("source CLAN key exceeds Q16 range")
    return fixed


def verify_balloon_clips(catalog, source_dir):
    src = (Path(source_dir) / "gallery_balloon_clan.c").read_text(encoding="utf-8")
    tables = parse_balloon_tables(src)
    selected = [clip for clip in catalog.get("clips", [])
                if clip.get("archive") == "Select.arc.files" and clip.get("clip") in CLIPS]
    if len(selected) != len(CLIPS) or len({clip["clip"] for clip in selected}) != len(CLIPS):
        raise ValueError("missing or duplicate original SelectBalloonButton clips")
    total = 0
    for clip in selected:
        frames, specs = CLIPS[clip["clip"]]
        if clip.get("frames") != frames or clip.get("loop_flag") != 0:
            raise ValueError("unexpected source CLAN duration or loop: " + clip["clip"])
        tracks = clip.get("tracks", [])
        if len(tracks) != len(specs):
            raise ValueError("unexpected source CLAN channels: " + clip["clip"])
        channels = {}
        for track in tracks:
            if track.get("value_type") != 2:
                raise ValueError("unexpected discrete CLAN channel: " + clip["clip"])
            key = (track["pane"], track["kind"], track["index"], track["target"])
            if key in channels:
                raise ValueError("duplicate source CLAN channel: " + clip["clip"])
            channels[key] = [tuple(map(q_float, item)) for item in track["keys"]]
        for pane, kind, index, target, table in specs:
            key = (pane, kind, index, target)
            if key not in channels:
                raise ValueError("missing original balloon channel: " + str(key))
            expected = tables[table] if table else [(0, 255 * 65536, 0)]
            if channels[key] != expected:
                raise ValueError("source balloon CLAN key mismatch: " + clip["clip"] + "/" + pane)
        total += len(tracks)
    canonical = json.dumps(tables, sort_keys=True, separators=(",", ":")).encode("ascii")
    return {"clips": len(selected), "channels": total,
            "numeric_sha256": hashlib.sha256(canonical).hexdigest()}
