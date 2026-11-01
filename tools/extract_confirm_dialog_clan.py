#!/usr/bin/env python3
"""Verify privately owned original Mii Maker 3DS two-button DialogBase02.

Extract only public-safe numeric metadata (CLPA W_Dialog Y curve) and SHA-256.
The Nintendo .bclan files themselves must not enter a public repository.
Run this against the user's locally extracted Dialog.arc/anim folder.
"""
from pathlib import Path
from argparse import ArgumentParser
import hashlib
import json
from extract_gallery_clan import parse

CLIPS=(
    "DialogBase02_DialogIn",
    "DialogBase02_DialogOut",
    "DialogBase02_DialogOutUp",
)

def inspect(directory:Path)->dict:
    report={}
    for clip in CLIPS:
        data=(directory/(clip+".bclan")).read_bytes()
        frames,panes=parse(data)
        found=[(name,channels) for (name,_category),channels in panes.items()
               if name=="W_Dialog"]
        if len(found)!=1:
            raise ValueError("expected one source W_Dialog pane in "+clip)
        keys=found[0][1].get(("CLPA",0x0100))
        if not keys:
            raise ValueError("missing source W_Dialog Y channel: "+clip)
        q16=[]
        for frame,value,tangent in keys:
            values=[round(number*65536) for number in (frame,value,tangent)]
            if any(not -(2**31)<=v<2**31 for v in values):
                raise ValueError("source key out of 32-bit Q16 range")
            q16.append(values)
        report[clip]=dict(source_frames=frames,
                          sha256=hashlib.sha256(data).hexdigest(),
                          source_track="W_Dialog/CLPA/0100",
                          keyframes_q16=q16)
    return report

def main():
    parser=ArgumentParser(description=__doc__)
    parser.add_argument("private_dialog_anim_dir",type=Path)
    parser.add_argument("--private-report",type=Path)
    args=parser.parse_args()
    report=inspect(args.private_dialog_anim_dir)
    print(json.dumps({
        clip:dict(source_frames=meta["source_frames"],
                  sha256=meta["sha256"],
                  numeric_key_count=len(meta["keyframes_q16"]))
        for clip,meta in report.items()
    },indent=2))
    if args.private_report:
        args.private_report.write_text(json.dumps(report,indent=2)+"\n")

if __name__=="__main__":
    main()
