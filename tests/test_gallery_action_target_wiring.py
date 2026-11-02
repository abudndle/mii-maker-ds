#!/usr/bin/env python3
"""Ensure the gallery binds each stylus action to its original selected Mii."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
gallery=main.split("}else if(screen==MDS_SCREEN_GALLERY){",1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){",1)[0]
assert "mds_gallery_action_press_bind_slot(&gallery_action_press,editor.slot);" in gallery
assert "mds_gallery_action_press_release_for_slot(" in gallery
assert "editor.slot,!gallery.used[editor.slot]||" in gallery
assert "mds_ui_gallery_actions_visible(animation_vblanks)&&" in gallery
assert "gallery_action_press.pressed!=MDS_GALLERY_ACTION_FAVORITE||" in gallery
assert "mds_ui_gallery_favorite_visible(animation_vblanks))));" in gallery
assert gallery.index("mds_gallery_action_press_bind_slot(") < gallery.index(
    "mds_gallery_action_press_release_for_slot("
)
assert "if(!gallery.used[editor.slot]&&" in gallery
print("PASS: release targets original Mii and rechecks balloon visibility")
