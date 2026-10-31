#!/usr/bin/env python3
"""Regress touch drag sorting, release delivery and transactional gallery moves."""
from pathlib import Path

root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
editor=(root/"source/editor.c").read_text()
api=(root/"source/editor.h").read_text()
irq=main[main.index("static void animation_vblank(void)"):
         main.index("static MdsInput next_input(void)")]
gallery=main.split("}else if(screen==MDS_SCREEN_GALLERY){",1)[1].split(
        "}else if(screen==MDS_SCREEN_GENDER){",1)[0]
move=editor[editor.index("int mds_editor_move("):editor.index("int mds_editor_copy(",editor.index("int mds_editor_move("))]

checks={
    "release event field": "int down,repeat,held,up;touchPosition touch;" in main,
    "VBlank stylus release detection": ".up=keysUp()&KEY_TOUCH" in irq,
    "track last held touch position": "if(live_held&KEY_TOUCH){live_touch_x=current.px;live_touch_y=current.py;}" in irq,
    "release position preserved": "event.touch.px=live_touch_x;event.touch.py=live_touch_y;" in irq,
    "release has priority over key repeats": "if(!(event.down||event.up)&&queued>=23)return;" in irq,
    "release not discarded on full queue": "if(!(event.down||event.up))return;" in irq,
    "touch-down captures occupied source": "if(down&KEY_TOUCH){" in gallery and
                                 "mds_gallery_drag_begin(&gallery_drag,page,slot," in gallery and
                                 "slot>=0&&gallery.used[slot]" in gallery,
    "touch release ends drag": "if(input.up&KEY_TOUCH){" in gallery and "mds_gallery_drag_end(&gallery_drag,page," in gallery,
    "drag destination from original hitboxes": "mds_gallery_touch(input.touch.px,input.touch.py,page)" in gallery,
    "preserve original source across pages": "mds_gallery_page_step(page,editor.slot" in gallery and
                                            "page==drag_page" not in gallery,
    "reject empty source": "slot>=0&&gallery.used[slot]" in gallery,
    "persist gallery move": "mds_editor_move(&editor,(unsigned)destination,persist,NULL)" in gallery,
    "cancel drag after leaving gallery": "if(screen!=MDS_SCREEN_GALLERY)mds_gallery_drag_reset(&gallery_drag);" in main,
    "public sorting API": "int mds_editor_move(MdsEditor *,unsigned destination,MdsPersist,void *);" in api,
    "move or swap two saved Mii records": "g->miis[destination]=old_source;" in move and
                                           "g->miis[source]=old_dest;" in move,
    "restore both slots on failed write": "g->miis[source]=old_source;g->miis[destination]=old_dest;" in move,
    "restore old generation and bank": "g->generation=generation;g->active_bank=bank;" in move,
    "reload selected Mii after moving": "e->slot=destination;" in move and "reload(e);" in move,
}
for label,okay in checks.items():
    if not okay:
        raise SystemExit("FAIL: "+label)
# Both source and destination must be resolved while in the gallery branch,
# and the source must be captured before seeing the destination.
assert gallery.index("mds_gallery_drag_begin(&gallery_drag,page,slot,") < gallery.index("if(input.up&KEY_TOUCH){")
assert gallery.index("if(input.up&KEY_TOUCH){") < gallery.index("mds_editor_move(&editor,")
assert gallery.index("mds_gallery_drag_end(&gallery_drag,page,") < gallery.index("mds_editor_move(&editor,")
assert "drag_page" not in gallery
assert "unsigned source;" in gallery
print("PASS: cross-page stylus gestures, input release and persistent Mii move/swap rollback")
