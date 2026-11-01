#!/usr/bin/env python3
"""Regress gallery primary command priority over secondary mutations."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
gallery=main.split("}else if(screen==MDS_SCREEN_GALLERY){",1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){",1)[0]
assert gallery.count("mds_gallery_controls_secondary_allowed(gallery_action)")>=4
for token in ("if((down&KEY_X)&&!block_gallery_actions&&",
              "if((down&KEY_Y)&&!block_gallery_actions&&",
              "if(touch_action==MDS_GALLERY_ACTION_FAVORITE&&!(down&KEY_X)&&",
              "else if(touch_action==MDS_GALLERY_ACTION_COPY&&"):
    assert token in gallery, token
assert "KEY_UP|KEY_DOWN|KEY_LEFT|KEY_RIGHT|KEY_START" in gallery
assert gallery.index("mds_gallery_action_press_reset(&gallery_action_press);") < gallery.index(
    "if(input.up&KEY_TOUCH)")
print("PASS: primary gallery input wins and physical controls cancel pending touches")
