#!/usr/bin/env python3
"""Reject false-positive 'gallery' captures and require multiple rendered Miis.

Compare against the BEFORE (home) frame in native DS screen coordinates.
This is strictly an emulator acceptance probe, not a fidelity certificate.
"""
import argparse
import json
from pathlib import Path
from PIL import Image

def ds_pixels(path, require_native_width=False):
    with Image.open(path) as opened:
        image = opened.convert("RGB")
    w,h=image.size
    if w<256 or h<384:
        raise ValueError("capture smaller than both original 256x192 DS screens")
    # The private acceptance runner uses native-size 256x384 DS screens.
    # Refuse wider windows rather than silently sampling their left edge,
    # which could be toolbar/background pixels rather than the game.
    if require_native_width and w!=256:
        raise ValueError(f"capture width {w} is not native DS width 256; crop the emulator viewport first")
    # melonDS screenshots may include the QT menu bar above the DS canvas.
    return image.crop((0,h-384,256,h))

def different(a,b,box,threshold=28):
    count=0
    left,top,right,bottom=box
    p=a.load();q=b.load()
    for y in range(top,bottom):
        for x in range(left,right):
            r=p[x,y];s=q[x,y]
            if max(abs(int(r[k])-int(s[k])) for k in range(3))>=threshold:
                count+=1
    return count

def verify(home_path,gallery_path,minimum_actors=2,require_native_width=False):
    # A window resize between captures changes the sampled viewport and
    # can masquerade as gameplay movement. Fail rather than compare it.
    with Image.open(home_path) as before, Image.open(gallery_path) as after:
        if before.width < 256 or before.height < 384 or after.width < 256 or after.height < 384:
            raise ValueError("capture smaller than both original 256x192 DS screens")
        if before.size != after.size:
            raise ValueError(f"capture window geometry changed ({before.size} vs {after.size})")
    home=ds_pixels(home_path,require_native_width);gallery=ds_pixels(gallery_path,require_native_width)
    if home.tobytes()==gallery.tobytes():
        raise ValueError("gallery capture is identical to home; the input did not reach the game")
    top=different(home,gallery,(0,0,256,192))
    bottom=different(home,gallery,(0,192,256,384))
    if top<200 or bottom<350:
        raise ValueError(f"menu changed without a proven gallery scene (top={top}, bottom={bottom})")
    # Original SelectMii B_Mii_00..09 placement (DS-scaled source CLYT).
    cols=(21,64,107,150,194)
    visible=[]
    for local in range(10):
        x=cols[local%5]
        y=49 if local<5 else 97
        changes=different(home,gallery,(x,y,x+42,y+46))
        if changes>=80:
            visible.append(local)
    if len(visible)<minimum_actors:
        raise ValueError(f"fewer than {minimum_actors} independently rendered Mii positions: {visible}")
    return {"top_changed_pixels":top,"bottom_changed_pixels":bottom,
            "changed_mii_pane_slots":visible, "minimum_actor_positions":minimum_actors}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("home",type=Path)
    p.add_argument("gallery",type=Path)
    p.add_argument("--report",type=Path)
    p.add_argument("--require-native-width",action="store_true",help="reject captures wider than 256 pixels; opt in only for native viewport screenshots")
    a=p.parse_args()
    try:
        result=verify(a.home,a.gallery,require_native_width=a.require_native_width)
        if a.report:
            a.report.write_text(json.dumps(result,sort_keys=True,indent=2)+"\n",encoding="utf8")
    except (OSError,ValueError) as exc:
        p.exit(1,f"FAIL: saved-Mii scene: {exc}\n")
    print("PASS: gallery changed both DS screens and rendered independently at %d source-layout Mii positions" %
          len(result["changed_mii_pane_slots"]))

if __name__=="__main__":
    main()
