# Mii Maker DS — original-resource development build
this is ai project dont look into this page please i was originally trying to keep it private but i cant do that 
anynore so dont mind the notes and messages you read in the code
im just playing with ai for fun
This is an unfinished Nintendo DS/DSi demake of 3DS Mii Maker. **The melonDS blank-screen fault is corrected**, and the supplied `CFL_Res.dat` now drives a real head preview in the editor and saved-gallery thumbnails. This is not a complete or pixel-identical 3DS port.

## Run the corrected ROM

Open **`mii-ds.nds`** in melonDS with **DS console mode** and **Direct Boot** enabled. These are the tested settings. The build remains DSi-enhanced, but DSi boot/camera hardware testing is still outstanding. Close the older ROM before opening the corrected file.

The ROM has been tested with the current melonDS DS libretro core 1.4.0, its underlying melonDS engine, an older melonDS 0.9.3 core, and DeSmuME 2015. The tests exercise actual emulated ARM execution, embedded assets, touch routing, editing, cartridge saving and separate-process restart. This is not a standalone GUI test on the user's machine.

Two packaging errors caused melonDS failures: the DSi region boundary was zero for a custom game code, hiding embedded assets from the retail-style cartridge reader; and the reserved secure-area prefix lacked the decrypted marker required by the current core with built-in BIOS. The build now corrects both automatically. If asset initialization ever fails, the app displays an error instead of leaving both screens blank.

## Original assets and code mapping

See **`reference/SOURCE_MAP.md`** and **`reference/SOURCE_MAP.json`**. These connect all 94 extracted original layouts, 62 stored profile fields and 369 embedded runtime assets to the DS implementation. The original compiled 3DS executable is retained as evidence; Nintendo's source code is not available. Its ARM11/OS/PICA code is not executed directly on DS hardware.

The app uses original main-menu textures, labels, layout bounds, editor pages, feature icons and the gallery grid. The profile, creation gender picker, accessory selector and touch confirmation now use original layouts and widget art. Mirrored pane origins are corrected, restoring complete button shapes. Birthday numerals use the original extracted Nintendo number font; other text uses a substitute font. Material effects, complete animation coverage, upper-screen plaza and the full international keyboard remain incomplete. Primary texture wrapping is corrected for the menu/gallery background.

The supplied `nitrofiles/cfl/CFL_Res.dat` contains the original face meshes and feature textures. `source/cfl_resource.c` parses its sections; `source/head.c` renders face/mask, hair, forehead, caps, noses, glasses, facial hair, eyes, brows, mouth, mole, makeup and lines using the selected appearance fields. Projection, lighting, texture sampling and material composition are provisional. The original male/female body geometry, skeleton and original skeletal motions now render too; the body editor shows a full-body view with live height/build/shirt updates. The streamed player supports all 53 original skeletal clips at every integer source frame; the editor uses Wait00, and the gallery automatically cycles through six original idle clips or lets the player choose any of the 53 clips with UP/DOWN (START restores autoplay). Exact original frame rate, full animation coverage and exact body proportion coefficients remain incomplete. Host tests exercise all 132 hairstyle selections and 12 face meshes, but do not establish pixel accuracy for every combination.

**`CFL_DB.dat` / `CFL.DB.dat` is not required, embedded, imported or used.** The previously supplied database was discarded from the project. Miis start in an empty gallery.

## Controls and implemented flow

- Main menu: touch View or Create (then choose gender); D-pad up/down and A also select entries. Send/Receive opens the standard Mii file-import browser. QR Code/Image Options uses the original QR menu; camera scanning is visible only in DSi mode.
- Gallery: touch a slot, A edits it, X requests deletion, Y copies when allowed, SELECT exports an image, L/R pages, B returns home. Saved slots show original-resource head previews.
- Editor: touch feature tabs/icons, arrows, color swatches, hair flip or body sliders. Hold and drag either body slider freely; capture continues outside its track and clamps at the ends. Controls update while dragging; the software model preview refreshes after a brief pause or release. D-pad up/down selects fields; left/right or A adjusts a field. Original move/size/rotation/spacing/stretch buttons and reset now update the preview, and original face subtabs are wired. The original accessory tab opens the glasses, mustache, beard and mole selector.
- START saves. L/R changes slots; SELECT opens Profile. Edit nickname/creator (10 UTF-16 units), gender, shirt color, birthday, favorite, sharing and copying permissions. The DS touch keyboard provides ASCII letters, digits and basic punctuation; unchanged Unicode names are retained. X backspaces, Y changes case, and X clears a birthday. Modal changes require Done; B cancels. At most ten favorites are allowed. The first locally created Mii is Personal, always a Favorite and protected from deletion. Received Miis with copying disabled are viewable but locked against editing and copying. Copies clear Personal/Favorite flags. B returns home, asking before discarding edits; use original Yes/No touch buttons or A/B. B+Y requests deletion.
- Y requests the DSi-only camera. DS/DS Lite displays the camera gate. The compiled DSi controller supports A freeze/resume, X switch, B close, but remains untested on DSi hardware. Photo-to-Mii recognition is not implemented.

Software preview drawing is cached independently for head thumbnails, portraits and full-body views. New input cancels an unfinished model redraw and keeps the last complete frame; a VBlank input queue preserves short taps. The top screen is composed offscreen before presentation, avoiding partially erased models. Gallery thumbnails can still take time to populate. Physical DS/DSi performance is unmeasured; a hardware 3D backend is still needed for full animation.

## Cartridge saves

New saves use an **8 KiB EEPROM snapshot**, compatible with melonDS's default for an unknown cartridge. The format stores 100 slots, all 62 fields, settings, a generation and CRC. Names and creator names follow the original limit of **10 UTF-16 units**; invalid or longer names are refused without silently truncating them. The temporary runtime font remains ASCII-only.

Existing valid **64 KiB** project saves retain their legacy two-bank format on a device configured for that size. DeSmuME tests use 64 KiB/two-address-byte EEPROM and cover both old-bank loading and new compact snapshots. Miis stay in the ROM-associated save rather than individual SD files. Unknown nonblank save images are refused. Real flashcart mappings are not verified.

The new compact format has one full snapshot: its CRC detects interrupted/corrupt writes, but it does not provide the old 64 KiB format's second-bank recovery. A failed write retains the in-memory draft; it cannot guarantee recovery of a snapshot interrupted during writing. Legacy saves should be backed up before changing emulator save configuration.

## Build

Install **BlocksDS 1.24.0**, Wonderful's ARM toolchain, GNU make and Python 3. Setup: https://blocksds.skylyrac.net/docs/setup/linux/ . Run `make` in this directory. Override `BLOCKSDS` and `WONDERFUL_TOOLCHAIN` for your installation. The included Makefile defaults to `/opt/wonderful/thirdparty/blocksds/core` and `/opt/wonderful`.

The outer Makefile delegates compilation/packing to the SDK and runs `tools/fix_nds_regions.py` after packing, even for an otherwise up-to-date ROM. The postprocessor aligns DSi payloads to 512 KiB, preserves ARM instructions/NitroFS data, marks the reserved decrypted prefix, sets capacity/boundary/lengths and updates CRCs. The result is `mii-ds.nds`. Do not distribute an intermediate SDK-packed image before this step. `make clean` and `make dump` delegate to the SDK too.

Original asset extraction can be repeated with `tools/extract.py`, `unpack.py`, `textures.py`, `layouts.py`, `ui_hitboxes.py`, `menu_assets.py` and `source_map.py`. Image tools require Pillow. Extraction uses the user's supplied application and DS reference; no original ROM is downloaded.

## Validation and remaining features

`validation/report.json` records hashes, pinned emulator revisions and tested scope. `tests/rom_regions.py` checks the actual packed image's DS/DSi boundary, header CRC, unchanged payloads, accessible NitroFS and repeatable postprocessing. `tests/head.c` exercises the genuine supplied archive with address/undefined-behavior sanitizers; `tests/save_compact.c` checks 100 slots, all fields, Unicode, limits, corruption and truncation. Other portable tests cover the legacy save, editor transactions and menu bounds.

`tools/emulator_melonds_test.py` tests current/older melonDS DS direct boot, original head editing, save and `--restart`; it implements normal libretro frontend SRAM persistence. It does not modify guest RAM. DeSmuME scripts use interpreter mode and `tests/emulator-frontend.patch` to select the existing 64 KiB EEPROM setting. That patch exposes frontend configuration/inspection only. Emulator binaries are not bundled.

Direct wireless DS/3DS/Wii/Wii U interoperability, photo-to-Mii recognition, original JPEG export, remaining animation scene bindings, sound, the full international keyboard and remaining modal flows remain unfinished. Standard Mii file import, authenticated QR generation and the portable QR image scanner are implemented; physical SD/camera/stock-device compatibility remains unverified. See `FEATURES.md`. Camera remains exclusive to DSi mode.


## Original body and editor presentation update

`reference/BODY_RENDERING.md` and `body-models.json` trace original model/rig/pose data to DS code. The editor and gallery now use original body geometry attached to CFL heads. Development titles, slot lists and numeric-field overlays are removed; proportional substitute text is used. Original alpha-only icon tint, multi-texture button masks and texture wrapping are applied across the editor. Original slider knobs follow their values. The renderer uses streamed original skeletal animation poses, while camera/light/material fidelity, source frame-rate matching and body proportion coefficients remain provisional. Nintendo's shared font is still unavailable.

Regenerate body binaries with `python3 tools/body_models.py` (NumPy required), and the proportional substitute glyphs with `python3 tools/ui_font.py` (Pillow and DejaVu Sans required). Build-time use of generated assets does not require those regeneration dependencies. `tests/body.c` checks both bodies, framing and live parameters; `tests/transform.c` checks original control semantics and clamped/reset behavior. The melonDS test's `--appearance` option exercises original transform/reset buttons, face subtabs, body sliders and shirt recoloring through actual inputs.

## Profile and graphics update

`reference/PROFILE_FLOWS.md` records the implemented profile behavior and its limits. Regenerate its original assets with `tools/profile_assets.py`, the original numeral font with `tools/number_font.py`, and the original SMDH-derived banner icon with `tools/banner_icon.py`. `tests/profile.c` covers validation and cancellation; `tools/emulator_profile_test.py` exercises real melonDS touch input, copy/delete policy and cold-restart persistence. `CFL_Res.dat` remains the required embedded head resource; `CFL_DB.dat` remains unused.

## Original idle animation, free sliders and image export

`tools/motion_pack.py` evaluates all 53 original clips at every integer source frame. MSP1 streams a 912-byte frame of original bone/head transforms from NitroFS and applies it to the existing original mesh, instead of keeping repeated complete meshes in RAM. BOD3 uses wide coordinates so original scene motion is retained. Source timing is still assumed to be 30 fps; rendering can drop poses to prioritize input. The editor plays Wait00; the gallery automatically sequences Wait00/Wait01/Wait02/Wait03Pre/Wait03/Wait04. In gallery view, UP/DOWN browse all 53 original skeletal clips and START returns to the six-idle playlist. Clip labels appear on the upper screen. That playlist is independently authored; the original scene/event choreography is not yet recovered. Older 24-pose ANI1 files remain a fallback if the runtime is used with older resources.

Body slider capture follows the latest held stylus coordinate, even outside the track, until release. Values span the full 0–127 range. A cached original body-editor background avoids repeated cartridge reads while dragging. Expensive model rendering waits until a brief pause or release; the slider knob moves independently.

Gallery SELECT exports a 128×128, 24-bit BMP of the selected Mii into `MiiMaker/Images` on the DSi SD card or DS flashcart card. Sharing must be allowed. Filenames never overwrite an existing image; write failures remove incomplete output. This is a DS image-export adaptation, not original JPEG/QR functionality. The BMP encoder and missing-card/permission paths are tested; physical SD writes remain untested. Mii records continue using the ROM-associated save.

`tests/animation.c` renders every original sampled pose and checks animation bounds, wrap, cancellation and malformed data. `tests/image.c` and independent Pillow decoding check BMP layout, colors, padding, transparency and write failure. The melonDS test options `--sliders --animation --image` exercise continuous stylus movement, endpoint clamps, release, actual visible idle motion and missing-card export handling.

`reference/PERFORMANCE.md` documents the fixed-point/scanline optimization, immutable facial-mask cache and measured emulator limits. Improved responsiveness does not establish full 3DS visual parity or a smooth hardware frame rate.

## Standard Mii data, original QR GUI and SD photos

`reference/FEATURE_PORT_MAP.md` and `MII_EXCHANGE.md` trace the original fields, layouts and runtime components. `mii-fields.json` maps all imported appearance/profile values to standard 96-byte Mii records. Put `.cfsd` / `.ffsd` files in `MiiMaker/Import` on the SD card. Send/Receive opens the file browser; choose a record and Import. A copied incoming Mii becomes received, retains sharing/copying policy, and never acquires Personal ownership from a foreign identity. Full original record identity remains in the source file; the private gallery stores appearance/profile/status rather than every original hardware identifier.

QR Code/Image Options uses the original `QR/BtnQR` buttons and `DialogPhotoSelect` face/entire-Mii selector. A creates/displays a QR, Y opens the image chooser, SELECT saves a face image, and L/R selects a saved Mii. The original camera row and X scan shortcut are DSi-only. In the camera view, A attempts a QR read and X switches sensors. QR recognition is implemented separately from unfinished photo-to-Mii face recognition.

QR and Mii pictures save as lossless 400×240 PNGs in `MiiMaker/Photos` on DSi SD or a DS flashcart card. This is ordinary photo-file storage, not registration in Nintendo DSi Camera's album database. The existing gallery SELECT BMP export is retained. A QR can be shown on screen without an SD card, while saving reports that the card is missing. New local exports assign a normal DS-family software Mii identity; they do not claim the original imported console identity. Special Mii QR re-export from the compact gallery is unavailable.

`tools/qr_assets.py` imports original QR/photo GUI, and `tools/status_assets.py` imports actual Personal/Favorite crown artwork. Pants now reflect local/received/special status with provisional software material tints. Wii U's other-account bronze crown is not synthesized for this single-profile DS app.

Compact saves now use MDSC version 2 with the same 8 KiB capacity and 100 slots. MDSC version 1 and legacy MDS2 packets remain readable; the obsolete fifth temporary creator-character byte migrates to received/special status zero, while full creator strings remain intact. New private packets use MDS3. Keep old save backups before returning to older builds, which cannot understand the new status format.

`tools/animation_inventory.py` validates first/mid/last bone-curve samples for all 53 original clips, inventories 327 original GUI animation tracks, and writes `reference/animation-map.json`. All source clips remain in the local resource bundle. All 53 clips now have streamed skeletal playback support; six idle clips are bound to editor/gallery presentation. Full original plaza/event choreography, expressions and the 327 GUI animation tracks remain unfinished.

`python3 tools/test_host.py` runs fifteen asset-free sanitizer suites, including codec/CRC, migrated saves, status/ownership, QR authentication, PNG output and camera-sized decoding. `tests/qr_interop.py` independently verifies with PyCryptodome and ZXing (install Pillow, pycryptodome and zxing-cpp for that optional test). The native import test uses explicit fictional NitroFS fixtures and is separate from production SD access. Source dependencies are Nayuki's MIT QR generator, public-domain tiny-AES-c and quirc under its included license; only warning-clean portability changes were made. Nintendo assets remain outside the GitHub source repository.

`tests/motion.c` checks portable streamed-motion bounds and clocks. `tests/motion_assets.c` transforms all 12,164 gender/source frames and checks 316 full-mesh oracle poses (first/middle/last of each clip); maximum observed coordinate difference is 1/128 model unit and normal difference 2/127. Every oracle pose is rendered under ASan/UBSan. Exact pixel and hardware timing parity are not established. See `reference/ANIMATION_RENDERING.md`.


## SD gallery backup

Press SELECT on Home or Y on the profile overview to open Gallery Backup. A or the touch Create Backup button writes all saved slots to `sd:/MiiMaker/Backups` on DSi, or `fat:/MiiMaker/Backups` on a DS flashcart. B/Back returns. Unsaved edits must be saved first; an unreadable/unknown cartridge save cannot be exported as an empty replacement.

Backups are standard project MDSC snapshots (`Gallery0000.mdsc`, `Gallery0001.mdsc`, ...), with all 100 slots, 62 fields, names, creators, status/permission flags and gallery settings. Existing files are never overwritten. Every successful export is flushed, closed, reopened and compared byte for byte before success is reported. Failed writes attempt to remove only the new incomplete file. The cartridge and in-memory gallery remain unchanged. This adds backup export, not an in-app restore or a second bank inside compact cartridge saves; physical SD/flashcart writes remain unverified.

`tests/backup.c` exercises real filesystem export and independent compact decoding, complete Unicode records, settings, unique filenames and partial-write cleanup using a host file-size limit. It is part of the 29-suite sanitizer runner. `tools/emulator_profile_test.py --backup --core /path/to/core.so --save-dir /tmp/fresh-backup-test` checks the actual menu, touch/button routing, dirty-draft guard and missing-SD error path in melonDS. As with the other emulator tests, use symbols generated from the matching ROM build.
