#!/usr/bin/env python3
"""Guard first-boot Personal Mii creation without trapping missing-save users."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
main = (root / "source/main.c").read_text()
editor = (root / "source/editor.c").read_text()
save = (root / "source/save.c").read_text()
before_loop = main.split("for(;;){", 1)[0]
gender = main.split("}else if(screen==MDS_SCREEN_GENDER){", 1)[1].split(
    "}else if(screen==MDS_SCREEN_PROFILE){", 1
)[0]
editor_input = main.split("}else{\n            if(k&KEY_UP)", 1)[1].split(
    "if(screen!=MDS_SCREEN_GALLERY)mds_gallery_drag_reset", 1
)[0]
assert "save_ready&&mds_gallery_empty(&gallery)" in before_loop
assert "mds_editor_create(&editor,0)" in before_loop
assert "mds_profile_open(&profile,&editor.draft,MDS_PROFILE_GENDER)" in before_loop
assert "screen=MDS_SCREEN_GENDER;" in before_loop
assert "if(save_ready&&mds_gallery_empty(&gallery))" in gender
assert "screen=gender_return_screen;" in gender  # only optional creation cancels
assert "if(save_ready&&mds_gallery_empty(&gallery))" in editor_input
assert "Save your first Mii before leaving." in editor_input
assert "mds_editor_save(&editor,persist,NULL)" in editor_input
assert "if(!personal){e->draft.value[51]=1;e->draft.value[46]=1;}" in editor
assert "if(!g)return 0;" in save.split("int mds_gallery_empty(", 1)[1].split(
    "static int valid(", 1
)[0]
print("PASS: first-boot Personal Mii creation, cancellation guard and save-unavailable escape")
