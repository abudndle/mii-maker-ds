#!/usr/bin/env python3
"""Generate DS dialog-motion keys from privately extracted CLAN metadata."""
import argparse
import json
import math
from pathlib import Path

def q16(value):
    if not isinstance(value,(int,float)) or not math.isfinite(value):
        raise ValueError("nonfinite CLAN key")
    scaled=round(value*65536)
    if not -(2**31)<=scaled<2**31:
        raise ValueError("CLAN key exceeds Q16.16 range")
    return scaled

def generate(catalog):
    clips=[c for c in catalog.get("clips",[])
           if c.get("archive")=="Dialog.arc.files" and
              c.get("clip")=="DialogBase00_DialogIn"]
    if len(clips)!=1 or clips[0].get("frames")!=21:
        raise ValueError("missing/changed original DialogBase00_DialogIn")
    matches=[t for t in clips[0]["tracks"] if
             (t["pane"],t["kind"],t["index"],t["target"],t["value_type"])==
             ("W_Dialog","CLPA",0,1,2)]
    if len(matches)!=1:
        raise ValueError("expected exactly one W_Dialog Y track")
    keys=matches[0]["keys"]
    if len(keys)!=3 or keys[0][0]!=0 or keys[-1][0]!=20:
        raise ValueError("unexpected original dialog frame range")
    if keys[0][1]!=-240 or keys[-1][1]!=0:
        raise ValueError("unexpected original dialog endpoints")
    prev=float("-inf")
    rows=[]
    for key in keys:
        if len(key)!=3 or key[0]<prev or key[0]>20:
            raise ValueError("invalid original key ordering")
        prev=key[0]
        rows.append("{%s,%s,%s}"%tuple(q16(v) for v in key))
    return ("/* Private-source numeric CLAN W_Dialog Y keys, no original file payload. */\n"
            "#ifndef MDS_CLAN_DIALOG_GENERATED_H\n"
            "#define MDS_CLAN_DIALOG_GENERATED_H\n"
            '#include "clan_curve.h"\n'
            "static const MdsClanKey dialog_in_y[]={"+",".join(rows)+"};\n"
            "#endif\n")

if __name__=="__main__":
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("catalog",type=Path)
    parser.add_argument("--output",type=Path,required=True)
    args=parser.parse_args()
    result=generate(json.loads(args.catalog.read_text(encoding="utf-8")))
    args.output.write_text(result,encoding="utf-8")
    print("PASS: original DialogBase00_DialogIn W_Dialog Y keys generated")
