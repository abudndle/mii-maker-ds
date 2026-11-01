#!/usr/bin/env python3
"""Verify exact original DialogBase02 Select and Decide CLMC tracks privately.

Only numeric metadata and SHA-256 are printed; original Nintendo BCLAN
binaries are not bundled or uploaded. Input: original Dialog.arc/anim folder.
"""
from pathlib import Path
import argparse
import hashlib
from extract_gallery_clan import parse

TRACKS=("DialogBase02_Select","DialogBase02_Decide")
SOURCE_DEFAULT=(100,190,149)
SOURCE_SELECTED=(50,163,112)

def check(directory:Path):
    reports=[]
    for clip in TRACKS:
        data=(directory/(clip+".bclan")).read_bytes()
        frames,panes=parse(data)
        if frames!=6:raise ValueError("unexpected original source frames: "+clip)
        for pane in ("P_BaseL_00","P_BaseR_00"):
            rows=[channels for (name,_),channels in panes.items() if name==pane]
            if len(rows)!=1:raise ValueError("missing original confirmation pane "+pane)
            channels=rows[0]
            start=tuple(round(channels["CLMC",kind][0][1]) for kind in (0x400,0x500,0x600))
            if clip.endswith("_Select"):
                finish=tuple(round(channels["CLMC",kind][-1][1]) for kind in (0x400,0x500,0x600))
                if start!=SOURCE_DEFAULT or finish!=SOURCE_SELECTED:
                    raise ValueError("original selection color differs: "+pane)
            elif start!=SOURCE_SELECTED:
                raise ValueError("original Decide color differs: "+pane)
        reports.append((clip,frames,hashlib.sha256(data).hexdigest()))
    return reports

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("private_dialog_anim",type=Path)
    args=parser.parse_args()
    for clip,frames,digest in check(args.private_dialog_anim):
        print(f"PASS {clip}: {frames} original frames, SHA256 {digest}")

if __name__=="__main__":
    main()
