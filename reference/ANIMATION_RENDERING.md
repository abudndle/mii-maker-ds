# Original skeletal motion and DS presentation

The supplied male/female CGFX triangle streams, rigid bone palettes and 18-bone hierarchy remain the geometry source. No substitute meshes or authored motion poses are used. `animation_curves.py` decodes source scalar curves, including Hermite values/tangents; `body_models.py` composes the original scale/rotation/translation hierarchy. Source-format observations were cross-checked against SPICA at commit 82acbd63695e4ef8b95a92ce884f25ec1044788f; no implementation from that project is vendored.

`motion_pack.py` evaluates every integer source frame of all 53 clips for both original body rigs: 12,164 body/frame combinations. MSP1 stores a 32-byte header, 40-byte named clip entries and 912-byte frames. Each frame holds the original 12-float head-bone world matrix and eighteen fixed-point 3x4 transforms relative to the existing original Wait00 frame-zero mesh. Headers and fields are little-endian; transforms use signed Q16.16. `motion-pack.json` records source/output hashes, source frame counts and source loop flags.

`motion.c` validates the complete directory/length before retaining a borrowed FILE. It reads only the requested frame, bounds matrices and bone indices, transforms the original positions/normals, and emits BOD3: an eight-byte magic/count prefix, 48-byte head matrix, then 18-byte vertices (three signed 32-bit coordinates at 1/128 model unit, three signed byte normals at 1/127, original material and bone IDs, one padding byte). Wider coordinates retain original motions that exceed BOD2's 16-bit range. Original vertex order and triangle topology are unchanged. This is a private conversion format, not Nintendo serialization.

The runtime keeps two pose buffers and tiny clip directories; full animation packs stay in NitroFS. It avoids allocating the older complete-mesh ANI1 animations when MSP1 loads successfully. The old 24-pose files/parser remain a runtime fallback for older resources. All 53 clips are playable by the skeletal engine. The editor binds Wait00; the gallery sequences Wait00, Wait01, Wait02, Wait03Pre, Wait03 and Wait04 on the selected upper-screen Mii. This playlist is independently authored. Original plaza/event choreography, scene translations/cameras, facial expressions and the 327 CLAN GUI tracks are not fully bound.

Timing still assumes 30 source fps, driven by a 60 Hz VBlank clock. The original executable's timing has not been recovered. Playback selects the current source frame rather than waiting for every preceding render; slow software rendering can drop frames. Skeletal playback support is not a claim of frame-perfect original scene reproduction or smooth physical DS performance.

`tests/motion.c` covers asset-free format bounds, malformed/truncated files, looping and one-shot endpoint behavior, long clocks, invalid matrices and transform output. `tests/motion_assets.c` transforms all 12,164 source frames, then compares and renders 316 first/middle/last poses against independent full-geometry conversion by `motion_reference.py`. The observed maximum difference is 1/128 model unit for coordinates and 2/127 for normals, from fixed-point/byte quantization. Original topology/material/bone IDs and head matrices match. These tests use ASan/UBSan. The native melonDS test verifies both complete packs load, visible idle motion changes without altering Mii fields, and the gallery reaches all six idle clips. No guest RAM is modified by those checks.

The top image is composed in RAM and presented only as a complete frame. New queued input cancels unfinished rendering and retains the previous frame. Body sliders capture the stylus continuously, clamp 0–127 outside the track, and redraw their knobs independently of expensive model previews. Rendering remains a software implementation; original camera/light/material fidelity and body-proportion coefficients still need work.

Regenerate local data with `python3 tools/motion_pack.py`; run the reference generator with `python3 tools/motion_reference.py`. Original resources and generated private reports stay outside the source-only GitHub repository.

## DS scene-transition milestone

The home↔gallery navigation now starts a ten-VBlank, deterministic software fade on the bottom display. `source/gui_tween.c` handles timing and VBlank wrap; `source/ui.c` keeps an unmodified 256×192 base image and regenerates each fade frame from that base so repeated stepping does not progressively darken the source. A redraw replaces the cached base, and the transition stops at full brightness. The event loop starts the fade only on home/gallery changes, so editor/body previews and camera mode are not intentionally animated by this code. `tests/gui_tween.c` covers interpolation endpoints, timer wrap and zero-duration behavior.

This is an independently implemented DS transition, **not** a decoded reproduction of the original 3DS CLAN tracks. The original resource timeline format, per-widget bindings, original fade choreography and their visual timing still need to be ported. The full updated ROM has not yet been built or emulator-tested after this change; actual screen behavior remains unverified.

## Decoded original CLAN property-curve milestone

The private Mii Maker resource ZIP has 327 valid CLAN animations containing **13,366**
numeric animation channels (CLPA 782, CLVC 1,989, CLMC 10,580, CLVI 14,
CLTP 1). The earlier 8,290 count described a narrower pane-tag inventory,
not the full channel count. `tools/clan_keyframes.py` decodes bounded source
frames, values, tangents and discrete visibility/pattern keys without copying
Nintendo binary resources into the public Git repository.

`source/clan_curve.[ch]` evaluates float tracks in Q16.16 with cubic Hermite
interpolation and duplicated-frame endpoint rules; `source/clan_home.[ch]`
adapts four original PlazaTop_Select CLPA pane-Y curves into a 2-3 pixel
focus-outline cue on the existing DS home background. The state loop redraws
once after the motion finishes, including when a slow render skipped its final
animation frame. This is only one adapted original motion property, **not**
full CLYT pane hierarchy or original CLMC/CLVC material/vertex playback.
Local source tests used GCC/UBSan and compared 40,053 source samples against
the floating reference (worst error 0.039 source units). The original DS
ROM has not been built or boot-tested for this milestone.
