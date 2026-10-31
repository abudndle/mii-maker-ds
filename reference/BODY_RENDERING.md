# Original body and editor mapping

The renderer now includes the supplied application's original `MaleBody.bcmdl` and `FemaleBody.bcmdl` geometry. It does not use replacement body shapes. `tools/body_models.py` independently reads the CGFX shape, interleaved vertex attributes, face descriptors, rigid bone palettes and skeleton hierarchy. It reads the scalar transform channels at frame zero of the supplied `MiiAnim.arc/Wait00.bcskla` and bakes that pose into the runtime mesh.

`body-models.json` records each source SHA-256, shape/submesh offsets, vertex stride, attribute format and scale, raw vertex/index offsets, palette and triangle count. The male model contributes 476 visible triangles, the female model 480. The separate two-triangle shadow plane is omitted. Both use the original 18-bone hierarchy. The head is attached through the original head-bone matrix, rather than placed on an invented torso. Runtime files are `nitrofiles/models/MaleBody.bin` and `FemaleBody.bin` (`BOD2`, a bounded independent intermediate format).

Format observations were cross-checked against the primary implementation https://github.com/gdkchan/SPICA at commit `82acbd63695e4ef8b95a92ce884f25ec1044788f`. The independent Python reader is project code; no SPICA implementation or third-party runtime is vendored. Regeneration requires Python, NumPy and the already extracted user assets; compiling the supplied project uses the generated model binaries.

## Original data to runtime

| Original data | Runtime mapping | Fidelity limit |
|---|---|---|
| Shape indices, triangle indices, position/normal attributes | `tools/body_models.py` emits original triangles and posed normals; `source/head.c` rasterizes them | DS RGB555 output and software rasterization |
| Submesh bone indices and rigid skinning | Original palette resolves each vertex to the original skeleton bone | These supplied body meshes use rigid skinning; the converter rejects smooth skinning |
| Bone scale/rotation/translation and parent indices | Parent-composed SRT matrices with original `Wait00` frame-zero channels | 24 sampled original idle poses, original Hermite curves decoded; other animations and exact original timing pending |
| Original head-bone matrix | CFL mesh placement uses the source attachment transform | Camera and lighting remain provisional |
| Body material index and hand-bone assignment | Favorite-color clothing, skin-colored hands and dark trousers | Full original GPU material/shader evaluation is not implemented |
| Height/build fields and `B_BgSlide_00/01` | Slider values change body geometry and original knob positions | Body proportion coefficients are provisional DS mappings, not a recovered original function |
| Editor transform button icon resources | `source/transform.c` maps Down/Up, Enlarge/Reduce, Rotate, Near/Wide, Stretch/Narrow, Left/Right and Reset | Original slider bounds are used; complete original per-style reset/range rules are not established |
| `EditFaceTab` | Original shape/makeup/lines buttons open their corresponding pages | Full original animation and remaining secondary tabs pending |

`source/ui.c` now shows the original Mii model in portrait/full-body editor views and a selected full-body Mii above the gallery grid. The development heading, field numbers and slot listing are removed. A proportional DejaVu Sans substitute replaces the development monospace text. Alpha-only original icons use their material tint; button masks/texture wrapping are applied to editor pages. Original slider knobs move with their stored values.

This is closer to the original presentation, not a claim of an exact original renderer. Nintendo's shared font, exact camera/lighting/materials, complete animation coverage, plaza staging and several flows remain incomplete. The original compiled executable is retained as evidence; Nintendo C/C++ source was not recovered and does not run directly on DS hardware.

See `ANIMATION_RENDERING.md` and `body-animation.json` for the source-curve decoder, sample schedule, input cancellation and timing limits.
