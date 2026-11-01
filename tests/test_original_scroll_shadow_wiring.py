#!/usr/bin/env python3
"""Asset-free linkage check for original 3DS Select.arc BtnScrollShadow and CLVC."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
ui=(root/'source/ui.c').read_text()
art=(root/'source/original_gallery_art.c').read_text()
h=(root/'source/original_gallery_art.h').read_text()
nav=(root/'source/gallery_nav_clan.c').read_text()
curves=(root/'source/gallery_nav_clan_generated.h').read_text()
gallery=ui[ui.index('static void draw_original_room_arrows('):
           ui.index('static int gallery_drag_slot=-1;')]
checks={
    "uses authentic original private scroll shadow artwork":
        'nitro:/art/Select/BtnScrollShadow.bin' in art,
    "source texture exact 16x16 original dimensions":
        'BtnScrollShadow.bin",16,16' in art,
    "source CLVC 200-to-zero/zero-to-200 curves unchanged":
        'gallery_nav_left_shadow_alpha' in curves and
        'gallery_nav_right_shadow_alpha' in curves and
        'out->shadow_alpha=alpha8(eval(shadow,2,elapsed));' in nav,
    "shadow drawn behind arrow not above":
        'mds_original_gallery_arrow_shadow(bottom,256,192,' in gallery and
        gallery.index('mds_original_gallery_arrow_shadow(') <
        gallery.index('for(int y=0;y<18;y++)'),
    "both original arrows share source CLVC":
        gallery.count('mds_original_gallery_arrow_shadow(bottom,256,192,')==2,
    "source 320-to-256 stamp scale and fixed hitboxes":
        '3+left_dx,89,13,13,shadow_alpha' in gallery and
        '240+right_dx,89,13,13,shadow_alpha' in gallery and
        'mds_gallery_room_arrow' in (root/'source/menu.c').read_text(),
    "clipped channel blending not a fabricated shadow box":
        'original_sprite_ready(&arrow_shadow)' in art and
        'if(!(src&0x8000u))continue;' in art and
        '(dv*(255u-alpha)+sv*alpha+127u)/255u' in art,
    "missing original source art leaves background unchanged":
        'if(!original_sprite_ready(&arrow_shadow))return 0;' in art,
    "header exposes API for independent host testing":
        'mds_original_gallery_arrow_shadow(' in h,
    "no Nintendo binaries committed in source":
        not list((root/'source').glob('*.bclim')),
}
for label,ok in checks.items():
    if not ok:raise SystemExit('FAIL: '+label)
print('PASS: original source scroll-shadow image, CLVC timing, blending and fixed hitboxes')
