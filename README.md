# Mii Maker DS

An unfinished Nintendo DS/DSi demake of Nintendo 3DS Mii Maker. It uses independently written DS code with locally supplied original resource data. Original models are retained; no replica character meshes are substituted.

Implemented work includes original-resource head/body rendering, sampled original idle poses, original menu/editor/profile/dialog layouts, captured body-slider dragging, naming/profile settings, local gallery copying and ROM-associated saves. The current renderer is provisional; this is not a complete or pixel-identical 3DS port. See [FEATURES.md](FEATURES.md) and [DEVELOPMENT.md](DEVELOPMENT.md) for tested behavior and remaining work.

## Local resources

This repository contains source, conversion tools and tests. It does not contain decrypted ROMs, Nintendo executable code, extracted Nintendo graphics/models/fonts/audio, prebuilt asset-containing ROMs or user save data. Supply your own local resources. `CFL_Res.dat` is required; `CFL_DB.dat` and `CFL.DB.dat` are unused and are never required.

To build from the existing private project workspace, copy its `assets/` and `nitrofiles/` resource directories into this checkout locally. Those paths are ignored by Git. The conversion scripts can regenerate resources from your own extracted application: `extract.py`, `unpack.py`, `textures.py`, `layouts.py`, `ui_hitboxes.py`, `menu_assets.py`, `profile_assets.py`, `number_font.py`, `banner_icon.py`, `body_models.py` and `body_animation.py`. Conversion requires Python, Pillow and NumPy. Original resource and generated provenance reports remain local; no original game is downloaded by the build.

## Build

Install BlocksDS 1.24.0 and the Wonderful ARM toolchain, Python 3 and GNU make. Run `make`. Default paths are `/opt/wonderful/thirdparty/blocksds/core` and `/opt/wonderful`; override `BLOCKSDS` and `WONDERFUL_TOOLCHAIN` as needed. `tools/check_assets.py` reports missing local dependencies before compilation. The build applies the melonDS DS/DSi cartridge-header correction automatically.

For the tested emulator configuration, use melonDS DS mode with Direct Boot. DSi camera hardware remains unverified. Camera-dependent functionality is DSi-only; Mii records stay in the ROM-associated save.

## Tests

Run `python3 tools/test_host.py` for nine portable sanitizer test suites without Nintendo assets. GitHub Actions runs these source-only tests. Tests using actual models, ROM images or emulator cores require the corresponding local resources. No real-device or complete Nintendo interchange compatibility is claimed.

The substitute DejaVu font data is accompanied by its notice in `licenses/dejavu-font.txt`. SDK dependency notices are under `licenses/blocksds`. Nintendo assets are not licensed or distributed by this repository.
