#!/usr/bin/env python3
"""Asset-free statistics on privately captured melonDS screen pixels."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image

def measure(image_path):
    with Image.open(image_path) as opened:
        image = opened.convert("RGB")
    width, height = image.size
    if width < 256 or height < 192:
        raise ValueError("capture too small to contain a DS screen")
    thumb=image.copy()
    thumb.thumbnail((256,384))
    pixels=list(thumb.getdata())
    distinct=len(set(pixels))
    ranges=[max(p[i] for p in pixels)-min(p[i] for p in pixels) for i in range(3)]
    if distinct<32 or max(ranges)<25:
        raise ValueError("boot screen visually blank or uniform (%d colors)"%distinct)
    return {"width":width,"height":height,"sampled_unique_colors":distinct,
            "channel_ranges":ranges,"sha256":hashlib.sha256(Path(image_path).read_bytes()).hexdigest()}

def compare_gallery(before_path,after_path,min_changed=700):
    """Fail an alleged gallery capture if the DS touchscreen never changed."""
    with Image.open(before_path) as a, Image.open(after_path) as b:
        first=a.convert("RGB");second=b.convert("RGB")
    if first.size!=second.size:
        raise ValueError("capture window geometry changed")
    w,h=first.size
    if w<256 or h<384:
        raise ValueError("expected vertically stacked Nintendo DS display")
    bounds=(w//10,h-172,w-w//10,h-20)
    px=first.crop(bounds).getdata()
    qx=second.crop(bounds).getdata()
    changed=sum(max(abs(x[i]-y[i]) for i in range(3))>12
                for x,y in zip(px,qx))
    if changed<min_changed:
        raise ValueError(f"gallery still shows home screen ({changed} changed pixels)")
    return {"gallery_changed_pixels":changed,"gallery_navigation_verified":True}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("screenshot",type=Path)
    p.add_argument("--report",type=Path)
    p.add_argument("--compare-home",type=Path)
    a=p.parse_args()
    try:
        report=measure(a.screenshot)
        if a.compare_home:report.update(compare_gallery(a.compare_home,a.screenshot))
        if a.report:a.report.write_text(json.dumps(report,indent=2,sort_keys=True)+"\n")
    except (OSError,ValueError) as e:
        p.exit(1,f"FAIL: melonDS visual smoke: {e}\n")
    print("PASS: melonDS rendered %d distinct sampled colors; dimensions %dx%d" % (
        report["sampled_unique_colors"],report["width"],report["height"]))
if __name__=="__main__":main()
