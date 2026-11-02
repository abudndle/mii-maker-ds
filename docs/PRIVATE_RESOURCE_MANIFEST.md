# Mii Maker DS private build resource manifest

This manifest mirrors the required local inputs checked by `tools/check_assets.py`.
It is a checklist only: it does not contain Nintendo ROM data, decrypted archives,
extracted textures, models, firmware, keys, or other proprietary resources.

## Required local inputs

Provide authorized source files in the private build workspace at these paths:

### Mii model and animation resources

- `nitrofiles/models/MaleBody.msp`
- `nitrofiles/models/FemaleBody.msp`
- `nitrofiles/cfl/CFL_Res.dat`
- `nitrofiles/models/MaleBody.bin`
- `nitrofiles/models/FemaleBody.bin`
- `nitrofiles/models/MaleBody.ani`
- `nitrofiles/models/FemaleBody.ani`

### UI, status, and icon resources

- `nitrofiles/ui/EditBody.rgb555`
- `nitrofiles/ui/home-bottom.rgb555`
- `nitrofiles/ui/profile.rgb555`
- `nitrofiles/ui/import-bottom.rgb555`
- `nitrofiles/ui/qr-menu-ds.rgb555`
- `nitrofiles/ui/qr-menu-dsi.rgb555`
- `nitrofiles/ui/photo-select.rgb555`
- `nitrofiles/art/StatusPersonal.bin`
- `nitrofiles/art/StatusFavorite.bin`
- `nitrofiles/art/Select/IconFavorite.bin`
- `nitrofiles/art/Select/IconMyMii.bin`
- `nitrofiles/art/Select/IconCopyB.bin`
- `nitrofiles/art/Select/IconOpen.bin`
- `nitrofiles/font/number.bin`
- `assets/ui/original-icon.gif`

### Generated project headers

These are required generated build inputs. Regenerate them from authorized local
resources using the repository's generation tools; do not copy extracted copyrighted
graphics into public source files.

- `source/ui_generated.h`
- `source/ui_hits.h`
- `source/menu_generated.h`
- `source/profile_generated.h`
- `source/ui_font.h`

## Build preparation

1. Obtain the original resources through an authorized source and keep them in a private workspace.
2. Follow `DEVELOPMENT.md` and the resource import/generation scripts.
3. Run `python3 tools/build_preflight.py`.
4. Run `python3 tools/check_assets.py`.
5. Build with the supported BlocksDS toolchain.
6. Run private ROM acceptance and melonDS tests; keep the ROM and resource archive private.

The project does not require `CFL.DB.dat` or `CFL_DB.dat`. Do not add either as a build prerequisite.

## Important

The manifest describes expected inputs, not proof that they are present, valid, or
successfully integrated. CI using synthetic fixtures does not establish original
asset fidelity or gameplay acceptance.
