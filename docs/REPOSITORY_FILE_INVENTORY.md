# Mii Maker DS — repository file and build readiness inventory

This inventory separates files that **belong in public source control** from original Nintendo resources that must be supplied **privately**. A public GitHub repository cannot contain every original 3DS game file.

## Public project structure (already present)

- `source/`: DS/DSi application modules, editor, Mii renderer, room/gallery, save, camera, QR, exchange, and UI.
- `tools/`: original-resource import and verification, private builds, build preflight, provenance, emulator/gallery validation.
- `tests/`: portable host/source tests and synthetic ROM smoke tests.
- `reference/`: source-to-DS mappings and extracted-layout metadata; do not add proprietary binaries.
- `docs/`, `DEVELOPMENT.md`, `FEATURES.md`, `README.md`: build instructions, compatibility limits, parity tracking.
- `Makefile`, `Makefile.devkitpro`, `.github/workflows/`: build and CI entry points.
- `.gitignore`: excludes private assets, NitroFS resources, ROMs, saves, decrypted archives and extracted game formats.

## Private local resource inputs (never commit)

The existing `tools/build_preflight.py` checks the following inputs for a complete original-resource build:

| Required private file | Purpose |
| --- | --- |
| `nitrofiles/cfl/CFL_Res.dat` | Original Mii face/head resources |
| `nitrofiles/models/MaleBody.bin` | Original male body resource |
| `nitrofiles/models/FemaleBody.bin` | Original female body resource |
| `assets/ui/original-icon.gif` | Original game banner/icon |

The local `nitrofiles/` directory and BlocksDS SDK/ARM compiler must also be present. These inputs are **not** available merely because source code is on GitHub. Do not require `CFL.DB.dat` or `CFL_DB.dat`; the project explicitly excludes that database.

## Build/verification sequence

1. Install BlocksDS and the supported ARM compiler in a private Linux workspace.
2. Supply authorized original resources privately; do not upload ROMs or decrypted files to GitHub Actions.
3. Run `python3 tools/build_preflight.py` to identify missing prerequisites.
4. Run `python3 tools/check_assets.py` and follow the documented private build flow in `DEVELOPMENT.md`.
5. Build the ROM and test actual DS/DSi boot, saving, editing, multiple walking Miis, and camera gating in melonDS.
6. Use `tools/private_rom_acceptance.py` for private build evidence; do not publish proprietary resources or generated original-resource ROMs.

## Outstanding original-game parity

Consult `FEATURES.md` for the maintained feature-by-feature inventory. In particular, exact model/material rendering, all original UI transitions, original animations and proportions, DSi camera recognition, native wireless exchange, Wii/Wii U interoperability, and real-hardware acceptance remain incomplete or unverified. Synthetic compile success must not be reported as proof of these features.

## Scope limitation

This document inventories existing files and missing private prerequisites. It does **not** claim the full original game has been extracted, legally redistributable, compiled, or tested on physical DS/DSi hardware.
