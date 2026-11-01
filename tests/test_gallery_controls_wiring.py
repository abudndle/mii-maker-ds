#!/usr/bin/env python3
"""Prevent regression of the DS gallery SELECT+A chord and export routing."""
from pathlib import Path

main = (Path(__file__).resolve().parents[1] / "source/main.c").read_text()
gallery = main.split("}else if(screen==MDS_SCREEN_GALLERY){", 1)[1].split(
    "}else if(screen==MDS_SCREEN_GENDER){", 1
)[0]
required = (
    "mds_gallery_controls_step(&gallery_controls,",
    "(down&KEY_A)!=0,(input.held&KEY_A)!=0",
    "(down&KEY_SELECT)!=0,(input.held&KEY_SELECT)!=0",
    "(input.up&KEY_SELECT)!=0",
    "if(gallery_action&MDS_GALLERY_CONTROL_RECALL)",
    "if(gallery_action&MDS_GALLERY_CONTROL_EDIT)",
    "if(gallery_action&MDS_GALLERY_CONTROL_EXPORT)",
    "mds_gallery_controls_reset(&gallery_controls);",
)
for expression in required[:-1]:
    assert expression in gallery, f"Gallery input routing missing: {expression}"
assert required[-1] in main, "Gallery chord state must reset on scene exit"
assert "k&KEY_SELECT" not in gallery, "SELECT held state must not use key-repeat bits"
assert "if(down&KEY_SELECT)editor.status" not in gallery, (
    "Export must be deferred until standalone SELECT release"
)
print("PASS: gallery SELECT+A uses held state, and SELECT export is release-only")
