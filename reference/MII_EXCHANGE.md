# Original Mii records, QR images and received status

`source/mii_codec.c` independently maps the 96-byte CFLStoreData/Ver3StoreData format to DS appearance/profile fields. `mii-fields.json` lists byte offsets, bit widths and inversions. The reference is devkitPro/libctru `libctru/include/3ds/mii.h` (blob 38e2674a812106b7added5b085d8de9b53487552), with the recovered eyebrow word from jamesrhg/cfl-mii: five rotation bits, four spacing bits and five height bits. The earlier libctru eyebrow declaration has a different bit split and is not blindly used.

Decoding checks length, version, CRC-16/XMODEM, supported field ranges, date consistency and UTF-16 names. Invalid data never partially replaces the output record. Encoding an existing `MdsMiiRecord` preserves its original console/creator identity, options and reserved bytes while updating editable fields and CRC. The raw record and private gallery are different objects: gallery imports retain visible profile/appearance and policy/status, while the complete original identity remains in the source file rather than the compact save. Imported Favorites/Personal ownership are cleared. Copy-disabled received Miis remain usable but cannot be edited or copied.

Send/Receive currently opens the DS file-import adaptation. Put `.cfsd` or `.ffsd` files in `MiiMaker/Import` on the DSi SD card or DS flashcart card. Up/down selects; A or Import commits to the first free slot; B returns; X/Rescan refreshes. Names are sorted, directories and other extensions are ignored, and the list is bounded to 100 entries. Persistence failures roll back the gallery. The first locally created Mii becomes Personal even if foreign Miis were imported first.

The private compact save is now version 2, retaining its 8 KiB size and 100 slots. A previously temporary character-input field stores received/special status. Version-1 compact and MDS2 legacy records migrate that obsolete input byte to zero while retaining full nickname/creator strings. The Personal Mii is normalized to a Favorite. New private packets use MDS3. Unknown/corrupt saves are still refused; there is no CFL_DB.dat import or dependency.

## QR and photos

The envelope is eight nonce bytes, 88 ciphertext bytes and a 16-byte tag. The nonce comes from original record bytes 12–19 and is padded with four zero bytes for AES-CCM. The 3DS authenticates a padded 96-byte length, although only 88 encrypted bytes are stored. This behavior is independently implemented and checked against PyCryptodome with reconstructed padding. Format observations: https://gist.github.com/jaames/96ce8daa11b61b758b6b0227b55f9f78 and Genwald/MiiPort `include/mii_qr.hpp` / `include/ccm_3ds.h` at 15a3032dd2e929c8b3686fd357b7b86032794dac. The published interoperability key is used; no account credential or user console secret is required.

QR images use version 10, high error correction, and four quiet modules. The extracted `QR/BtnQR` menu and `Dialog/DialogPhotoSelect` provide the original buttons, labels, artwork and hitboxes. Scan is hidden in DS/DS Lite mode. The app can display a generated QR without an SD card; saving still reports the missing card. QR photos and face/entire-Mii pictures stream as lossless 400×240 PNGs into `MiiMaker/Photos`, using non-overwriting names and failed-write cleanup. This does not register files in Nintendo DSi Camera's proprietary album database. The original game used JPEG; this demake currently writes PNG.

For gallery exports, `mds_cfs_create` assigns a new normal DS-family software identity using the export time and a synthetic locally administered MAC derived from the private record. It does not claim to preserve the original hardware identity of an imported copy. Special-record QR re-export from the gallery is currently unavailable. An existing raw record can be wrapped without regenerating its identity through the codec API.

QR camera scanning is DSi-only. The portable quirc image decoder reads a 256×192 RGB555 frame, then authenticates/decrypts the payload and checks the Mii record. Successful imports use the same transactional gallery path. This is QR recognition, not unfinished photo-to-Mii face recognition. Physical DSi camera capture and stock 3DS/Wii U scanner interoperability still require hardware testing. SD file writes are unit-tested through the portable PNG encoder and native missing-card path, not verified on physical cards.

## Ownership and original status artwork

The original 3DS `I_MyMii` and `I_Favorite` panes are extracted with their material tint. They mark Personal/Favorite state; Personal cannot be unfavorited or deleted. Received and special flags persist independently of copying permission. Pants use gray, red, blue or gold software tints according to status; exact shader/material matching remains pending. Wii U's separate bronze crown for another local user account has no corresponding account object in this single-profile DS app and is not fabricated.

Nintendo's Wii U status reference: https://en-americas-support.nintendo.com/app/answers/detail/a_id/2465 . Original 3DS menu resources remain the visual source for this port.

## Tests

`tests/mii_codec.c` uses a fictional reference fixture generated against the libctru structure plus the corrected eyebrow word and an independent polynomial CRC. It checks every editable-field maximum, metadata-preserving round trips, UTF-16 and all one-byte corruptions/truncations. `tests/save_migration.c` covers old-format migration. `tests/mii_qr.c` verifies an independent encrypted vector, tamper rejection, PNG output and QR extraction from a camera-sized synthetic frame. `tests/qr_interop.py` uses independent AES and ZXing libraries and can inspect the actual emulator QR screenshot.

The native import test uses `MDS_IMPORT_TEST_FILES` and read-only fictional NitroFS fixtures to exercise the ARM application flow and cartridge persistence. It does not simulate a real SD card. Release preflight refuses that fixture folder unless the test flag is explicit. Production missing-card behavior is tested separately. No test modifies guest RAM.
