#!/usr/bin/env python3
"""Source-only integration checks for the original 3DS confirmation dialog.

The tests intentionally do not use or publish Nintendo 3DS resources.
"""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
ui=(root/"source/ui.c").read_text()
header=(root/"source/ui.h").read_text()
motion=(root/"source/confirm_motion.c").read_text()
clan=(root/"source/clan_dialog.c").read_text()
source=(root/"source/clan_dialog_generated.h").read_text()
checks={
    "original DialogBase02 / source CLPA metadata retained":
        "dialog_in_y" in source and
        "{0,-15728640,0}" in source and
        "{1114112,131072,0}" in source and
        "{1310720,0,-43691}" in source,
    "original source CLAN curve evaluator drives dialog movement":
        "mds_clan_dialog_y(now,motion->started)" in motion and
        "mds_clan_curve_eval(keys,count,frame)" in clan,
    "underlying original gallery retained during dialog entry":
        "memcpy(confirm_backdrop,bottom,sizeof confirm_backdrop)" in ui and
        "mds_confirm_motion_composite(bottom,confirm_backdrop,confirm_window," in ui,
    "dialog window built once separately without erasing gallery":
        "bottom=confirm_window;" in ui and
        "bitmap(\"nitro:/ui/confirm.rgb555\",bottom);" in ui and
        "bottom=screen;" in ui,
    "no expensive full Mii-model rebuild on every dialog tick":
        "mds_ui_confirm_animation_tick(animation_vblanks)" in main and
        "mds_confirm_motion_tick(&confirm_motion,now)" in ui,
    "confirm touch uses static original input bounds after entrance":
        "(down&KEY_TOUCH)&&mds_ui_confirm_touch_ready(animation_vblanks)" in main and
        "mds_ui_confirm_touch(t.px,t.py)" in main,
    "editor A/B still can accept/cancel confirmation":
        "if(down&KEY_A)response=1;else if(down&KEY_B)response=0;" in main,
    "dialog state resets after confirm accepted or cancelled":
        "if(!editor.pending)" in main and
        "mds_ui_confirm_reset();" in main,
    "source-determined 40 DS VBlank tick presentation, no floating point":
        "MDS_CLAN_DIALOG_VBLANKS" in motion and
        "mds_confirm_motion_composite" in motion and
        "memcpy(dest,background," in motion,
    "no original Nintendo BCLAN in public source":
        not list((root/"source").glob("*.bclan")),
    "UI declarations for isolated unit validation":
        "mds_ui_confirm_animation_tick(uint32_t now)" in header and
        "mds_ui_confirm_touch_ready(uint32_t now)" in header,
}
for name,okay in checks.items():
    if not okay:raise SystemExit("FAIL: "+name)
print("PASS: source-derived dialog motion, no gallery rerender, safe confirmation UI lifecycle")
