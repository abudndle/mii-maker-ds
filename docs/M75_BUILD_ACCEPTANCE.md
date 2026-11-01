# Milestone 75 — private ROM acceptance gate

The latest source is not considered a verified playable build until all steps pass against the user's own private resource archive.

1. Run `python3 tools/build_private.py MiiMaker_DS_Resources.zip --no-cache --jobs 4` in a configured BlocksDS environment. This invokes the full original-resource validation, source and body-model checks, actual ARM9/ARM7 compilation, and packed-ROM verification.
2. Preserve the resulting `mii-ds.nds` privately; do not commit it or Nintendo assets to GitHub.
3. Boot the **new** ROM in melonDS, DS mode with Direct Boot, and verify menu, gallery, several Miis per room, original animation playback, drag-and-drop, physical L/R navigation, editor, save, reset and saved state restoration.
4. Capture fresh screenshots from the newly compiled ROM and compare to source 3DS layout and colors. The previously compiled `mii-maker-ds-title-corrected.nds` is an older checkpoint and does not verify M72–M74.
5. Record ROM and ZIP SHA-256, compiler versions, emulator version and results in a private release log.

The original archive independently inspected in the November 1 checkpoint contains 3,575 entries and passes ZIP CRC verification. This does **not** replace the complete private build script's validation. A successful synthetic CI compilation does **not** establish the new private ROM's runtime correctness.

Current blocker in this execution environment: no configured BlocksDS compiler, Docker or melonDS executable; GitHub Actions' synthetic smoke builds cannot substitute for a private original-resource build.
