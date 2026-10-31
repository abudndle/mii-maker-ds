#!/usr/bin/env python3
"""Guard original 3DS received-Mii copy-before-edit UI flow and save policy."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
editor=(root/"source/editor.c").read_text()
main=(root/"source/main.c").read_text()
ui=(root/"source/ui.c").read_text()
header=(root/"source/editor.h").read_text()

request=editor.split("int mds_editor_request(",1)[1].split("int mds_editor_confirm(",1)[0]
confirm=editor.split("int mds_editor_confirm(",1)[1].split("int mds_editor_create(",1)[0]
gallery=main.split("}else if(screen==MDS_SCREEN_GALLERY){",1)[1].split("}else if(screen==MDS_SCREEN_GENDER){",1)[0]
modal=main.split("}else if(editor.pending){",1)[1].split("}else if(screen==MDS_SCREEN_HOME){",1)[0]
redraw=main.split("if(editor.pending)mds_ui_confirm(",1)[1].split(";",1)[0]

checks={
 "typed confirm action": "MDS_EDIT_COPY_RECEIVED" in header,
 "received Miis always read-only": "return a&&(a->value[61]&3)!=0;" in editor,
 "prompt only for received sources": "if(action==MDS_EDIT_COPY_RECEIVED)" in request and
                               "value[61]&1" in request,
 "special status blocks edit copying": "value[61]&2" in request,
 "permission blocks edit copying": "!e->gallery->miis[e->slot].value[48]" in request,
 "dirty drafts cannot be overwritten": 'mds_editor_dirty(e)' in request,
 "copy is not performed before confirmation": "e->pending=action;" in request,
 "copy calls transactional persist": "return mds_editor_copy(e,persist,ctx);" in confirm,
 "gallery A offers source copy": "gallery.miis[editor.slot].value[61]&1" in gallery and
                                  "mds_editor_request(&editor,MDS_EDIT_COPY_RECEIVED)" in gallery,
 "gallery editor direct path still works": "screen=MDS_SCREEN_EDITOR;" in gallery and
                                          "!mds_editor_locked(&gallery.miis[editor.slot])" in gallery,
 "confirmation happens before switching screen": "mds_editor_confirm(&editor,response,persist,NULL)" in modal and
                                            "if(response&&confirmed&&copy_prompt)" in modal,
 "successful copy selects new page": "page=editor.slot/10;" in modal,
 "successful copy returns to gallery": "editor_return_screen=MDS_SCREEN_GALLERY;" in modal,
 "cancel or failed save does not open editor": "response&&confirmed&&copy_prompt" in modal,
 "copy modal has distinct text": 'editor.pending==MDS_EDIT_COPY_RECEIVED?"Copy Mii to edit?"' in redraw,
 "modal uses original button/touch controls": "mds_ui_confirm_touch" in modal,
 "copy helper strips received status": "copy.value[61]=0;" in editor,
 "copy helper keeps received original": "copy=g->miis[e->slot]" in editor,
}
for description,okay in checks.items():
 if not okay:
  raise SystemExit("FAIL: "+description)
if modal.index("mds_editor_confirm(&editor,response,persist,NULL)") > modal.index("if(response&&confirmed&&copy_prompt)"):
 raise SystemExit("FAIL: editor opened before the copy was saved")
print("PASS: original 3DS received Mii copy-to-edit modal, permissions, rollback and source preservation")
