#!/usr/bin/env python3
"""Guard real top-screen room navigation's walk-phase persistence wiring."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ui = (root / "source/ui.c").read_text()
gallery = ui[ui.index("void mds_ui_gallery_top("):ui.index("int mds_ui_gallery_retry_pending(")]
switch = gallery[gallery.index("if(walk_room_start!=start){"):gallery.index("/* Animation clock is sampled")]

checks = {
    "ten rooms retain independent phase state":
        "static unsigned walk_phase_saved[MDS_SLOTS/MDS_ROOM_SLOTS];" in ui,
    "room switch restores the saved phase":
        "walk_ticks=mds_room_walk_resume(walk_phase_saved,\n"
        "                                        previous_room_start,start,walk_ticks);" in switch,
    "room switch does not reset phase to zero": "walk_ticks=0;" not in switch,
    "new room rebases its VBlank clock": "walk_last_clock=animation_clock;" in switch,
    "A recall still returns Miis to their home spots":
        "walk_home_remaining=24u;" in ui and
        "mds_room_walk_tick(&room_walk[local],local,0,1);" in ui,
    "menu time is excluded from walking":
        "void mds_ui_room_pause(void)" in ui and
        "walk_last_clock=animation_clock;" in ui,
    "ten independent walkers still composite on top screen":
        "mds_room_walk_tick(&room_walk[local],local,walk_ticks,walk_home_remaining!=0u);" in gallery,
}
for name, valid in checks.items():
    if not valid:
        raise SystemExit("FAIL: " + name)
print("PASS: room walk phases survive navigation without changing recall or pause")
