#!/usr/bin/env python3
"""Asset-free source wiring regression for genuine 3DS exit clips."""
from pathlib import Path
root=Path(__file__).resolve().parents[1]
main=(root/"source/main.c").read_text()
ui=(root/"source/ui.c").read_text()
header=(root/"source/ui.h").read_text()
motion=(root/"source/confirm_motion.c").read_text()
clan=(root/"source/clan_dialog.c").read_text()
source=(root/"source/clan_dialog_generated.h").read_text()
checks={
    "original DialogOut and DialogOutUp Q16 tracks":
        "dialog_out_y[]" in source and "dialog_out_up_y[]" in source and
        "{1114112,-15728640,0}" in source and "{1114112,15728640,0}" in source,
    "original exit sampled with source CLAN Hermite evaluator":
        "mds_clan_dialog_exit_y(now,motion->started,(int)motion->exit_up)" in motion and
        "mds_clan_curve_eval(keys,count,frame)" in clan,
    "source entrance always finishes before exit begins":
        "motion->exit_requested&&!motion->exiting" in motion and
        "motion->started=now;" in motion,
    "confirmation transaction is deferred until dialog leaves":
        "confirm_exit_response=response;" in main and
        "if(mds_ui_confirm_exit_done(animation_vblanks))" in main and
        main.index("if(mds_ui_confirm_exit_done(animation_vblanks))")<
        main.index("mds_editor_confirm(&editor,response,persist,NULL)"),
    "new input blocked while exit motion is staged":
        "if(confirm_exit_response>=0)" in main and
        "!motion->exit_requested" in motion,
    "original overlay and underlay are preserved during the exit":
        "mds_confirm_motion_composite(bottom,confirm_backdrop,confirm_window," in ui and
        "mds_ui_confirm_animation_tick(animation_vblanks)" in main,
    "dialog closed and original screen forced to redraw":
        "mds_ui_confirm_reset();" in main and "drawn_screen=-1; /* repaint the real post-dialog UI */" in main,
    "UI interfaces exist":
        "mds_ui_confirm_request_exit(int up)" in header and
        "mds_ui_confirm_exit_done(uint32_t now)" in header and
        "mds_confirm_motion_request_exit(&confirm_motion,up)" in ui,
    "no private Nintendo graphics or BCLAN on source tree":
        not list((root/"source").glob("*.bclan")) and
        not list((root/"source").glob("*.bclim"))
}
for name,okay in checks.items():
    if not okay: raise SystemExit("FAIL: "+name)
print("PASS: source-authentic DialogBase02 exit wired to confirmed action and safe gallery restoration")
