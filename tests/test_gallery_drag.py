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
    "VBlank records key-up and stylus release": ".up=keysUp()" in irq,
    "track last held touch position": "if(live_held&KEY_TOUCH){live_touch_x=current.px;live_touch_y=current.py;}" in irq,
    "release position preserved": "event.touch.px=live_touch_x;event.touch.py=live_touch_y;" in irq,
    "release has priority over key repeats": "if(!(event.down||event.up)&&queued>=23)return;" in irq,
    "release not discarded on full queue": "if(!(event.down||event.up))return;" in irq,
    "touch-down selects tapped occupied box": "editor.slot=(unsigned)slot;" in gallery and
                                 "slot>=0&&gallery.used[slot]" in gallery,
    "touch-down captures occupied source for optional drag": "mds_gallery_drag_begin(&gallery_drag,page,slot,1)" in gallery,
    "touch release ends drag": "if(input.up&KEY_TOUCH){" in gallery and "mds_gallery_drag_end(&gallery_drag,page," in gallery,
    "drag destination from original hitboxes": "mds_gallery_touch(input.touch.px,input.touch.py,page)" in gallery,
    "gallery keeps original artwork without placeholder labels": "text_at(bottom,103,10,\"ROOM\")" not in (root/"source/ui.c").read_text(),
    "tap selects without requiring a drop move": "Tap box to select; drag the Mii" in (root/"source/ui.c").read_text(),
    "drag renders Mii sprite instead of moving box": "mds_thumbnail_blit(&gallery_thumbnails,page,local,bottom,256,192,gallery_drag_x-21,gallery_drag_y-23)" in (root/"source/ui.c").read_text() and "if(slot==selected)outline(&gallery_hits[i]);" in (root/"source/ui.c").read_text(),
    "physical L/R navigate rooms when idle": "mds_gallery_page_step(page,editor.slot,direction)" in gallery,
    "physical L/R browse destination while dragging": "mds_gallery_page_step(page,gallery_drag.source,direction)" in gallery and
                                      "gallery_drag.source>=0" in gallery,
    "continuous touch drag browses rooms over arrows": "if((k&KEY_TOUCH)&&gallery_drag.source>=0)" in gallery and
                                      "mds_gallery_page_step(page,(unsigned)gallery_drag.source,arrow)" in gallery,
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
assert "unsigned source=0;" in gallery
print("PASS: touchscreen gestures, shoulder Mii cycling, input release and persistent Mii move/swap rollback")
