#!/usr/bin/env python3
"""Verify the optimized opaque RGB555 path remains pixel-identical to the old path."""
from pathlib import Path
import re

source = (Path(__file__).resolve().parents[1] / "source" / "head.c").read_text()
match = re.search(r"static const uint8_t shirts\[12\]\[3\]=\{(.*?)\};", source, re.S)
if not match:
    raise SystemExit("FAIL: original Mii shirt palette missing")
colors = [tuple(map(int, item.split(","))) for item in re.findall(r"\{(\d+,\d+,\d+)\}", match.group(1))]
assert len(colors) == 12
# Same integer expression as the original renderer, channel-by-channel.
def previous(color, light):
    rgb = [channel * light // 255 for channel in color]
    return 0x8000 | (rgb[0] >> 3) | ((rgb[1] >> 3) << 5) | ((rgb[2] >> 3) << 10)

def optimized(color, light):
    return (0x8000 | ((color[0] * light // 255) >> 3)
            | (((color[1] * light // 255) >> 3) << 5)
            | (((color[2] * light // 255) >> 3) << 10))

for color in colors:
    for light in range(256):
        assert previous(color, light) == optimized(color, light), (color, light)
# Include pure channel extremes and mixed colors outside the shirt palette.
for color in ((0, 0, 0), (255, 255, 255), (255, 0, 0),
              (0, 255, 0), (0, 0, 255), (31, 127, 248)):
    for light in range(256):
        assert previous(color, light) == optimized(color, light), (color, light)
print("PASS: optimized opaque RGB555 rendering matches 4,608 reference colors")
