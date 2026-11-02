# Weekly release and feature-parity audit — 2026-11-02 (Monday)

## Scope and baseline

Repository: `abudndle/mii-maker-ds`. Audited merged `main` at
`3deebf9619a452acd657a340d206cde2335deedd` (PR #207).
This is a source/Actions audit, **not** a new original-resource ROM build or
live melonDS run. This audit and its workflow changes are proposed on a
separate branch; they do not establish that the latest ROM has booted.

The highest-priority open milestone is [M81 / issue #84](https://github.com/abudndle/mii-maker-ds/issues/84).
PR #207 was merged after seven applicable PR checks passed on head
`2e51601de6e291eccf5bf2376000bdf4545c710a`: BlocksDS synthetic
ARM9/ARM7 compile smoke, portable host, portable source, gallery Favorite,
original balloon CLAN, continuous validation, and private-build provenance.
New `main` push checks were still running at audit time. Do not confuse
these source-only/synthetic checks with a private ROM or emulator result.

## Original 3DS feature parity

| Area | Verified in source or prior evidence | Release acceptance still required |
| --- | --- | --- |
| Original resources | Private resource recovery and manifest checks exist; source-only repository excludes Nintendo payloads. | Fresh source-hash/asset validation at the final commit and byte-for-byte NitroFS audit. |
| Models and rendering | Original CFL head and male/female body streams are integrated; original motion packs cover 53 clips. | Side-by-side 3DS/DS screenshots for geometry, material, lighting, proportions, texture and animation timing. |
| Gallery and rooms | 100 slots, multi-Mii room preview, drag/swap, room navigation and save-backed selection have implementations and host regressions. | Latest private ROM: 10 independently rendered Miis, drag across rooms, EEPROM fixture recognition, cold restart and persisted state. |
| Personal/Favorite | First-boot Personal Mii protection, ownership, favorite cap and touch Favorite/Copy/Edit paths have source tests. | Actual gold/red/blue/gray pants and crown display, received-Mii permissions, modal and save rollback on emulator/hardware. |
| Original gallery UI | Source CLYT pane hierarchy and numeric Select/Unselect/Decide/UnDecide CLAN tracks are implemented. | Measure authentic runtime SelectBalloonButton scene anchor; verify hierarchy/layering, actual DS hitboxes, source choreography and visual captures. |
| Editor and profiles | 13 editor pages, Unicode profile fields, source-driven icons and controls exist. | Screen-by-screen original reference comparison, input and save/restart acceptance. |
| QR, DSi and transfer | QR codec, export paths and DSi camera gates have source coverage. | Stock-system QR exchange, physical SD, DSi sensor, create-from-photo recognition and wireless DS/3DS/Wii/Wii U transport. |
| Sound and polish | Original sound archive is retained privately. | Original audio conversion, event binding, menu transitions and performance measurement. |

**Release decision: NOT READY.** Passing CI does not satisfy the
[completion gates](../reference/COMPLETION_GATES.md) or the
[feature-port map](../reference/FEATURE_PORT_MAP.md). The original 3DS ARM11
executable is not a DS ARM9 binary; the port uses separately authored DS code
with original resources.

## Actual private build and emulator evidence

The historical private original-resource run
[41256672205](https://github.com/abudndle/mii-maker-ds/actions/runs/41256672205)
on 2026-11-01, old milestone branch
`11d5ecff16d48ab6a1370eb237c6602cd8a2746a`, passed secret presence,
ZIP download/validation, extraction, original renderer checks, BlocksDS
compilation and ROM validators. Its melonDS step **failed before displaying
the ROM** because the AppImage loader could not find `libEGL.so.1`.
The current workflow source includes `libegl1` in its emulator dependency
installation; no latest-main private rerun was observed during this audit.
The old run is **not** M81 acceptance evidence.

The private build workflow previously listened only to historical milestone
branches and manual dispatch, so merging to `main` did not automatically
test the latest original-resource ROM. This audit proposes adding trusted
`main` pushes, a daily 14:30 UTC private acceptance run, and per-ref
concurrency. No `pull_request` trigger is added: PRs continue to run
asset-free checks. Private ROMs and screenshots remain GPG-encrypted before
artifact upload, and Nintendo resources must never enter public commits.

## Open work in priority order

1. **M81 remains open:** obtain four or more independently measured,
   source-hash-matched original runtime pane centers; fit the affine with
   `tools/calibrate_balloon_scene.py`, reject collisions with
   `tools/check_gallery_anchor.py`, and confirm original UI placement.
   Candidate fits with `runtime_anchor_verified: false` are not proof.
2. Rebuild from the **same final commit** with the owner's private ZIP and
   BlocksDS, then run the full ROM validation suite and real melonDS
   first-boot, gallery, Favorite/Copy/Edit, drag, save and cold-restart probes.
   Record commit, archive/ROM SHA-256, emulator result and protected captures.
3. After M81 is actually verified, close issue #84 and activate exactly one
   next milestone for the largest remaining original scene/model/animation
   parity gap. Do not close M81 on source CI alone.
4. Review older stacked PRs (#1–#5, #17, #66–#68) against current main
   before merging; they are not evidence of current integration. PR #96
   duplicates private asset verification but uses raw `unzip` extraction
   rather than the established validated restore path: do not merge it
   without a security and relevance review.

At audit time there was one open GitHub issue (#84), below the five-active-
milestone cap. The next run should resume this open milestone rather than
restart completed M78–M80 work.
