#!/usr/bin/env python3
"""Generate source-derived DS home animation tables from private numeric metadata."""
import argparse
import json
import math
from pathlib import Path

TRACKS = [
    ("home_y0", "N_BtnTop_03", "CLPA", 0, 1),
    ("home_y1", "N_BtnTop_02", "CLPA", 0, 1),
    ("home_y2", "N_BtnTop_01", "CLPA", 0, 1),
    ("home_y3", "N_BtnTop_00", "CLPA", 0, 1),
    ("home_red", "BtnSel_L", "CLMC", 0, 4),
    ("home_green", "BtnSel_L", "CLMC", 0, 5),
    ("home_blue", "BtnSel_L", "CLMC", 0, 6),
    ("home_alpha", "BtnSel_L", "CLMC", 0, 15),
    ("home_shadow", "BtnSelSdwL", "CLVC", 0, 16),
]


def q16(value):
    if not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError("nonfinite original key")
    scaled = round(value * 65536)
    if not -(2**31) <= scaled < 2**31:
        raise ValueError("original key beyond fixed-point range")
    return scaled


def generate(catalog):
    clips = [clip for clip in catalog.get("clips", [])
             if clip.get("archive") == "Plaza.arc.files"
             and clip.get("clip") == "PlazaTop_Select"]
    if len(clips) != 1 or clips[0].get("frames") != 6:
        raise ValueError("missing or changed original PlazaTop_Select clip")
    clip = clips[0]
    output = ["/* Generated from privately owned original CLAN numeric metadata. */",
              "#ifndef MDS_CLAN_HOME_GENERATED_H", "#define MDS_CLAN_HOME_GENERATED_H",
              '#include "clan_curve.h"']
    for name, pane, kind, index, target in TRACKS:
        matches = [t for t in clip["tracks"] if
                   (t["pane"], t["kind"], t["index"], t["target"]) ==
                   (pane, kind, index, target)]
        if len(matches) != 1 or matches[0].get("value_type") != 2:
            raise ValueError("missing/ambiguous source channel: " + name)
        keys = matches[0]["keys"]
        if not 2 <= len(keys) <= 16 or keys[0][0] != 0 or keys[-1][0] != 1:
            raise ValueError("unexpected source key range: " + name)
        if any(len(k) != 3 or k[0] < 0 or k[0] > 1 for k in keys):
            raise ValueError("invalid keys: " + name)
        values = ", ".join("{%s, %s, %s}" % tuple(q16(v) for v in key)
                           for key in keys)
        output.append(f"static const MdsClanKey {name}[] = {{{values}}};")
    output.append("#endif")
    return "\n".join(output) + "\n"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    args.output.write_text(generate(json.loads(args.catalog.read_text(encoding="utf-8"))),
                           encoding="utf-8")
    print("PASS: nine original CLAN UI property tracks generated")
