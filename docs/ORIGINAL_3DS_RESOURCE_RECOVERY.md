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
