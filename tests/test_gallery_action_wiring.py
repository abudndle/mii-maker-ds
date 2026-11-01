#!/usr/bin/env python3
"""Ensure touch commands reuse the same save/permission paths as physical keys."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
main = (root / "source/main.c").read_text()
ui = (root / "source/ui.c").read_text()
editor = (root / "source/editor.c").read_text()
gallery = main.split("}else if(screen==MDS_SCREEN_GALLERY){", 1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){", 1
)[0]
assert "MdsGalleryTouchAction touch_action=MDS_GALLERY_ACTION_NONE;" in gallery
assert "if(down&KEY_TOUCH){" in gallery
assert "mds_gallery_action_press_begin(&gallery_action_press," in gallery
assert "mds_gallery_action_touch(input.touch.px,input.touch.py)" in gallery
assert "gallery_action_press.pressed==MDS_GALLERY_ACTION_NONE" in gallery
assert "mds_gallery_action_press_hold(&gallery_action_press," in gallery
assert "mds_gallery_action_press_release_for_slot(" in gallery
assert gallery.index("mds_gallery_action_press_release_for_slot(") < gallery.index(
    "if(touch_action==MDS_GALLERY_ACTION_EDIT)"
)
assert "mds_gallery_action_press_reset(&gallery_action_press);" in main
assert "gallery_controls.select_used=1;" in gallery
assert "if(touch_action==MDS_GALLERY_ACTION_EDIT)" in gallery
assert "gallery_action|=MDS_GALLERY_CONTROL_EDIT;" in gallery
assert "if(touch_action==MDS_GALLERY_ACTION_FAVORITE&&!(down&KEY_X))" in gallery
assert gallery.count("mds_editor_toggle_favorite(&editor,persist,NULL)") == 2
assert "else if(touch_action==MDS_GALLERY_ACTION_COPY)" in gallery
assert gallery.count("mds_editor_copy(&editor,persist,NULL)") == 2
assert "if(!mds_editor_locked(&gallery.miis[editor.slot]))" in gallery
assert "MDS_EDIT_COPY_RECEIVED" in gallery
assert "if(e->pending||mds_editor_dirty(e))" in editor
assert "e->draft=e->baseline;" in editor
assert "mds_original_gallery_action_icon_alpha(bottom,256,192," in ui
assert "24-(int)size/2,179-(int)size/2" in ui
assert "1,personal,alpha);" in ui
assert "98,169,20,20,2,0,balloon.balloon_alpha);" in ui
assert "181,169,20,20,3,0,balloon.balloon_alpha);" in ui
assert 'text_at(bottom,124,174,"Copy");' in ui
assert 'text_at(bottom,206,174,g->used[selected]?"Edit":"Create");' in ui
print("PASS: touch Favorite/Copy/Edit reuse existing permission and save flows")
