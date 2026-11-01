#!/usr/bin/env python3
"""Regress DS 3DS-source navigation and confirmation wiring without private assets."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
menu=(root/"source/menu.c").read_text()
ui=(root/"source/ui.c").read_text()
art=(root/"source/original_gallery_art.c").read_text()
numeric=(root/"source/gallery_nav_clan_generated.h").read_text()
state=(root/"source/gallery_nav_clan.c").read_text()
gallery=main.split("}else if(screen==MDS_SCREEN_GALLERY){",1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){",1)[0]
checks={
 "original 3DS source clips and keyframes":
    "MDS_SOURCE_EDITSELECTBASE_SCROLLL_FRAMES 11u" in numeric and
    "MDS_SOURCE_EDITSELECTBASE_SCROLLR_FRAMES 11u" in numeric and
    "MDS_SOURCE_EDITSELECTBASE_INVALID_FRAMES 11u" in numeric and
    "gallery_nav_left_l_x" in numeric and
    "gallery_nav_right_r_x" in numeric and
    "gallery_confirm_red" in numeric,
 "original 3DS hardware scale, not approximate offsets":
    "5LL*65536LL" in state and
    "source_pixels_to_ds" in state,
 "verified invalid source has constant zero arrow offset":
    "gallery_nav_invalid_arrow_x[]={{0,0,0}}" in numeric and
    "do not manufacture" in state,
 "original arrow artwork shifts, original hitboxes stay fixed":
    "draw_original_room_arrows(&navigation)" in ui and
    "3+x+left_dx" in ui and "240+x+right_dx" in ui and
    "mds_gallery_room_arrow(input.touch.px,input.touch.py,page)" in gallery,
 "original selection art receives source CLMC tint":
    "mds_original_gallery_box_border_tinted(bottom,256,192" in ui and
    "navigation.confirm_tint" in ui and
    "mds_original_gallery_box_border_tinted" in art,
 "navigation triggers on physical shoulders":
    "mds_ui_gallery_navigation(direction,animation_vblanks)" in gallery,
 "navigation triggers on stylus arrows including held dragging":
    "mds_ui_gallery_navigation(arrow,animation_vblanks)" in gallery and
    "gallery_drag.source>=0" in gallery,
 "tap and successful saved move trigger original confirmation":
    gallery.count("mds_ui_gallery_confirm(animation_vblanks)")>=2,
 "invalid first/last room event and no unrequested wrap":
    "mds_ui_gallery_invalid(page==0?-1:1)" in gallery and
    "if((direction<0&&page==0)||(direction>0&&page==9))return -1" in menu,
 "new source feedback loop gets VBlank redraw and complete reset":
    "mds_gallery_nav_clan_active(&gallery_nav_clan_state,now)" in ui and
    "mds_gallery_nav_clan_reset(&gallery_nav_clan_state)" in ui,
 "original private binaries not present in repository source":
    not list((root/"source").glob("*.bclan")),
}
for name,good in checks.items():
    if not good:raise SystemExit("FAIL: "+name)
print("PASS: original 3DS scroll, confirmation and invalid-boundary input wiring")
