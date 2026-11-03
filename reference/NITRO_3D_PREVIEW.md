# M88: Nitro Engine + DSMA hardware-3D Mii body preview

This is an **opt-in, separate BlocksDS ROM** for testing source-derived body
meshes on the real Nintendo DS 3D polygon engine. It does not replace the
Mii Maker game or its original two-screen interface. The original 3DS body
mesh is exported privately using the M86 BOD2 -> MD5 -> DSM/DSA path.
Nitro Engine renders the DSM through its DSMA-backed animated-model API.

## Build prerequisites

- BlocksDS toolchain and Nitro Engine installed with:
  wf-pacman -Sy blocksds-nitroengine
- Authorized original 3DS Mii model data previously extracted by the owner.
- The privately generated source BOD2 male/female body mesh.
- An original-resource texture and correct skeletal bind transforms are
  **not yet** supported by the M86 BOD2 exporter. Its interim zero UV and
  identity joints only establish *geometry pipeline* validation, not original
  textured skeletal animations. The generated base-pose DSA is **not**
  one of the original 53 motion clips.

## Stage the source-derived files privately

From the repository root, with the converter installed:

    make dsma-private-model BOD2_INPUT=/private/MaleBody.bin \
      NITRO_ENGINE_MD5_TOOL=/private/nitro-engine/tools/md5_to_dsma/md5_to_dsma.py \
      DSMA_STAGE=/tmp/mii-maker-dsma-private DSMA_NAME=MiiBody

The converter emits MiiBody_dsm.bin (model) and MiiBody_dsa.bin
(identity base-pose animation). Stage them in the ignored NitroFS folder:

    mkdir -p hardware3d/nitrofiles/models
    cp /tmp/mii-maker-dsma-private/MiiBody_dsm.bin hardware3d/nitrofiles/models/
    cp /tmp/mii-maker-dsma-private/MiiBody_dsa.bin hardware3d/nitrofiles/models/

Then compile with:

    make nitro-3d-preview

This builds hardware3d/mii-body-gpu-test.nds, **not** mii-ds.nds.
The test ROM uses Nitro Engine's NE_ModelLoadDSMFAT, NE_AnimationLoadFAT,
NE_ModelSetAnimation and NE_ModelDraw; D-pad rotates the body and START
exits. Nitro Engine owns the 3D top display and libnds drives the 2D
console on the bottom. Run in melonDS with 3D rendering enabled or
on real DS hardware. The private converted assets must never be committed.

## Safety and limitations

The main game still uses a software RGB555 top-screen renderer and the
original Mii UI. That renderer must not be switched until 3D overlay
composition, original UVs, source joint hierarchy/animation pose parity,
and memory/performance targets are tested. This is a GPU acceptance
harness and a real hardware 3D loading/drawing implementation, **not**
a completed port of the main Mii Maker renderer.

Other library roles: BlocksDS/libnds provides 2D touchscreen and hardware
services; Maxmod is already linked for optional audio; DSMA handles skeletal
draw calls through Nitro Engine; libslim is an optional SD backend; uLibrary
could accelerate future 2D UI work but has not been connected. Networking
would require DSWiFi and the appropriate ARM7 core plus a verified transfer
protocol rather than only linking a WiFi library.

Documentation:
- https://blocksds.skylyrac.net/docs/libs/core_libs/
- https://blocksds.skylyrac.net/docs/libs/additional_libs/
- https://github.com/AntonioND/nitro-engine
- https://github.com/AntonioND/dsma-library

## Additional DSi references and how to reuse them

- libnds API reference (https://libnds.devkitpro.org/): keys, touch, VRAM, NDMA, IRQ and camera APIs already used in this port; cross-check BlocksDS installed libnds version before relying on devkitPro-specific declarations.
- Epicpkmn11/dsi-camera (https://github.com/Epicpkmn11/dsi-camera): standalone devkitPro DSi inner/outer camera preview and SD PNG photo-save example, not a drop-in BlocksDS library. Useful for comparing sensor-routing behavior.
- addisonking/dsi-camera (https://github.com/addisonking/dsi-camera): forked standalone app with sensor exposure, gain, white balance, capture and album features. Any adaptation needs license/API review, NDMA ownership checks, privacy-scrub preservation and physical DSi testing.
- Epicpkmn11/dsidl (https://github.com/Epicpkmn11/dsidl): standalone QR-to-URL downloader; reference for DSi networking and file-browser behavior, not a Mii wireless protocol library. Its documented router compatibility limitations must be considered.

The existing source/camera_ds.c already selects the DSi inner camera for photo creation and outer camera for QR, guards DMA timeouts and securely scrubs prior frames. Preserve these safety properties; do not replace the camera with demo code without parity tests. Other supporting libraries remain candidates, not automatic dependencies.
