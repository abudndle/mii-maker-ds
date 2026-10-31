#!/usr/bin/env python3
"""Generate original dialog entry and exit W_Dialog Y keys from private CLAN metadata."""
import argparse
import json
import math
from pathlib import Path

CLIPS = (
    ("DialogBase00_DialogIn", "dialog_in_y", 3, -240, 0, 20),
    ("DialogBase00_DialogOut", "dialog_out_y", 2, 0, -240, 17),
    ("DialogBase00_DialogOutUp", "dialog_out_up_y", 2, 0, 240, 17),
)

def q16(value):
    if not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError("nonfinite CLAN key")
    scaled=round(value*65536)
    if not -(2**31)<=scaled<2**31:
        raise ValueError("CLAN key exceeds Q16.16 range")
    return scaled

def generate(catalog):
    rows=["/* Numeric keyframes extracted from original private Dialog.arc.files.",
          " * No original Nintendo binary/audio/image resources are included. */",
          "#ifndef MDS_CLAN_DIALOG_GENERATED_H",
          "#define MDS_CLAN_DIALOG_GENERATED_H",
          '#include "clan_curve.h"']
    for clip_name,array_name,n,start,end_frame,terminal in CLIPS:
        matches=[c for c in catalog.get("clips",[])
                 if c.get("archive")=="Dialog.arc.files" and c.get("clip")==clip_name]
        if len(matches)!=1 or matches[0].get("frames")!=21:
            raise ValueError("missing/changed original "+clip_name)
        tracks=[t for t in matches[0]["tracks"] if
                (t["pane"],t["kind"],t["index"],t["target"],t["value_type"])==
                ("W_Dialog","CLPA",0,1,2)]
        if len(tracks)!=1:raise ValueError("missing/ambiguous W_Dialog track for "+clip_name)
        keys=tracks[0]["keys"]
        if len(keys)!=n or keys[0][0]!=0 or keys[-1][0]!=terminal:
            raise ValueError("unexpected animation frame span for "+clip_name)
        if keys[0][1]!=start or keys[-1][1]!=end_frame:
            raise ValueError("unexpected animation endpoints for "+clip_name)
        previous=-1
        converted=[]
        for key in keys:
            if len(key)!=3 or key[0]<previous or key[0]>20:
                raise ValueError("invalid original CLAN frame ordering")
            previous=key[0]
            converted.append("{"+",".join(str(q16(value)) for value in key)+"}")
        rows.append("static const MdsClanKey "+array_name+"[]={"+",".join(converted)+"};")
    rows.append("#endif")
    return "\n".join(rows)+"\n"

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=generate(json.loads(args.catalog.read_text(encoding="utf-8")))
    args.output.write_text(result,encoding="utf-8")
    print("PASS: original DialogBase00 entry, exit and exit-up W_Dialog Y keys")
