#!/usr/bin/env python3
"""Guard DS Mii editor's origin-aware B-button exit and confirmation flow."""
from pathlib import Path

source = (Path(__file__).resolve().parents[1] / "source" / "main.c").read_text()
required = {
    "remember editor origin": "editor_return_screen=MDS_SCREEN_HOME,pending_editor_return=0;",
    "gallery origin for existing Miis": "editor_return_screen=MDS_SCREEN_GALLERY;\n                    screen=MDS_SCREEN_EDITOR;",
    "origin for newly created Miis": "editor_return_screen=gender_return_screen;\n                screen=MDS_SCREEN_EDITOR;",
    "gallery-origin new Mii": "gender_return_screen=MDS_SCREEN_GALLERY;",
    "home-origin new Mii": "gender_return_screen=MDS_SCREEN_HOME;",
    "deferred exit on dirty draft": "if(editor.pending)pending_editor_return=1;",
    "immediate exit on clean draft": "else screen=editor_return_screen;",
    "confirmed return to origin": "else if(response&&confirmed&&pending_editor_return)\n                    screen=editor_return_screen;",
    "cancel confirmation leaves editor open": "pending_editor_return=0;",
}
for name, snippet in required.items():
    if snippet not in source:
        raise SystemExit("FAIL: missing " + name)
if "return_home" in source or "if(response&&return_home)screen=MDS_SCREEN_HOME;" in source:
    raise SystemExit("FAIL: legacy hardcoded HOME exit is still present")
# A confirmed discard must be successful before navigating. A rejection
# from the confirmation dialog must keep the current editor active.
confirm = source[source.index("}else if(editor.pending){"):source.index("}else if(screen==MDS_SCREEN_HOME){")]
if confirm.index("int confirmed=mds_editor_confirm(") > confirm.index("else if(response&&confirmed&&pending_editor_return)"):
    raise SystemExit("FAIL: screen changes before discard is confirmed")
print("PASS: Mii editor returns to gallery or home only after successful discard")
