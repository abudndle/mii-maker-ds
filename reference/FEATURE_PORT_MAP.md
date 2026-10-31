# Original feature to DS implementation

The original compiled ARM11 executable is evidence, not recovered Nintendo C/C++ source. The DS runtime is independently authored. Models and artwork are extracted originals, not replica meshes or generated replacements. Data and code provenance do not by themselves prove functional parity.

| Original component | DS mapping | Current evidence / limit |
|---|---|---|
| CFL_Res.dat meshes, anchors, masks and feature textures | cfl_resource.c, head.c | Real original geometry/textures; software camera/materials remain provisional |
| MaleBody/FemaleBody rigid meshes and skeleton | body_models.py, head.c | Original triangle/palette/bone streams and head attachment; body proportion coefficients incomplete |
| MiiAnim.arc, Wait00 | animation_curves.py, body_animation.py, animation.c | 24 sampled source poses per gender; remaining original clips retained locally but not all played |
| PlazaTop / SelectMii / EDITSelectBase | menu.c, ui.c, menu_assets.py | Original menu/gallery art and bounds; animated plaza/sorting incomplete |
| Thirteen original editor pages | layouts.py, ui_hitboxes.py, ui.c | Icons, transform/reset controls, colors and captured sliders |
| Editor/Profile and original gender/date/permission dialogs | profile.c, profile_assets.py | Names/profile controls, original numeral font and dialog hits |
| QR/BtnQR, Dialog/DialogPhotoSelect | qr_assets.py, qr_generated.h, ui.c | Original QR menu and Face/Entire Mii selector; camera row hidden on DS |
| Original 327 CLAN GUI animation tracks | animation_inventory.py | Retained and inventoried; full GUI track playback remains unfinished |
| Original Personal/Favorite icon panes | status_assets.py, status.c, ui.c | Original tinted crown art; persistent ownership/status and provisional pants tints |
| CFLStoreData / Ver3StoreData | mii_codec.c, unicode.c | Explicit original serialized field/UTF-16/CRC mapping; full raw identity preserved only in exchange records |
| Mii QR payload | mii_qr.c, qr_scan.c | Authenticated original-format envelope, independent AES/QR checks; stock-device test pending |
| Save QR / Save Mii image | qr_photo.c, ui.c | Streaming SD PNG adaptation, source head/body previews; physical SD write unverified |
| Camera QR recognition | camera_ds.c, qr_scan.c, main.c | DSi-only camera entry; portable camera-sized decode tested; sensor test pending |
| Photo-to-Mii recognition | Retained original recognition data | Engine/feature mapping unfinished; DSi-only target |
| Nintendo local wireless to DS/3DS/Wii U | Future transport | Not implemented; direct stock Wii U compatibility requires its actual protocol |
| Wii Mii Channel | Retained Tomodachi/reference resources | Stock path receives from Wii; sending into Wii needs a compatible receiver, not a renamed stock receive option |
| Original audio | Retained EditSound.bcsar | Conversion/playback/event mapping unfinished |

`SOURCE_MAP.json` inventories all extracted layouts, stored fields and embedded assets with hashes. `mii-fields.json`, `body-models.json`, `body-animation.json`, `profile-layouts.json`, `qr-layouts.json` and `number-font.json` provide the detailed per-format maps. Raw Nintendo resources and generated private data reports remain outside the source-only GitHub repository.
