#!/usr/bin/env python3
"""Check source-derived 3DS choice playback and main-loop integration."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
ui=(root/"source/ui.c").read_text()
header=(root/"source/confirm_choice.h").read_text()
paint=(root/"source/confirm_choice.c").read_text()
motion=(root/"source/confirm_motion.c").read_text()
assert "mds_ui_confirm_choose(response,animation_vblanks)" in main
assert "confirm_exit_response=response;" in main
assert "mds_ui_confirm_exit_done(animation_vblanks)" in main
assert "MDS_CONFIRM_CHOICE_VBLANKS" in motion
assert "mds_confirm_motion_request_exit(motion,0)" in motion
assert "mds_confirm_motion_choose(&confirm_motion,yes,now)" in ui
assert "mds_confirm_choice_tint(confirm_window," in ui
assert "confirm_motion.choice_tinted=1;" in ui
assert '"nitro:/ui/confirm.rgb555"' in ui
assert "71u:111u" in paint
assert "r*50u+50u" in paint and "g*163u+95u" in paint and "b*112u+74u" in paint
assert "six-frame clip" in header
assert not list((root/"source").glob("*.bclan"))
print("PASS: verified source CLMC button feedback and original exit phase safely wired")
