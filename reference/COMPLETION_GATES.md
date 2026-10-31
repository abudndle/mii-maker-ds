# Mii Maker 3DS → Nintendo DS/DSi completion gates

**Status: unfinished.** Passing source/host CI is not a complete game-port acceptance test.
The 3DS program's ARM11 binaries are not portable as DS ARM9 executables. The
DS runtime is independently authored around locally supplied original model and
art resources. Preserve private resources outside this public Git repository.

| Original behavior / resource | Current DS implementation | Still required before complete |
|---|---|---|
| Home, create, view, edit, delete, copy | Native menu, editors, persistent gallery drag-to-move/swap and 100 physical slots | Verify actual ARM9 gameplay, all navigation and modal confirmation screens in melonDS |
| 13 appearance pages, original colors and transforms | Original UI icon/layout inputs and field controls | Verify every original hitbox/field visually against 3DS reference and all DS controls |
| Mii viewing angle using L/R | 24 yaw steps applied to original face/body geometry in editor; gallery L/R pages unchanged | Confirm shading, silhouette, side and back views against the original 3DS presentation |
| Mii names, birthday, gender, favorite color, copying/sharing | Profile controls, Unicode store/QR mapping, favorite cap, Personal Mii protection and received-Mii copy-before-edit confirmation | Validate actual menu choreography, persistence, and cross-version profile compatibility |
| 100 Miis, Personal Mii, favorites | Save backends with CRC and older-bank recovery for checksum-valid invalid Personal-Mii snapshots, import/export, thumbnail cache, gallery selection | Confirm cold restart and EEPROM detection across supported emulator/hardware |
| Original CFL face meshes/textures and body assets | Original-resource software renderer and BOD2/BOD3 body streams | Improve projection, lighting, materials, body proportions and verify visual parity |
| 53 male/female skeletal animation clips | Original 53-clip stream and manual gallery clip selector; six automatic idles | Implement original scene/event clip triggers and transition/blend timing |
| Original CLAN animation timeline | Inventory of 327 original GUI tracks | Bind all decoded property channels to matching original CLYT widgets and replace provisional transitions; home focus, editor selection and reconstructed profile entrance/exit cues are partial |
| QR transmit/receive, image exports | QR encode/decode, file image/QR export, DSi camera QR entry | Stock 3DS/DSi interop, actual SD reads/writes, QR scanner and camera tests |
| Create Mii from photo | Recognition resources retained, not a working converter | Implement recognition/adaptation on camera-equipped DSi; original DS has no built-in camera |
| Wireless Mii sharing, Wii reception | No completed wireless transport | Design and test DS-compatible transport; stock 3DS/Wii protocols cannot be assumed interoperable |
| Original music/sounds | Audio archive retained only | Extract licensed-in-private assets, convert to a DS-compatible format, map menu/events, verify playback |
| Original 3DS interface fidelity | Selected original layouts, art, icons and text data | Compare screens against reference captures; some texts, animations and layouts are provisional |
| DS/DSi ROM and hardware | Source build recipe plus private asset and executable validation | Run latest BlocksDS build, execute ARM9/ARM7 on melonDS, save/restart and test DS/DSi hardware |

## Required release/finish evidence

1. **Assets:** The user's own resource ZIP passes extraction safety, original 53-clip catalog checks, and original male/female renderer integration. Do not publish the ZIP, extracted game resources, or a ROM embedding them.
2. **Host:** All 19 portable host suites and GCC/Clang source checks pass at the final commit. Rotation, save, QR, gallery, editor and import flows have asset-free regressions.
3. **Build:** A fresh `mii-ds.nds` is compiled from that **same** commit with BlocksDS. ROM checks pass: executable sections, DS/DSi boundary, NitroFS payload parity, body meshes, 53 original motion packs.
4. **Emulation:** Boot that exact ROM with DS mode + Direct Boot in melonDS. Exercise all primary screens, 100-slot gallery, creation, profile, editor L/R 3D view, sampled and streamed animations, copy/delete/QR, image export, save + cold-restart.
5. **Functional parity:** Implement and acceptance-test the missing items in the table. Document explicitly any unavoidable DS-versus-3DS hardware difference instead of declaring unsupported functionality finished.
6. **Visual parity:** Compare source-correct screenshots and animation timings against the 3DS original under multiple genders, skin tones, hair, eyewear, expression/face shapes, poses and model views.

## Repeatable private build

From the repository directory, with the user's resource ZIP and BlocksDS installed:

```sh
python3 tools/build_private.py /path/to/MiiMaker_DS_Resources.zip --validate-only
python3 tools/build_private.py /path/to/MiiMaker_DS_Resources.zip
```

The full command checks original head/body rendering **before compilation**, then
builds and verifies the ROM. It cannot attest to live emulator/device behavior
without running the resulting ROM through a compatible emulator or hardware.

**Completion must never be inferred solely from GitHub source CI.**
