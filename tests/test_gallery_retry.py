#!/usr/bin/env python3
"""Protect interrupted Nintendo DS gallery preview retry and cache behavior."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
ui = (root / "source/ui.c").read_text()
main = (root / "source/main.c").read_text()
header = (root / "source/ui.h").read_text()
top = ui[ui.index("void mds_ui_gallery_top("):ui.index("int mds_ui_gallery_retry_pending(")]
gallery = ui[ui.index("void mds_ui_gallery("):ui.index("static const uint8_t profile_colors", ui.index("void mds_ui_gallery("))]
main_redraw = main[main.index("int animate=0;"):main.index("}else if(!camera_open&&animate){")]
checks = (
    ("pending flag declared", "static int gallery_retry_pending;" in ui),
    ("pending state exposed", "int mds_ui_gallery_retry_pending(void)" in header),
    ("pending state reset on gallery draw", "gallery_retry_pending=0;" in gallery),
    ("selected full-body cancellation tracked", "if(render_cancelled_count!=before_cancel)gallery_retry_pending=1;" in top),
    ("thumbnail cancellation tracked", "if(render_cancelled_count!=before_cancel)gallery_retry_pending=1;" in gallery),
    ("thumbnail rendered only if ready", "if(ready)mds_thumbnail_capture(" in gallery),
    ("retry only when no input waiting", "mds_ui_gallery_retry_pending()&&!input_waiting()" in main_redraw),
    ("redraw only in gallery", "screen==MDS_SCREEN_GALLERY&&mds_ui_gallery_retry_pending()" in main_redraw),
)
for name, ok in checks:
    if not ok:
        raise SystemExit("FAIL: " + name)
if gallery.index("gallery_retry_pending=0;") > gallery.index("mds_ui_gallery_top("):
    raise SystemExit("FAIL: gallery retry flag resets after top draw")
if gallery.index("mds_thumbnail_page(") > gallery.index("if(ready)mds_thumbnail_capture("):
    raise SystemExit("FAIL: gallery thumbnail cache page not selected before capture")
print("PASS: interrupted gallery renders retry when idle without caching incomplete thumbnails")
