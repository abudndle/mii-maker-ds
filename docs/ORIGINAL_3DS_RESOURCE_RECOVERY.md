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
