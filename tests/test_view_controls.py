#!/usr/bin/env python3
"""Regress original 3DS L/R Mii preview controls and cache coherency on DS."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
ui=(root/"source/ui.c").read_text()
head=(root/"source/head.c").read_text()
header=(root/"source/head.h").read_text()
original=(root/"tools/test_original_render.py").read_text()
editor=main.split("}else{\n            if(k&KEY_UP)",1)[1].split("if(screen==MDS_SCREEN_EDITOR&&mds_editor_locked",1)[0]
gallery=main.split("}else if(screen==MDS_SCREEN_GALLERY){",1)[1].split("}else if(screen==MDS_SCREEN_GENDER){",1)[0]
preview=ui.split("static int preview(",1)[1].split("static void paint_head(",1)[0]
checks={
 "L rotates left in editor": "if(down&KEY_L){if(mds_ui_view_step(-1))" in editor,
 "R rotates right in editor": "if(down&KEY_R){if(mds_ui_view_step(1))" in editor,
 "L/R no longer switch editor slots": "MDS_EDIT_PREV" not in editor and "MDS_EDIT_NEXT" not in editor,
 "gallery shoulder buttons cycle room Miis": "mds_gallery_slot_step(page,editor.slot,down&KEY_L?-1:1)" in gallery,
 "editor yaw reset when leaving": "mds_ui_view_scene(screen==MDS_SCREEN_EDITOR" in main,
 "camera yaw included in cache key": "preview_view[mode]!=requested_view" in preview,
 "cancelled preview rejects stale yaw": "preview_view[mode]==requested_view" in preview,
 "successful preview records yaw": "preview_view[mode]=requested_view" in preview,
 "original resource meshes rotated": "mds_view_rotate(&p[0],&p[2],view_angle)" in head,
 "original body vertices rotated": "mds_view_rotate(&px,&pz,view_angle)" in head,
 "front-facing export retains default": "return mds_mii_render_view(a,m,bytes,size,out,full,0);" in head,
 "view-aware head API exposed": "mds_head_render_view" in header,
 "original resource host rendering links camera": '"view"' in original.split("MODULES =",1)[1].split("\n",1)[0],
}
for name,done in checks.items():
 if not done:raise SystemExit("FAIL: "+name)
print("PASS: original Mii L/R view, gallery controls, model yaw, cache safety and front-facing exports")
