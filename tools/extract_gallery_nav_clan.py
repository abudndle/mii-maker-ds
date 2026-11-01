#!/usr/bin/env python3
"""Audit source numeric 3DS Mii gallery navigation/confirmation curves privately.

Reads the user's extracted Select.arc/anim only. Do not upload .bclan inputs,
original textures or the full game. The JSON output has only selected small
numeric keyframe tracks, source filenames and SHA-256 provenance.
"""
import argparse
import hashlib
import json
from pathlib import Path
from extract_gallery_clan import parse

TRACKS = {
    "EDITSelectBase_ScrollL": {
        "P_ArrowL": [("CLPA",0x0000)],
        "P_ArrowR": [("CLPA",0x0000)],
        "P_ArrowLSdw_00": [("CLVC",0x1000)],
    },
    "EDITSelectBase_ScrollR": {
        "P_ArrowL": [("CLPA",0x0000)],
        "P_ArrowR": [("CLPA",0x0000)],
        "P_ArrowLSdw_00": [("CLVC",0x1000)],
    },
    "EDITSelectBase_Invalid": {
        "P_ArrowL": [("CLPA",0x0000)],
        "P_ArrowR": [("CLPA",0x0000)],
    },
    "SelectMii_Decide": {
        "P_Mii_00": [("CLMC",0x0400),("CLMC",0x0500),("CLMC",0x0600)],
    },
    "SelectMii_UnDecide": {
        "P_Mii_00": [("CLMC",0x0400),("CLMC",0x0500),("CLMC",0x0600)],
    },
}

def q16(value:float)->int:
    integer=round(value*65536)
    if not -(2**31)<=integer<2**31:
        raise ValueError("BCLAN keyframe value outside Q16.16 range")
    return integer

def audit(directory:Path)->dict:
    results={}
    for clip,panes in TRACKS.items():
        file=directory/(clip+".bclan")
        data=file.read_bytes()
        frames,tracks=parse(data)
        selected={}
        for pane,channels in panes.items():
            available=[v for (name,_category),v in tracks.items() if name==pane]
            if len(available)!=1:
                raise ValueError(f"ambiguous source pane {clip}/{pane}")
            for tag,kind in channels:
                keys=available[0].get((tag,kind))
                if not keys:
                    raise ValueError(f"missing {clip}/{pane}/{tag}/{kind:#x}")
                selected[f"{pane}/{tag}/{kind:#06x}"]=[
                    [q16(frame),q16(value),q16(tangent)]
                    for frame,value,tangent in keys
                ]
        results[clip]={
            "source_frames":frames,
            "sha256":hashlib.sha256(data).hexdigest(),
            "keyframes_q16":selected
        }
    return results

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_select_animation_directory",type=Path)
    parser.add_argument("--report",type=Path,help="optional private JSON output")
    args=parser.parse_args()
    data=audit(args.private_select_animation_directory)
    summary={k:{"source_frames":v["source_frames"],"sha256":v["sha256"],
                "channels":len(v["keyframes_q16"])} for k,v in data.items()}
    print(json.dumps(summary,indent=2))
    if args.report:
        args.report.write_text(json.dumps(data,indent=2)+"\n")

if __name__=="__main__":
    main()
