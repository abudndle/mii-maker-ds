#!/usr/bin/env python3
"""Source-only regression for optional original 3DS selection arrow art."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ui=(root/"source/ui.c").read_text()
source=(root/"tools/convert_original_bclim.py").read_text()

checks={
 "original 3DS artwork optional": 'fopen("nitro:/art/Select/BtnArrow.bin","rb")' in ui,
 "one-time asset read": "if(original_room_arrow_state==0){" in ui,
 "missing private asset is safe": "original_room_arrow_state=-1;" in ui and
                               "if(original_room_arrow_state!=1)return;" in ui,
 "original left/right source coordinate rendering": "(86+y)*256+3+x" in ui and
                                                    "(86+y)*256+240+x" in ui,
 "left-right arrow mirrored": "original_room_arrow[y*12+(11-x)]" in ui,
 "source selection background retained": 'bitmap("nitro:/ui/gallery-bottom.rgb555",bottom);' in ui,
 "runtime used in gallery": "    draw_original_room_arrows();" in ui,
 "converter validates input": "CLIM tiled-data size mismatch" in source and
                               "invalid CLIM footer fields" in source,
}
for name,valid in checks.items():
    if not valid:raise SystemExit("FAIL: "+name)
print("PASS: original 3DS room arrow resource linkage, safety, caching, geometry")
