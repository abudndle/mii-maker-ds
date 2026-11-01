#!/usr/bin/env python3
"""Asset-free source checks for original 3DS gallery graphic/drag wiring."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
ui=(root/"source/ui.c").read_text()
main=(root/"source/main.c").read_text()
header=(root/"source/ui.h").read_text()
art=(root/"source/original_gallery_art.c").read_text()
gallery=ui[ui.index("void mds_ui_gallery(const"):]
input_branch=main.split("}else if(screen==MDS_SCREEN_GALLERY){",1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){",1)[0]
checks={
    "original room-tab art drawn from recovered panes":
        "mds_original_gallery_room_tab_tinted(bottom,256,192," in gallery and
        "const MdsMenuHit *tab=&gallery_room_hits[room];" in gallery,
    "original box art under Mii thumbnails":
        "mds_original_gallery_box_base(bottom,256,192" in gallery and
        gallery.index("mds_original_gallery_box_base(bottom,256,192") <
        gallery.index("mds_thumbnail_blit(&gallery_thumbnails"),
    "source original selection borders and safe fallback":
        "mds_original_gallery_box_border_tinted(bottom,256,192" in gallery and
        "outline(&gallery_hits[i]);" in gallery,
    "source art transparency preserved": "if(pixel&0x8000u)" in art,
    "source assets absent from public files": 'nitro:/art/Select/BtnMiiB.bin' in art and
        'nitro:/art/Select/BtnRoomEDITline01.bin' in art,
    "dimensions validated before blitting":
        "width==sprite->expected_width" in art and
        "height==sprite->expected_height" in art,
    "gamepad and touchscreen room paging while dragging":
        "mds_gallery_page_step(page,gallery_drag.source,direction)" in input_branch and
        "if((input.held&KEY_TOUCH)&&gallery_drag.source>=0)" in input_branch,
    "floating sprite is clipped and restores old VRAM backing":
        "static void gallery_drag_restore_under(void)" in ui and
        "gallery_drag_under_valid=0;" in ui and
        "gallery_drag_draw_at(x,y);" in ui,
    "drag follows live stylus instead of polling expensive thumbnails":
        "void mds_ui_gallery_drag_follow(int x,int y)" in ui and
        "mds_ui_gallery_drag_follow(live_touch_x,live_touch_y)" in main and
        "void mds_ui_gallery_drag_follow(int x,int y);" in header,
    "cancelled room-arrow release ends drag":
        "mds_gallery_drag_reset(&gallery_drag);" in input_branch,
}
for title,ok in checks.items():
    if not ok:raise SystemExit("FAIL: "+title)
print("PASS: original source Mii boxes and room tabs, input and live drag wiring")
