# M84: private original-runtime scene evidence format (version 1)

The calibration code is asset-free, but the **input measurement record and source layout are private** and must not be committed or uploaded to public CI artifacts. A matching SHA-256 and a self-reported `original-3ds-runtime` provenance field **do not prove authenticity**: review against the original capture and build is still required. Nothing in this pipeline sets `runtime_anchor_verified: true`.

## Required measurements

Use an independently captured and audited 256×192 bottom-screen image, upright, with X increasing to the right and Y downward. If captured at native 3DS 320×240 resolution, document and reproduce the preprocessing in the private workspace; the SHA-256 refers to the **actual normalized 256×192 input frame**, not its source file. Record at least **five distinct fit pane centers and two other, never-fitted holdout pane centers**, by matching names against the unanchored private CLYT layout report. Do not reuse holdout pane identities in the fit set.

### JSON shape (placeholders, NOT actual 3DS evidence)

```json
{
  "schema_version": 1,
  "source_sha256": "<64 lower-case hex digits of unanchored source layout>",
  "capture": {
    "sha256": "<64 lower-case hex digits of normalized private capture>",
    "width": 256,
    "height": 192,
    "screen": "bottom",
    "orientation": "upright",
    "coordinate_system": "DS-bottom-top-left"
  },
  "provenance": {
    "kind": "original-3ds-runtime",
    "capture_method": "Describe device, original build, capture method, downsampling and visual feature matching"
  },
  "fit_points": [
    {"pane": "UniquePaneA", "ds_center": [20, 30]},
    {"pane": "UniquePaneB", "ds_center": [70, 30]},
    {"pane": "UniquePaneC", "ds_center": [20, 80]},
    {"pane": "UniquePaneD", "ds_center": [70, 80]},
    {"pane": "UniquePaneE", "ds_center": [110, 100]}
  ],
  "holdout_points": [
    {"pane": "DifferentPaneF", "ds_center": [100, 40]},
    {"pane": "DifferentPaneG", "ds_center": [55, 120]}
  ]
}
```

The pane identifiers and coordinates above are **invented schema examples only**, not a claim about actual CLYT pane names or the 3DS display. Use actual pane names and visually measured coordinates inside the private workspace.

Run:

```sh
python3 tools/validate_balloon_scene_evidence.py private-layout.json private-evidence.json --capture private-normalized-bottom.png --output private-candidate-report.json --max-error 2
```

The CLI requires the actual private normalized 256×192 PNG and checks its file SHA-256 against the evidence record and its PNG IHDR dimensions/CRC before writing a report. A plausible hash written in JSON is not enough, and these checks do not prove original-console provenance. The private image must never be committed or uploaded in plaintext.\n\nThe validator checks hash agreement, capture metadata, unique pane IDs, plausible coordinates, at least five fit points with leave-one-out checks, at least two separate held-out points, transform conditioning and per-holdout errors. The output records the canonical evidence SHA-256, capture hash, affine transform, residuals and determinant, and **always** marks the anchor unverified. Keep the report private because fitted coordinates may derive from owner-supplied original resources.

Next: independently audit the actual 3DS runtime capture provenance, compare fitted pane corners and real button bounding boxes against melonDS and original frames, then verify original `SelectBalloonButton` clip dispatch/timing. Do not enable original-geometry hitboxes on the strength of synthetic or unaudited reports.
