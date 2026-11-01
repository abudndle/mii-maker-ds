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


## Milestone 70: original scroll-shadow artwork and CLVC compositing

The user's privately recovered original
`layout/Select.arc/timg/BtnScrollShadow.bclim` was decoded and inspected:
- Original texture is **16 x 16**, CLIM A4 (format 13), and contains
  transparent and opaque pixels. The exact pixel data is not in GitHub.
- Source .bclim SHA-256:
  `7740c7ac44427260ce59e27aeafae72c82f042eacbd5d199b4cad98f9e5cdc56`
- Locally converted RGB555A1 sprite SHA-256:
  `8f8351fdca22e3a26e05371c0d884412f262e3939d68ca875679192ad1e6f9d1`.
- The original EDITSelectBase_ScrollL and ScrollR BCLAN clips each supply
  CLVC 0x1000 on the P_ArrowLSdw_00/01 and P_ArrowRSdw_00/01
  panes. Their available source values fade **200 to 0** and **0 to 200**
  respectively during source frames zero to one.

The DS source now optionally loads `nitro:/art/Select/BtnScrollShadow.bin`
and draws the converted, source-derived 16 x 16 original stamp at 13 x 13
DS pixels on both arrow centers, behind the already integrated source
BtnArrow art. The 3DS-to-DS ratio is 4/5. The shadow RGB555 color
channels are composited over the existing lower-screen bitmap using the
source CLVC opacity, and the source 1-bit transparency mask remains
respected. Both shadow sprites share the arrow navigation translation,
but the original pane touch hitboxes **never move**.

Runtime validates exact sprite width, height and payload length and
caches the original asset only once; missing or malformed files leave
the existing gallery unchanged. No placeholder/synthetic shadow is
shown when the source original asset is absent.

**Private installation:** Install the companion six-file private gallery
asset bundle, keeping the files under `nitrofiles/art/Select/`. Never
commit that bundle or Nintendo textures to the public GitHub source.
Local rebuilds include those NitroFS files automatically.

**Caution:** The original background pane hierarchy may affect the
shadow's exact image placement and color modulation beyond the verified
P_ArrowLSdw CLVC opacity. The 13x13 centered stamp alignment is based
on source size/arrow pane center, not a pixel-perfect hardware capture.
The source-frame cadence remains provisionally 2 DS VBlanks per
original frame. The rest of the 3DS UI animation hierarchy, full
select/deselect button events, audio and full private-ROM melonDS
visual verification remain open.

Run the asset-free host and source regressions:

```sh
python3 tests/test_original_scroll_shadow.py
python3 tests/test_original_scroll_shadow_wiring.py
```


## Milestone 71: original two-button confirmation dialog opening

The user's private Mii Maker 3DS `Dialog.arc/anim` contains the
two-button `DialogBase02_DialogIn.bclan`, which has an identical
`W_Dialog` CLPA Y curve to the already ported original
`DialogBase00_DialogIn` and `DialogBase01_DialogIn` clips.
Its source SHA-256 is:
`7548f0d85b14edf98dcb01ec21d3b6d101e32ba7eb37b1a98f02aa9c73a36f4a`.

The exact source Hermite channel is 21 source frames (0 through 20):

| Source frame | W_Dialog Y (3DS px) | Source tangent |
| ---: | ---: | ---: |
| 0 | -240 | 0 |
| 17 | +2 | 0 |
| 20 | 0 | -0.6667 |

In the DS confirmation overlay, `source/confirm_motion.c` now
uses the existing integer Hermite CLAN decoder and the exact 240-to-192
Y conversion. The animation plays on **a cached copy of the dialog
bitmap over a cached, stationary underlying gallery screen**. This
avoids re-rendering all ten 3D Mii thumbnails every 60 Hz tick.
The extracted source BCLAN is not distributed or embedded.

The visual dialog begins offscreen, enters on the original source Y
keys, slightly overshoots, and settles on the static touchscreen
confirmation hitboxes. Touch confirmation is gated until the panel
arrives so players cannot press invisible controls; A and B keyboard
confirmation/cancellation still work during entrance. The original
DialogBase02 parent pane is 338 x 258 3DS pixels and its two button
panes are independent controls, as validated from the private CLYT.

The existing `nitro:/ui/confirm.rgb555` artwork remains in use for
the panel face: **this milestone ports the source motion, not a claim
that the current dialog appearance is pixel-identical to 3DS**.
The original game artwork for the dialog body and buttons, its CLMC
press states, DialogOut/OutUp visuals, and audio cues still require
additional integration. Source timing uses a provisional two DS
VBlanks for each original animation frame, pending melonDS/3DS
comparison.

Source-only, asset-free host tests verify keyframe timing, overshoot,
last-frame cleanup, VBlank rollover, clipped RGB555 compositing,
underlying-screen restoration, rejection of accidental touches during
entrance, and prompt reset after acceptance/cancellation.

To check the original files locally without publishing them, run:

```sh
python3 tools/extract_confirm_dialog_clan.py /private/Dialog/anim
python3 tests/test_confirm_motion.py
python3 tests/test_confirm_motion_wiring.py
```


## Milestone 72: original two-button confirmation exits and safe transactions

The privately extracted source from the supplied Mii Maker 3DS RomFS contains:
- `DialogBase02_DialogOut.bclan`, SHA-256
  `0f30409d9787168465e712ad125b89973e5a8d8b2bdaf5c4684f15d1d275f503`.
- `DialogBase02_DialogOutUp.bclan`, SHA-256
  `69a4081d4b0fb39e7796924768fd5e2dad2b5a292afa7ab1e895a797620bb325`.

Both are byte-for-byte identical to their respective `DialogBase00`
source clips. The generated, publicly safe Q16 source keys already in
`source/clan_dialog_generated.h` therefore apply without reinterpreting
the private BCLAN data: `DialogOut` moves the pane from 0 to -240 source
pixels and `DialogOutUp` from 0 to +240 by source frame 17.

A confirmation selection is now queued instead of immediately destroying
its dialog. The original entry finishes before the selected original
exit clip begins, with no discontinuity if physical A/B is pressed early.
The main input loop rejects additional interactions during closing;
the edit/copy/delete/discard transaction is applied **once the exit is
finished**, so no held button or touch can accidentally act on the
next screen. The existing underlay/compositor reveals the cached original
gallery behind the outgoing pane; the next real screen is then repainted.
If UI initialization fails, the old immediate confirmation path still
works instead of hanging a transaction.

This milestone does not embed or publish original Nintendo resource
bytes. Current `nitro:/ui/confirm.rgb555` artwork is retained; original
dialog material layering, press-state animation, audio and final
hardware frame timing remain incomplete. Two DS VBlanks per 3DS frame
is still a provisional timing assumption.

Synthetic, original-resource-free host regressions:

```sh
python3 tests/test_confirm_exit_motion.py
python3 tests/test_confirm_exit_wiring.py
python3 tests/test_confirm_motion.py
python3 tests/test_confirm_motion_wiring.py
```

Actual hardware/DSi camera and a fresh melonDS ROM screenshot have not
been verified by this source-only milestone.
