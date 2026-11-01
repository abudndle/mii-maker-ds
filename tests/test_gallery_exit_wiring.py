#!/usr/bin/env python3
"""Back must take precedence over every gallery mutation on the same frame."""
from pathlib import Path

main = (Path(__file__).resolve().parents[1] / "source/main.c").read_text()
gallery = main.split("}else if(screen==MDS_SCREEN_GALLERY){", 1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){", 1
)[0]
guard = gallery.index("if(down&KEY_B){")
cancel = gallery.index("mds_gallery_cancel_for_exit(", guard)
home = gallery.index("screen=MDS_SCREEN_HOME;", cancel)
otherwise = gallery.index("}else{", home)
end = gallery.rindex("} /* Only non-B gallery input may reach mutations above. */")
assert guard < cancel < home < otherwise < end
assert "if(down&KEY_B)screen=MDS_SCREEN_HOME;" not in gallery
for operation in (
    "mds_gallery_drag_end(",
    "mds_editor_move(",
    "mds_editor_copy(",
    "mds_editor_toggle_favorite(",
    "mds_editor_request(&editor,MDS_EDIT_DELETE)",
    "mds_ui_export_image(",
):
    pos = gallery.index(operation)
    assert otherwise < pos < end, operation
assert "&gallery_drag_arrow_latch" in gallery[guard:otherwise]
print("PASS: B/Back bypasses all same-frame gallery mutations and clears input")
