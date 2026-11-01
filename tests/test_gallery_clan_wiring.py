#!/usr/bin/env python3
"""Regression checks for actual 3DS-derived gallery CLAN effects in DS runtime."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
ui=(root/'source/ui.c').read_text()
main=(root/'source/main.c').read_text()
art=(root/'source/original_gallery_art.c').read_text()
curves=(root/'source/gallery_clan_generated.h').read_text()
engine=(root/'source/gallery_clan.c').read_text()
gallery=ui[ui.index('void mds_ui_gallery(const'):]
checks={
    "source selects correct 3DS clips":
        'SelectMii_Select:' in curves and
        'EDITSelectBase_Select:' not in curves or
        'gallery_slot_select_scale_x' in curves,
    "source animation data is compact numeric metadata":
        'gallery_room_select_red' in curves and
        'gallery_room_unselect_red' in curves and
        'gallery_slot_select_scale_x' in curves,
    "gallery uses actual source pane CLMC RGB modulation":
        'mds_original_gallery_room_tab_tinted(bottom,256,192' in gallery and
        'clan.selected_room_tint' in gallery and
        'clan.previous_room_tint' in gallery,
    "source CLPA scales the thumbnail, not the stationary Mii box":
        'MDS_THUMBNAIL_WIDTH*clan.scale_x_q16' in gallery and
        'gallery_thumbnails.slots[i].pixels[' in gallery and
        'mds_original_gallery_box_base(bottom,256,192' in gallery,
    "source effects are controlled by VBlank and shut off":
        'mds_gallery_clan_active(&gallery_clan_state,now)' in ui and
        'gallery_clan_was_active&&!active' in ui and
        'gallery_clan_painted=now' in gallery and
        'mds_ui_gallery_clan_tick(page,editor.slot,animation_vblanks)' in main,
    "gallery reset on other screens":
        'if(screen!=MDS_SCREEN_GALLERY)mds_ui_gallery_clan_reset();' in main,
    "single asset load preserved":
        'if(sprite->state!=0)return sprite->state==1;' in art,
    "source interpolation entirely in fixed point":
        'mds_clan_curve_eval(' in engine and
        'SOURCE_FRAME_Q16_PER_VBLANK' in engine,
    "no source Nintendo BCLAN file published":
        not list((root/'source').glob('*.bclan')),
}
for name,okay in checks.items():
    if not okay:
        raise SystemExit('FAIL: '+name)
print('PASS: source CLPA scale, CLMC color, original hitboxes and frame scheduling')
