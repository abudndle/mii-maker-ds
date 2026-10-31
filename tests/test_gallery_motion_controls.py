#!/usr/bin/env python3
"""Check gallery clip controls and female animation name matching are wired."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ui = (root / "source/ui.c").read_text()
main = (root / "source/main.c").read_text()
header = (root / "source/ui.h").read_text()

def require(found, message):
    if not found:
        raise SystemExit("FAIL: " + message)

gallery = main.split("}else if(screen==MDS_SCREEN_GALLERY){", 1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){", 1
)[0]
require("mds_ui_motion_step(-1)" in gallery and "down&KEY_UP" in gallery,
        "gallery UP does not select previous original clip")
require("mds_ui_motion_step(1)" in gallery and "down&KEY_DOWN" in gallery,
        "gallery DOWN does not select next original clip")
require("mds_ui_motion_auto()" in gallery and "down&KEY_START" in gallery,
        "gallery START does not resume idle autoplay")
require("int mds_ui_motion_step(int direction)" in ui and
        "int mds_ui_motion_auto(void)" in ui,
        "gallery playback control implementation missing")
require("mds_motion_cycle(&motions[0],gallery_selected_clip,direction)" in ui,
        "gallery navigation no longer uses checked catalog cycling")
require("gallery_selected_clip=-1" in ui and
        "gallery_selected_clip>=0)clip=gallery_selected_clip" in ui,
        "manual selection no longer overrides idle autoplay")
require("mds_motion_find(&motions[1],motions[0].clips[i].name)" in ui,
        "female clip map must resolve original male clip names")
require("gallery_female_by_male[motion_clip]" in ui and
        "gallery_female_by_male[clip]" in ui,
        "preview and redraw must both resolve female clip by name")
require("Motion: %s" in ui and "UP/DOWN: Clip   START: Auto" in ui,
        "gallery does not display selected clip and controls")
require("mds_ui_motion_step(int direction)" in header and
        "mds_ui_motion_auto(void)" in header,
        "public UI control declarations missing")
print("PASS: original 53-clip gallery controls, autoplay and gender name matching")
