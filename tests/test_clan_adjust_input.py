#!/usr/bin/env python3
"""Static integration checks for real DS editor release/invalid feedback."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
ui=(root/"source/ui.c").read_text()
api=(root/"source/ui.h").read_text()
checks=[
 (".up=keysUp()" in main,"DS VBlank captures touch and key-up events"),
 ("mds_ui_editor_adjust_release(animation_vblanks,input.up);" in main,
  "editor forwards actual release events to UI"),
 ("mds_ui_editor_adjust_invalid_key(animation_vblanks,editor.field,-1)" in main,
  "left-key invalid feedback"),
 ("mds_ui_editor_adjust_invalid_key(animation_vblanks,editor.field,1)" in main,
  "right-key invalid feedback"),
 ("mds_clan_adjust_release(&editor_adjust_fx,now)" in ui,
  "original UnDecide release bound in editor"),
 ("mds_clan_adjust_invalid(&editor_adjust_fx,now" in ui,
  "original Invalid material state bound in editor"),
 ("memcmp(old_values,a->value,sizeof old_values)!=0" in ui,
  "bounded touch transform detects no-op"),
 ("cue.tint_rgb555,cue.opacity" in ui,
  "invalid animation uses source-derived opacity"),
 ("void mds_ui_editor_adjust_release" in api,
  "release API declared in DS header"),
]
for ok,description in checks:
 if not ok:raise SystemExit("FAIL: "+description)
print("PASS: DS key-up FIFO and editor invalid/release path integration")
