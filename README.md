# Mii Maker DS

An unfinished Nintendo DS/DSi demake of Nintendo 3DS Mii Maker. It uses independently written DS code with locally supplied original resource data. Original models are retained; no replica character meshes are substituted.

Implemented work includes original-resource head/body rendering, sampled original idle poses, original menu/editor/profile/dialog layouts, captured body-slider dragging, naming/profile settings, local gallery copying and ROM-associated saves. New work adds standard CFSD/FFSD imports, original QR/photo menus, authenticated Mii QR generation, lossless PNG photos and a DSi-only camera QR decoding path. The current renderer is provisional; this is not a complete or pixel-identical 3DS port. See [FEATURES.md](FEATURES.md) and [DEVELOPMENT.md](DEVELOPMENT.md) for tested behavior and remaining work.

## Local resources

This repository contains source, conversion tools and tests. It does not contain decrypted ROMs, Nintendo executable code, extracted Nintendo graphics/models/fonts/audio, prebuilt asset-containing ROMs or user save data. Supply your own local resources. `CFL_Res.dat` is required; `CFL_DB.dat` and `CFL.DB.dat` are unused and are never required.

To build from the existing private project workspace, copy its `assets/` and `nitrofiles/` resource directories into this checkout locally. Those paths are ignored by Git. The conversion scripts can regenerate resources from your own extracted application: `extract.py`, `unpack.py`, `textures.py`, `layouts.py`, `ui_hitboxes.py`, `menu_assets.py`, `profile_assets.py`, `number_font.py`, `banner_icon.py`, `body_models.py`, `body_animation.py`, `animation_inventory.py`, `status_assets.py` and `qr_assets.py`. Conversion requires Python, Pillow and NumPy. Original resource and generated provenance reports remain local; no original game is downloaded by the build.

## Build

Install BlocksDS 1.24.0 and the Wonderful ARM toolchain, Python 3 and GNU make. Run `make`. Default paths are `/opt/wonderful/thirdparty/blocksds/core` and `/opt/wonderful`; override `BLOCKSDS` and `WONDERFUL_TOOLCHAIN` as needed. `tools/check_assets.py` reports missing local dependencies before compilation. The build applies the melonDS DS/DSi cartridge-header correction automatically.

For the tested emulator configuration, use melonDS DS mode with Direct Boot. DSi camera hardware remains unverified. Camera-dependent functionality is DSi-only; Mii records stay in the ROM-associated save.

## Tests

Run `python3 tools/test_host.py` for fourteen portable sanitizer test suites without Nintendo assets. GitHub Actions runs these source-only tests. Tests using actual models, ROM images or emulator cores require the corresponding local resources. No real-device or complete Nintendo interchange compatibility is claimed.

The substitute DejaVu font data is accompanied by its notice in `licenses/dejavu-font.txt`. SDK dependency notices are under `licenses/blocksds`. Nintendo assets are not licensed or distributed by this repository.

## Original data and animation mapping

[FEATURE_PORT_MAP.md](reference/FEATURE_PORT_MAP.md) indexes the original data and independent DS implementations. [MII_EXCHANGE.md](reference/MII_EXCHANGE.md) documents exact standard-Mii fields, QR encryption/format, received/special policy, save migration and hardware limits. [mii-fields.json](reference/mii-fields.json) contains the byte/bit map. All 53 original skeletal motion clips have first/mid/last curve samples validated; 327 original GUI animation tracks are inventoried. Only the verified idle binding currently plays in the runtime. The original raw assets and decoded motion samples remain in the private local resource bundle.

QR Code/Image Options uses original menu/selector artwork. QR, full-Mii and face pictures save as PNG files in `MiiMaker/Photos`; camera scanning is hidden on DS/DS Lite. Those files are not registered in the native DSi Camera album. Physical camera/SD and stock 3DS/Wii U acceptance remain unverified. Direct DS/DS, stock 3DS/Wii U wireless, Wii Channel receiving/sending, full original event choreography, audio and photo-to-Mii recognition are unfinished.

Build remains BlocksDS-only and DSi-enhanced. `CFL_Res.dat` remains required, and no `CFL_DB.dat` data is read or required. Version-1 compact/legacy records migrate into the version-2 8 KiB save without treating obsolete creator-input data as ownership flags. Full creator strings remain intact. Keep backups before running older builds against new saves.

QR dependencies are Nayuki's MIT QR generator, public-domain tiny-AES-c and quirc under its included license. Source-level portability patches are described in `reference/qr-dependencies.json`. Independent optional checks use PyCryptodome and ZXing; those Python packages are not part of the DS runtime.
