# 3DS Mii Maker parity target — current status

Requirements retained: original 3DS look and feature choices, DS/DS Lite operation, DSi-only camera, DS/3DS/Wii connectivity targets, and ROM-associated saving. Tomodachi Collection guides the DS implementation; it is not the application being ported.

| Feature | Current implementation / evidence | Remaining work |
|---|---|---|
| Original UI | Original home menu and gallery grid, 558 textures, 94 parsed layouts, 13 native editor pages | Complete materials, shared alphabet font, animation, remaining submenus and original international keyboard |
| Face/body display | Supplied original CFL meshes/textures now drive editor/gallery head previews | All 53 original clips have streamed full-source-frame skeletal playback; six idle clips bind to editor/gallery; exact camera/light/materials, proportions, timing and remaining event choreography incomplete |
| Face, hair, eyes, brows, nose, mouth, glasses, facial hair, mole | Original choice icons, touch selection and model fields | Verified original parameter ranges and accurate material/transform behavior |
| Colors, hair flip, body proportions | Native color-swatch, flip and slider handlers using extracted bounds; color/body paths tested in emulator | Continuous captured stylus dragging with 0–127 clamps; knobs stay independent of expensive preview rendering, which refreshes on pause/release; exact proportions and selection effects pending |
| Profile and naming | Original profile/gender/color/date/permission layouts, nickname/creator touch entry, strict 10-UTF16-unit limits, birthday validation and original numerals; native save/restart tested; controller focus, button typing and accessory selection | Full international keyboard and original shared alphabet font; DS keyboard is an adaptation |
| Gallery | 100 slots, D-pad navigation, draft/save/delete flow, protected personal Mii; confirmed stable name/favorites sorting with touch and buttons, selection retention, both save formats and failed-write rollback | International name collation, remaining original dialogs and complete future import/transfer permissions; local permission-aware copy is tested |
| ROM-associated saves | New 8 KiB snapshot supports 100 slots and melonDS defaults; legacy 64 KiB bank saves retained; writes/readback and cold restart tested; boot/status warnings, read retry, unknown/damaged-save write blocking and retained drafts | Compact format lacks full second-bank recovery; real hardware and flashcart mapping untested |
| Draft protection | Discard/delete confirmation; transaction rollback on failed persistence | Original touch confirmation art implemented; remaining modal transitions incomplete |
| DSi camera | Compiled DSi-only preview/freeze/switch controller; DS camera gate tested | DSi sensor testing, full-resolution capture and accurate original camera UI |
| Photo-to-Mii | Original resources and recognition data retained | Recognition engine and feature mapping; preview is not automatic Mii creation |
| QR generation/scan | Standard 96-byte codec, 3DS authenticated envelope, version-10-H QR, original menu and face/body chooser, PNG photo export, portable camera-sized scanner; independent AES/ZXing and native-screen checks | Physical DSi sensor/SD and stock 3DS/Wii U checks; broader QR variants and special-record re-export |
| Image export | QR, full-Mii and face 400×240 PNG photos in MiiMaker/Photos; original selector; gallery BMP retained; unique names/error cleanup | Physical SD/flashcart writes, original JPEG and native DSi Camera album integration |
| DS ↔ DS communication | Original communication scenes/code extracted as reference | Discovery, transport, verified payload format, errors and two-system tests |
| DS ↔ 3DS communication | QR/data format implemented; direct wireless target only | Stock compatibility investigation or explicit companion endpoint; hardware tests |
| Wii Mii Channel import | Original DS messages and communication overlays identified | Discovery parameters, association, payload/ack handling, data conversion and stock Wii test |
| DS → Wii U | Stock Mii Maker Connect to Nintendo 3DS is the requested target | Native protocol implementation and stock-device tests; not provided by a QR or file conversion alone |
| Sending to Wii | Requested target | Determine stock receiver capability and supported downgrade behavior; may require a Wii companion; receive/send labels are not evidence of stock two-way support |
| Copy/sharing/favorite settings | Standard file/QR imports preserve policy; copy-disabled received Miis remain read-only; Personal/Favorite icons and status persist; copy and QR permission checks | Future wireless-policy enforcement, full original identity retention in the compact gallery |
| Standard Mii files | CFSD/FFSD import browser, strict CRC/UTF-16/date/range checks and transactional persistence | Complete raw hardware-identity retention in the private gallery; wider format conversions |
| Sound/effects | Original sound archive and effects retained | Conversion, playback and event timing |
| System behavior | Lid suspend/resume preserves drafts/dialogs and pauses animation; wake input waits for release; camera capture stops and restores sensor/frozen state; cartridge-save status/retry UI | Physical DS/DSi sleep/camera validation, exit and remaining device-specific error handling |

No network backend is presented as connected or supported. The private demake record format is not Nintendo Mii format. A resource extraction, compiled driver or reference-code location is not itself proof of completed feature compatibility.

## Specific dependencies

The separately supplied `CFL_Res.dat` is now embedded and rendered. The shared original font and application body/pose/plaza implementation remain incomplete. The DS NFL file remains a distinct technical reference. The wrong `CFL_DB.dat` database is not used or required.

The Wii transfer path is established by the patched DS message text and relevant overlay resource references. A wire protocol has not yet been recovered. Wii receive behavior and any desired DS-to-Wii behavior must be verified independently.

## Save transport constraints

New compact saves use an 8 KiB snapshot; legacy bank saves require a 64 KiB device. Both use the type-2 EEPROM protocol. The launched ROM's boot header must have game code MDSD, and only blank or recognized project save images are accepted. The backend does not erase flash chips or auto-detect arbitrary retail cartridges. Only a compatible emulator/loader or appropriate homebrew save device is a supported integration target. Physical device behavior remains untested.
