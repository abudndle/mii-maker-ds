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
assert "mds_gallery_controls_suppress_export_on_touch(" in gallery
assert "mds_gallery_controls_consume_physical(" in gallery
assert "KEY_L|KEY_R|KEY_UP|KEY_DOWN|KEY_LEFT|KEY_RIGHT|KEY_START;" in gallery
assert "((input.down|input.held|input.up)&other_gallery_keys)!=0);" in gallery
assert gallery.index("mds_gallery_controls_consume_physical(") < gallery.index(
    "mds_gallery_controls_consume_touch(")
assert "mds_gallery_controls_consume_touch(&gallery_controls," in gallery
assert "((input.down|input.held|input.up)&KEY_TOUCH)!=0);" in gallery
assert gallery.index("mds_gallery_controls_consume_touch(") < gallery.index(
    "mds_gallery_controls_suppress_export_on_touch(")
assert "gallery_action,((input.held|input.up)&KEY_TOUCH)!=0);" in gallery
assert "mds_gallery_action_press_cancel_for_physical(" in gallery
assert "(down&physical_gallery_keys)!=0," in gallery
assert "(input.up&physical_gallery_keys)!=0);" in gallery
assert "mds_gallery_action_press_cancel_for_held(" in gallery
assert "&gallery_action_press,(input.held&physical_gallery_keys)!=0);" in gallery
assert gallery.index("mds_gallery_action_press_cancel_for_held(") < gallery.index(
    "if(input.up&KEY_TOUCH)")
assert gallery.index("mds_gallery_action_press_cancel_for_physical(") < gallery.index(
    "if(input.up&KEY_TOUCH)")
print("PASS: physical down/up cancel touch, SELECT-up cannot export during stylus gesture")
