# Nitro Engine + DSMA original-model migration (M86)

Preserve the user-owned, original 3DS body geometry and existing Mii Maker port. The shipping ROM currently presents a software-rendered top-screen RGB555 bitmap, so it must not be switched to Nitro Engine 3D without integrating the display compositor. This is a private, opt-in conversion and validation path, not a replacement Mii model or completed hardware renderer.

## Libraries

- Nitro Engine: chosen hardware 3D scene/rendering backend, https://github.com/AntonioND/nitro-engine (now maintained at https://codeberg.org/SkyLyrac/nitro-engine). BlocksDS package: blocksds-nitroengine, linker flag -lNE and LIBDIRS path $(BLOCKSDSEXT)/nitro-engine.
- DSMA: skeletal animation model/clip backend used by Nitro Engine, https://github.com/AntonioND/dsma-library. DSM stores DS display-list geometry and DSA stores skeleton frames.
- BlocksDS libraries: keep existing libnds/NitroFS toolchain, https://blocksds.skylyrac.net/docs/libs/ . LibDSF may help with font rendering later.
- libslim: https://github.com/DS-Homebrew/libslim . This is a FAT/SD filesystem library, not a 3D renderer, and requires deliberate migration from libfat API where used.
- uLibrary: https://codeberg.org/blocksds/ulibrary . Its APIs and compatibility are not yet verified, so it is not linked in the shipping ROM.

## Completed conversion adapter

The tools/export_bod2_md5.py exporter transforms existing source-extracted BOD2 triangle data to MD5 mesh input accepted by Nitro Engine's md5_to_dsma.py converter. It retains triangle positions, material grouping and the 18 existing per-vertex bone indices. It rejects malformed or inconsistent source geometry. Its synthetic tests run under GCC/Clang portable CI.

IMPORTANT: BOD2 does not include source UVs, complete bind pose, hierarchy or animation frames. The exporter explicitly uses temporary zero UV coordinates and identity bind joints to test static geometry conversion ONLY. The original UV textures and 53 real motions must be recovered from authorized private sources and verified separately before animated DSM/DSA can be used. No new substitute Mii is drawn.

## Private opt-in workflow

Run this locally in a private workspace with Nitro Engine installed:

    make dsma-private-model BOD2_INPUT=/private/MaleBody.bin NITRO_ENGINE_MD5_TOOL=/installed/nitro-engine/tools/md5_to_dsma/md5_to_dsma.py DSMA_STAGE=/tmp/mii-maker-dsma-private DSMA_NAME=MaleBody

This stages BOD2 -> MD5 mesh -> Nitro Engine DSM and identity-pose DSA. The existing ROM build is unchanged. Do not commit generated source-derived files, and keep converted Nintendo assets out of public Actions artifacts.

## Next acceptance gates

1. Recover source-exact bind transforms, bone hierarchy, UVs and material assignments; reject unsupported geometry.
2. Convert the original 53 animation clips and verify DSMA pose/fps/bone parity against existing source reference.
3. Add an opt-in Nitro Engine top-screen renderer that coexists with the original 2D lower touchscreen and gallery UI.
4. Validate melonDS 3D frames, memory budget, animation timing and real DS/DSi compatibility before switching the default renderer.
