#!/usr/bin/env python3
"""Check gallery Favorite input cannot accidentally delete or export a Mii."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
main = (root / "source/main.c").read_text()
editor = (root / "source/editor.c").read_text()
gallery = main.split("}else if(screen==MDS_SCREEN_GALLERY){", 1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){", 1
)[0]
shortcut = gallery.split("if((down&KEY_X)&&!block_gallery_actions){", 1)[1].split(
    "if((down&KEY_Y)&&!block_gallery_actions)", 1
)[0]
assert "int block_gallery_actions=mds_gallery_drag_blocks_actions(" in gallery
assert "if(input.held&KEY_SELECT)" in shortcut
assert "gallery_controls.select_used=1;" in shortcut
assert "mds_editor_toggle_favorite(&editor,persist,NULL)" in shortcut
assert "else mds_editor_request(&editor,MDS_EDIT_DELETE);" in shortcut
assert "if(gallery_action&MDS_GALLERY_CONTROL_EXPORT)" in gallery
assert "if(e->pending||mds_editor_dirty(e))" in editor
assert "if(mds_editor_locked(&g->miis[e->slot]))" in editor
assert "e->draft=e->baseline;" in editor
print("PASS: SELECT+X Favorite consumes SELECT, retains X delete, and rolls back")
