# BlocksDS Maxmod audio integration

Mii Maker DS now supports an **optional** NitroFS Maxmod soundbank for the
home-menu movement/confirm/cancel events. The existing original UI, 3D model
data, screenshots, saves, camera, and controls are preserved. The game does
not require audio assets to boot; if soundbank.bin is absent, the adapter is
silent and does not initialize Maxmod.

Maxmod ships in BlocksDS and the default ARM7 core supports it. The ARM9
Makefile links -lmm9 and the adapter loads a bank through
mmInitDefault("nitro:/soundbank.bin"). Avoid custom ARM7 firmware.

To add authorized original (or independently owned) sound effects in a private
workspace, create a NitroFS Maxmod bank with sample IDs 0, 1, 2 mapped to
movement, confirmation, and cancellation **respectively**. Use the BlocksDS
mmutil tool, and validate its generated soundbank.h sample indices before
packaging. Store the output at nitrofiles/soundbank.bin, which is gitignored.
If samples or formats differ, do not assume the ID order; the adapter must be
updated to the validated soundbank mapping. Do not publish original Nintendo
sound files or generated proprietary soundbanks.

References:
- https://blocksds.skylyrac.net/docs/libs/core_libs/
- https://blocksds.skylyrac.net/tutorial/basic/audio/
- https://blocksds.skylyrac.net/maxmod/md_documentation_2ds__programming__guide.html

Status: BlocksDS integration and event dispatch; no original audio bank
shipped, physical audio playback not yet verified. Future work should add
verified bank mapping, source-accurate 3DS audio timing, and options/settings
without replacing the existing UI.
