# M83 — SelectBalloonButton runtime evidence and remaining work

## Current source implementation (repository inspection)

- `tools/extract_balloon_layout.py` reads the private `SelectBalloonButton.bclyt` member, validates the CLYT header/sections, walks nested `pas1/pae1` hierarchy, composes parent/local affine transforms, preserves pane order separately from drawable paint order, and computes corner-based DS-space bounds.
- Required source panes are `B_Favorite`, `I_Favorite`, `I_MyMii`, `I_MiiCopy`, and `I_MiiOpen`.
- Its output deliberately sets `runtime_anchor_verified: false`. A supplied scene affine is only a candidate; it is not proof of the original 3DS runtime scene transform.
- `tools/check_gallery_anchor.py` is a fail-closed collision preflight. It checks candidate bounds against current gallery slots, room arrows, and provisional action hit regions. It also rejects any attempt to treat the preflight as runtime-anchor verification.
- `source/gallery_balloon_clan.c` exposes Select, Unselect, Decide and UnDecide playback using decoded numeric CLAN curve samples. Selection changes currently schedule Unselect then Select; Favorite press/commit schedules Decide/UnDecide. The source comments explicitly state that the original 3DS runtime event bindings remain unverified.

## Evidence boundary

The private melonDS acceptance run #41557889743 verified the current original-resource ROM's gallery, Favorite, Copy, Edit and received-Mii workflows. It did **not** prove the original 3DS scene anchor, final pane positions, or frame-accurate SelectBalloonButton event dispatch. The successful private ROM and framebuffer artifact is encrypted and owner-only; no proprietary payload is included here.

## M83 remaining implementation gates

1. Obtain original-runtime measurements for at least four independent pane centers, tied to a source build/resource hash and a documented capture method.
2. Fit and validate the scene affine against those measurements; reject outliers/degenerate geometry and retain an explicit unverified state until independent residual checks pass.
3. Resolve all relevant pane visibility, alpha inheritance, clipping, z-order, and transformed touch bounds.
4. Recover the original event-to-clip dispatch and source timing for Select/Unselect/Decide/UnDecide; do not infer event bindings from clip names.
5. Wire measured hitboxes and event dispatch only after the evidence gates pass; keep current provisional DS hit regions as fallback until then.
6. Run portable regression tests and latest private melonDS acceptance; encrypt all private diagnostics and clean the runner.

## Security

Never commit original Nintendo layouts, textures, ROMs, decrypted captures, private reports, or unencrypted CI artifacts. Public test fixtures must remain synthetic and must not be described as original-game evidence.
