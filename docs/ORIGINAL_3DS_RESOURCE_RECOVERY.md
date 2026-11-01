# Original Mii Maker 3DS resource extraction checkpoint

Source: user-provided **CTR-N-HEDE** NCCH game partition, extracted privately. Do not upload the game, its RomFS, or its resources to this public repository.

## Validated private inventory

- 37 top-level RomFS files; 22 LZ11/DARC archives unpacked with zero errors.
- 1,126 embedded archive files, independently reverified by SHA-256.
- 558 BCLIM original texture files with validated footer dimensions and sizes.
- 327 BCLAN UI animation files, 94 BCLYT UI layout files.
- 64 BCSKLA animation files and 16 BCMDL models in archives.
- 8 additional standalone LZ11 files decompressed, including original male/female CGFX bodies.
- The source also contains original sound, message, and effect resources.

## Source-derived touch geometry (not approximate)

From `layout/Select.arc/blyt/EDITSelectBase.bclyt` and `SelectMii.bclyt` on a 320x240 3DS canvas, scaled to 256x192 for DS:

| Pane | DS x | DS y | DS width | DS height |
| --- | ---: | ---: | ---: | ---: |
| B_Room_00 through B_Room_09 | 9 + 24*i | 2 | 22 | 21 |
| B_ArrowL | 0 | 59 | 19 | 72 |
| B_ArrowR | 237 | 59 | 19 | 72 |
| B_Mii_00 through B_Mii_09 | See `source/menu_generated.h` | 49 or 97 | 42 | 46 |

The room tabs, left/right arrows, and ten Mii destination boxes are **independent controls**. Keep animated Miis on the TOP screen, and drag the Mii (not its stationary box) on the BOTTOM screen.

## Completion boundary

This checkpoint establishes source resource identity, archive extraction and pane-coordinate provenance. It **does not** establish exact DS texture conversion, CGFX model rendering, full motion synchronization, audio playback, full 3DS feature parity, or melonDS runtime validation.

Original assets are deliberately **not** included in this public repository. Use the private extraction bundle on your own machine and convert only with authorized local source files.


## Milestone 66: original BCLIM to DS asset conversion (private)

The user-owned extracted `layout/Select/timg` archive includes 59 BCLIM
textures, including `BtnArrow.bclim` and original room/selection controls.
The full recovered archive tree contains 558 BCLIM files in nine formats:
L8, A8, LA4, LA8, RGB565, RGBA5551, RGBA4444, L4 and A4.

`tools/convert_original_bclim.py` validates the 40-byte CLIM footer,
8x8 Morton tiling and power-of-two padding. It produces a locally
loadable 4-byte little-endian width/height header followed by one
RGB555A1 pixel per visible source pixel.

**Private conversion command** (run on the machine that has the extracted
Nintendo files; never commit the resulting `nitrofiles` folder):

```sh
python3 tools/convert_original_bclim.py \
    /private/Mii_Maker_3DS_Archives_Unpacked/layout/Select/timg \
    nitrofiles/art/Select
```

For all known original textures, separately:

```sh
python3 tools/convert_original_bclim.py \
    /private/Mii_Maker_3DS_Archives_Unpacked \
    /private/Mii_Maker_3DS_Converted_All
```

The DS gallery optionally reads
`nitro:/art/Select/BtnArrow.bin`, checks its original 12×18 dimensions,
caches it once, and draws the original 3DS arrow art at the source-derived
left/right positions. If absent, it keeps the existing gallery background
without trying to read more game data.

**Limitations:** Alpha is thresholded to one DS alpha bit; full 3DS
material tints, CLYT nine-slice controls, BCLAN states, source sampling,
and the rest of the interface are not yet fully reproduced. This is a
real private-source conversion path and targeted integration, not a
verified pixel-identical port. Synthetic tests run without Nintendo
assets under `tests/test_original_bclim.py` and
`tests/test_original_ui_runtime.py`; the source-derived conversion
was also checked locally using the user's private textures.

Keep the extracted archives and converted artwork **out of the public
repository**. The Makefile already packages local `nitrofiles`
resources in a private ROM.


## Milestone 67: original selection-room controls and responsive drag

The private Mii Maker `layout/Select.arc/timg` has the actual
`BtnMiiB.bclim` (54×60), `BtnMiiLine.bclim` (54×60),
`BtnRoomEDITline.bclim` (32×28),
`BtnRoomEDITline01.bclim` (32×28), and
`BtnArrow.bclim` (12×18).
The corresponding local `.bin` files were produced with
`tools/convert_original_bclim.py` in milestone 66.

**To enable the new native DS gallery widgets locally:** extract the private
converted-asset ZIP into the project root, preserving
`nitrofiles/art/Select/`. The ROM build already packages local NitroFS.
The public repository deliberately does not contain Nintendo artwork.

The gallery now:
- renders all 10 original, separately selectable room-tab shapes using
  the exact scaled pane rectangles from `EDITSelectBase.bclyt`;
- displays the original Mii-box fill beneath each thumbnail and original
  source selection border instead of the provisional green outline,
  while falling back safely if the original files are not installed;
- preserves fixed original Mii destination box geometry during dragging;
- uses a clipped 42×46 backing-store refresh to move the floating Mii
  directly in bottom-screen VRAM, without rerendering 10 avatar previews
  on each stylus position update;
- pages destination rooms with L/R and held stylus arrow-hover input, and
  cancels a dropped-outside/arrow-released drag without a ghost sprite;
- loads each optional original sprite once, with strict dimension and
  payload-length validation; failed private reads are not retried per frame.

The selected/unselected border variants are conservative uses of real
Nintendo textures, **not** a proven reproduction of their complete original
BCLAN tint/alpha/keyframe states. Exact 3DS timings, sound cues and full
visual parity remain open tasks. The host test synthesizes images with the
same dimensions (no Nintendo data) and verifies transparent compositing,
hitbox sizing, clipping, and missing/corrupt-asset fallbacks.

Run `python3 tests/test_original_gallery_art.py` and
`python3 tests/test_original_gallery_runtime.py` without any private
assets, or build the private NitroFS ROM to check real original images in
melonDS. An ARM9 compile smoke test alone does not count as emulator proof.


## Milestone 68: source-keyframed 3DS room-selection feedback

The original, user-supplied `layout/Select.arc/anim/` archive was
inspected privately, **not** published to this repository. The relevant
Nintendo CLAN tracks were recovered from the binary's bounded `pai1`
channel records (3-float Hermite keyframes). Only the small numeric
channels, source frame counts and source digests are retained as
portable `source/gallery_clan_generated.h`.

| Original animation | Source frames | Ported source channels |
| --- | ---: | --- |
| `SelectMii_Select.bclan` | 6 | `P_Mii_00` CLPA X/Y scale (1.0 → 1.1 → 1.0 over source frames 0–2) |
| `EDITSelectBase_Select.bclan` | 2 | `P_Room_00` CLMC R/G/B from (220,255,244) to (50,118,80) |
| `EDITSelectBase_Unselect.bclan` | 2 | Reverse CLMC R/G/B from (50,118,80) to (220,255,244) |

Source SHA-256 identifiers (private files, **not** uploads):

- `SelectMii_Select`: `13b835186a2ebdda947ef20ea75f73f52d9edd8a13e2b4dd26718d933660d258`
- `EDITSelectBase_Select`: `58502d329d84c5db65a146983be0939d4f3a61b1816d801fbd5d5e28f8c804cd`
- `EDITSelectBase_Unselect`: `b636b327a56793d47710f15f7811f4bf2e73eef1d9dc8c4089e08527452c9993`

The DS port now evaluates those actual source curves in signed Q16.16
using the existing no-FPU Hermite evaluator. The selected Mii **thumbnail**
expands briefly, then returns to its original size. The 10 Mii
destination boxes never move and retain the existing 3DS-derived
touch rectangles; room-tab sprites are modulated by the source CLMC
colors on navigation. The full source 6-frame clip contains no further
scale changes after source frame 2, so the DS renderer stops refreshing
after the visible keys and performs one final cleanup redraw.

The display uses **two DS VBlanks per source frame provisionally**;
this is not yet a hardware-verified playback rate. No 3DS CLAN BCLAN
payload or other copyrighted bytes enter the public repository.

Run the local synthetic tests:
```sh
python3 tests/test_gallery_clan.py
python3 tests/test_gallery_clan_wiring.py
python3 tests/test_original_gallery_art.py
```
To reproduce the recovered metadata **privately**:
```sh
python3 tools/extract_gallery_clan.py /private/Select/anim
```

Remaining work: original GUI pane transforms beyond the targeted
P_Mii_00 scale and P_Room_00 color channels, alpha/visibility events,
BCLAN easing for other control hierarchies, stock timing, audio cues,
and actual pixel-by-pixel melonDS screenshots.


## Milestone 69: original room arrows and Mii confirmation

The user's private original Select.arc BCLAN files were inspected and their
numeric keyframes validated. Only these numeric curves and SHA-256 identifiers
are committed; no original game binaries are included.

| Original 3DS animation | Verified source keys | SHA-256 |
| --- | --- | --- |
| EDITSelectBase_ScrollL (11 frames) | P_ArrowL/R CLPA X: 0 to -3/+3; left shadow CLVC: 200 to 0 | c388baec78e64693fe4db2eb416aacf51d93f2683fff70db427e55c92d06942a |
| EDITSelectBase_ScrollR (11 frames) | Reverse CLPA X: -3/+3 to 0; shadow CLVC: 0 to 200 | e2380c0de88b7762a2dd9691c8382a7cd96108f800edfc7a83b68faaa09a4cfe |
| SelectMii_Decide (6 frames) | P_Mii_00 CLMC RGB constant 251/199/186 | be2f78f4a54d19d5a6f9fe4cbbbd430d7e44c94526475b8d1abbb71b63eede28 |
| SelectMii_UnDecide (6 frames) | P_Mii_00 CLMC RGB 251/199/186 to 216/233/214 | 6e8079065bf0afc8735684cd8cb6a01221f59054c5bfb5d171763468d5c3347c |
| EDITSelectBase_Invalid (11 frames) | P_ArrowL/R horizontal offsets are constant zero; no source bounce | 882e083b1a8dbc33a208a15a335367bcf2796ce13e782b0a00cae5d83052d0bb |

The DS port now evaluates the source arrow CLPA curves at the exact
320-to-256 pixel ratio of 4/5 using fixed-point arithmetic. The original
converted BtnArrow art follows those offsets; original Mii selection
borders receive source CLMC confirmation color feedback. Physical L/R
and the touchscreen arrows now share the original first/last-room
boundary behavior instead of physical input wrapping around.

The arrow shadow CLVC value is decoded and host-tested but its complete
original graphics layering remains unverified and **is not yet drawn**.
Likewise, the original Invalid clip has no changing arrow-translation
keyframes, so no unsupported bounce is invented.

The existing main loop reuses source-keyed VBlank redraw scheduling;
new navigation and confirmation effects are only active over frames
with verified changing keys. Input while dragging preserves the source
Mii and stationary destination boxes.

To verify source files privately, run:
python3 tools/extract_gallery_nav_clan.py /private/Select/anim

Run asset-free unit tests:
python3 tests/test_gallery_nav_clan.py
python3 tests/test_gallery_nav_wiring.py
python3 tests/test_original_gallery_art.py

Full 3DS animation/event parity, other arrow shadow layers, original
audio, exact 3DS frame timing, and real private-ROM melonDS visual testing
remain future milestones. The current two-VBlank source-frame cadence
is provisional.
