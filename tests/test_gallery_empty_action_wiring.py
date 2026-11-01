#!/usr/bin/env python3
"""M81: empty selected boxes expose Create but never phantom Favorite/Copy."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
main = (root / "source/main.c").read_text()
ui = (root / "source/ui.c").read_text()
gallery = main.split("}else if(screen==MDS_SCREEN_GALLERY){", 1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){", 1)[0]
guard = """if(!gallery.used[editor.slot]&&
               (touch_action==MDS_GALLERY_ACTION_FAVORITE||
                touch_action==MDS_GALLERY_ACTION_COPY))
                touch_action=MDS_GALLERY_ACTION_NONE;"""
assert guard in gallery
assert gallery.index("mds_gallery_action_press_release_for_slot(") < gallery.index(guard)
assert gallery.index(guard) < gallery.index(
    "if(touch_action==MDS_GALLERY_ACTION_EDIT)")
assert 'if(g->used[selected]&&mds_ui_gallery_actions_visible(now)){\n        text_at(bottom,38,174,' in ui
assert 'text_at(bottom,124,174,"Copy");' in ui
assert 'text_at(bottom,206,174,g->used[selected]?"Edit":"Create");' in ui
print("PASS: empty gallery slots show Create without phantom Favorite/Copy")
