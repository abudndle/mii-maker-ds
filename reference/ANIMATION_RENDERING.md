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

## CLAN home material/vertex visual milestone

The DS home-menu selection border now evaluates nine properties from the user's
original `PlazaTop_Select` clip: four CLPA Y positions, three CLMC RGB
channels, one CLMC alpha, and one CLVC shadow opacity. A deterministic
`tools/generate_clan_home_visual.py` converts the original numeric-key metadata
from `tools/clan_keyframes.py` into a small fixed-point header, excluding
copyrighted image/audio/model/binary CLAN payloads.

`source/clan_home.[ch]` evaluates all nine on the VBlank clock.
`source/clan_overlay.[ch]` blends a colored two-pixel outline and a
one-pixel shadow using clipped RGB555 software compositing.
`source/ui.c` applies the result to the home selection only; its
original background bitmap is redrawn before each cue, and completion
restores the fixed baseline border. The reconstruction **adapts** original
pane color and shadow opacity to the DS bitmap menu; it does not reproduce
the original 3DS shadow mesh, textures, pane hierarchy, or all 327 timelines.

Host CI tests include color/opacity endpoints, halfway values, all four
menu slots, timer wrap, RGB555 blending, pixel clipping (including extreme
coordinates) and six generator-corruption cases. The actual DS ROM still
needs BlocksDS build and melonDS visual/hardware testing.

## Original dialog pane entrance animation milestone

The `Dialog.arc.files/DialogBase00_DialogIn.bclan` original `W_Dialog`
pane Y track has three Hermite keys: frame 0 at -240, frame 17 at +2, and
frame 20 at 0 (21 source frames). `tools/generate_clan_dialog.py`
reproduces a small numeric-only header using the user's private
`clan_curves.json` metadata; no original Nintendo game archive is published.

`source/clan_dialog.[ch]` samples this curve with the existing Q16.16
Hermite evaluator at a provisional 30 fps, rescales original 240-pixel
coordinates to 192-pixel DS screen space, and shifts the freshly rendered
profile-bottom bitmap in place using a bounded RGB555 row move.
The profile page and nested profile dialogs now start an entrance motion
when opened. The UI begins the animation at the first rendered frame to
avoid skipping it during expensive model rasterization, and performs an
unshifted final redraw even if the game missed intermediate VBlanks.
The underlying profile touch hitboxes remain at their normal positions.

The current implementation animates the full reconstructed bottom panel,
not the original independent CLYT pane hierarchy. This is not a complete
replacement for original dialog exit sequences, texture/material animations,
or all 327 CLAN clips. The full private ROM is **not** yet built or
visually validated in melonDS after this milestone.

## Original CLAN dialog exit milestone

The DS profile screen now uses three original `Dialog.arc.files`
`W_Dialog` Y curves: `DialogBase00_DialogIn`,
`DialogBase00_DialogOut`, and `DialogBase00_DialogOutUp`.
The source exit keys are (0,0,-14.117647), (17,-240,0)
for the upward exit and (0,0,0), (17,+240,0) for the downward
exit, from 21-frame source clips. `tools/generate_clan_dialog.py`
reconstructs a numeric-only C header from the user's local
private CLAN metadata without publishing original binary resources.

In `source/main.c`, Back from the root profile now stages a
DialogOut transition before returning to the editor. Cancel,
confirm, or X-clear from a nested profile page stage DialogOutUp
before showing the root profile page. Input is ignored during
the pending exit so modal navigation cannot skip the animation.
The previous profile state remains visually displayed while the
underlying edit/cancel operation is already committed. Completion
is checked independently of other screen redraw conditions.
`source/ui.c` redraws the unmodified profile source bitmap for
every translated frame. Clip positions retain 240-to-192 DS scaling.

Limitations: these animations move the *reconstructed whole panel*,
not original individual CLYT pane geometry. The source 30-fps
cadence is provisional, and no real BlocksDS ROM or melonDS
visual parity run is confirmed for this milestone.

## Original editor selection animations: tab material RGB and feature scale

The DS editor now uses numeric tracks from the user's original
`Editor.arc.files/EditorCommon_Select`, `EditHair_Select` and
`EditFace_Select` CLAN clips. `tools/generate_clan_editor.py` extracts
eight source-derived tracks into a small Q16.16 header: tab icon CLMC
red/green/blue, pane CLMC red/green/blue, and selected feature CLPA X-scale
curves (1.00→1.08→1.00 and 1.00→1.10→1.00).

`source/clan_editor.[ch]` maps the existing 13 DS editor categories to
eight original tabs, plays the selected item enlargement at 30fps over
the VBlank clock, and evaluates original tab colors. `source/ui.c`
applies color to a reconstructed selection border and enlarges only
the currently selected feature icon using the previously supplied
original feature art. Input and touch hitboxes remain stationary.
`source/main.c` retriggers on actual category/item selection changes,
begins timing at first draw to tolerate expensive software previews,
and redraws the original unmodified bitmap on completion.

The color transition affects the DS outlines, not the original CLYT
material hierarchy; scaling affects selected feature sprites, not every
3DS pane. All original game resources remain private. The ROM still
requires a BlocksDS build plus actual melonDS and DS/DSi visual/input tests.

## Original editor arrow and change-button feedback milestone

Original user-provided `EditEye_Decide` and `EditHair_Decide` BCLAN
tracks supply nine numeric-only property channels: four `P_Change_00`
translation/material tracks, three `P_BtnArrowR` material RGB tracks,
and the Eye/Hair arrow Y motion tracks. The keyframes are reproduced
from private metadata by `tools/generate_clan_adjust.py` without shipping
the original BCLAN, texture, or layout files in public source control.

`source/clan_adjust.[ch]` evaluates these clips with the shared ARM9
Q16.16 Hermite evaluator on the 60 Hz clock. Its first-paint timing,
timer-wrap, input cancellation, and final redraw preserve static
editor screens even if a model render takes multiple VBlanks.
`source/ui.c` maps real original `B_ArrowL`, `B_ArrowR` and
`B_Change*` hitbox coordinates onto the live DS bitmap for short
colored outline/translation cues, while the original icon and hitbox
coordinates remain intact. Keyboard adjustments trigger feedback
only when the underlying avatar field changes; touch-based
transforms and arrow navigation trigger the same effect.

The original pane transform is **adapted as a border overlay**, not a
complete reconstruction of source CLYT materials/geometry.
Only these Decide tracks have been attached. The full original
menu audio and remaining clips are not yet ported. Host C/ASan/UBSan
and source-generator tests do not replace BlocksDS ROM compilation,
melonds image comparisons, or physical DS/DSi verification.

## Editor CLAN button release and invalid-selection feedback milestone

The private original `EditEye_UnDecide` animation contains actual
`P_BtnArrowR` CLMC RGB release keys at frames 0 and 1
(150,200,172)→(255,255,255); `EditEye_Invalid` has a distinct
held `P_Change_00` material RGB (228,230,228) and opacity 80.
`tools/generate_clan_adjust.py` now regenerates **21** keyframe tracks
across the original Decide, UnDecide, and Invalid CLAN clips, without
shipping original Nintendo binary assets.

`source/clan_adjust.[ch]` supports three states: Press, Release,
Invalid. Release starts when the stylus/keyboard button goes up,
or automatically after the press phase, ensuring even a dropped release
event cannot leave a pressed appearance stuck on screen. Invalid
feedback uses the original source state colors and alpha; because the
original Invalid tracks are mostly single held keys rather than a
recoverable error pulse, the visible hold duration is a DS adaptation.
The exit always redraws the underlying original editor bitmap.

`source/main.c` queues all `keysUp()` events (not just touch),
and routes key-up into the real editor UI. `source/ui.c` detects
no-op bounded touch transforms and unmodified keyboard adjustments,
using Invalid rather than a successful press cue. Touch targets,
original feature images and game-data changes are unaffected.

This source-level milestone is not complete 3DS CLYT animation
playback. Exact invalid-state scene choreography and material hierarchy,
console-ROM build and live melonDS acceptance remain unfinished.
