# GateTrace file guide

Descriptions follow the reviewed 237-file catalog. Links open the files in the adjacent repository directory.

## .gitattributes

[Open file](../repository/.gitattributes)

Preserve original file bytes in Git so automatic newline conversion does not break frozen hashes.

- Uses * -text repository-wide
- Comments explain preservation of scientific files and their line endings

**Inputs:** Git reads this attribute file.

**Outputs:** Controls text conversion during check-in and checkout.

**Usage:** Git uses it automatically when cloning or maintaining a frozen copy.

**Caution:** SHA verification separately checks file integrity; content correctness requires its own review.

**Current SHA256:** `b3dc2ae4210500cd7452d1faf7995a1bdc341f51a32abf0d8dc6d072fc3ac014`

## .gitignore

[Open file](../repository/.gitignore)

Reduce accidental addition of local data, answers, models and runtime outputs to Git.

- Ignores Python caches, virtual environments, runs and outputs
- Ignores datasets, weights, human_answers and answers
- Ignores image, video, weight and .env suffixes

**Inputs:** Git's untracked-file list.

**Outputs:** Affects default staging and status display.

**Usage:** Consult these rules when maintaining the repository.

**Caution:** Review already tracked files separately. Privacy review and access control remain separate safeguards.

**Current SHA256:** `f380476541508700d5818fa14f20e0d2dd28d488b02ebbe62b5d8aeb478af099`

## configs/pipeline_inputs.schema.json

[Open file](../repository/configs/pipeline_inputs.schema.json)

Define input-manifest structures for pixel, native v11 and GMC workflows.

- Common bindings require path, bytes and a 64-character lowercase SHA
- Restricts development sequences to 01/02 and their dimensions
- Pixel manifests bind weights and each frame image
- Native v11 manifests bind cache, geometry, G1, M4 policy and lineage; a separate GMC contract is included

**Inputs:** User-authored JSON input manifests.

**Outputs:** Structural constraints; does not read images or run models.

**Usage:** Choose one contract under oneOf when preparing pipeline inputs.

**Caution:** JSON Schema covers structure. The CLI additionally checks frame continuity, path containment and fixed weights.

**Current SHA256:** `601d22448dffe7735ed357d11c0470f5e2b7adfc8ae3f90f7057042bf0793c6b`

## configs/resource_cpu.json

[Open file](../repository/configs/resource_cpu.json)

Describe CPU resource entry points and input shapes in machine-readable form.

- Supported sequences and relative GT, seqinfo and track filenames
- Four resource entry-point paths
- Reference Python/NumPy and optional rendering notes
- Notes requiring new external outputs and prohibiting inference, training and network access

**Inputs:** Interface-description JSON for readers and tools.

**Outputs:** No results or scientific-parameter overrides.

**Usage:** Consult when configuring tools or checking path layouts.

**Caution:** Use this as interface documentation. Scientific thresholds are fixed in the implementation; the human_qc field preserves historical status.

**Current SHA256:** `db1ec1b65398a7c193983e3c78f3a7c36950f4d398eb4894823c7fea96bb1ab9`

## core/ANONYMITY.md

[Open file](../repository/core/ANONYMITY.md)

Describes which identity-related wording was changed for the anonymous review copy and which content was retained.

- Generalized identity-related wording in the workflow
- Statement that scientific data, code, numerical values, and provenance remain unchanged
- Anonymity reminders for hosting accounts, links, and archive metadata

**Inputs:** Data access: none

**Outputs:** Notes on the anonymous copy

**Usage:** Read when preparing anonymous review materials.

**Caution:** Scope: a record from creation of the anonymous copy. Public code or hashes may still support reverse association.

**Current SHA256:** `f35c98c1848bb7caade1f24e1fc015b65aad9011a53811b4a704be44fdde0093`

## core/ATTRIBUTION.md

[Open file](../repository/core/ATTRIBUTION.md)

Describes the provenance and attribution of MOT20, the example systems, and the frozen functions.

- Original MOT20 data and paper citation
- Notes on derived 01/02 labels and existing YOLOX-X + v11 outputs
- Distinction between third-party software, weights, and bundled code

**Inputs:** Data access: none

**Outputs:** Attribution and provenance notes

**Usage:** Read when citing, redistributing, or preparing materials for external presentation.

**Caution:** Scope: provenance paths are references. The original-data and bundled-code licenses apply to their respective materials.

**Current SHA256:** `02304b8b5ec8a98c7ec480de323fccb63e1d57420249ea4bd7e26ccc8d115e1c`

## core/CHANGES.md

[Open file](../repository/core/CHANGES.md)

Explains which fields were derived from the original annotations and which interfaces were added in v0.1.

- Semantics of coordinates, time, visibility, and rule-based confirmation
- Entry points, frozen functions, and examples added in v0.1
- Unchanged scientific rules and input restrictions

**Inputs:** Data access: none

**Outputs:** Derivation notes and version change history

**Usage:** Read when comparing versions or avoiding confusion between rule-based confirmation and human judgment.

**Caution:** Scope: version history at its original date. Current release approval is recorded separately.

**Current SHA256:** `8504c764e70084175901b41baa1529cef1135c5c462c7c646ccd995fb62aab66`

## core/check_inspector.py

[Open file](../repository/core/check_inspector.py)

Runs the event inspector's synthetic engineering checks centrally and generates a receipt.

- Whole-package verification before execution
- Discovery of tests/test_*.py and allocation of separate scratch directories
- --stdlib-only mode and log/receipt outputs

**Inputs:** Bundled synthetic test code; no real GT, tracks, images, or human answers required

**Outputs:** tests.log, receipt.json, started.json, and synthetic scratch directories

**Usage:** Consult this entry point to check protective logic after engineering changes to the inspector. This guide reviewed the code statically.

**Caution:** Scope: the synthetic engineering cases checked. Real-data rescoring and scientific conclusions require their own evidence.

**Current SHA256:** `a2910ef413753b3550f37565964e9d1f098ba255b2b22647489f65d0cd0cb902`

## core/DATA_LICENSE

[Open file](../repository/core/DATA_LICENSE)

Describes the license scope for derived labels, geometry, and numerical examples.

- CC BY-NC-SA 3.0 declaration and link to the governing legal text
- Original MOT20 provenance and attribution requirements
- Distinction between raw media, full GT, and code

**Inputs:** Data access: none

**Outputs:** Data license notes

**Usage:** Read before using or sharing derived data and numerical examples.

**Caution:** Scope: the data-license terms stated in this file. Code licensing is described in LICENSE_CODE.

**Current SHA256:** `1e41fc636502b14a6c426aa0602ddeb497893a6085af36da6186f76de6fa67c9`

## core/ENGINEERING_CHANGES.md

[Open file](../repository/core/ENGINEERING_CHANGES.md)

Explains changes to path checks, evidence sealing, and failure records in the event inspector.

- Three changes: I1 image paths, I2 evidence integrity, and I3 failure records
- Sealing scope limited to the six scoring evidence files consumed by the inspector
- Entry points for read-only reuse and synthetic checks

**Inputs:** Data access: none

**Outputs:** Engineering change notes and scope boundaries

**Usage:** Read to understand why the new Inspector requires a retained SHA256 or rejects an old evidence directory.

**Caution:** Scope: candidate and Adoption requires reflect the original document snapshot. Scientific verification is a separate evidence layer from engineering sealing.

**Current SHA256:** `6efd0801a86d99b036e26133487ea1cb76aaa763c22d4ca8636e4c38e91db872`

## core/examples/panel/bot/MOT20-01.txt

[Open file](../repository/core/examples/panel/bot/MOT20-01.txt)

Stores an example of per-frame BoT-SORT tracking outputs for MOT20-01.

- Ten-column MOTChallenge result per row: frame,id,x,y,w,h,conf,a,b,c
- One-based frame numbers and one-based top-left coordinates
- Within-frame output row order preserved for deterministic identity matching

**Inputs:** Static existing tracker outputs; tracking execution: none

**Outputs:** Text input read by score_tracker.py or the track parser

**Usage:** Inspect the format to see how BoT-SORT connects to the standard scoring interface; this file is for MOT20-01.

**Caution:** Requires: original within-frame row order. This guide checked only the first row column count; numerical track analysis is outside its scope.

**Current SHA256:** `e8eda5544e24847ef911303e6719f645c050e8bc882db4edc4028a8816e18692`

## core/examples/panel/bot/MOT20-02.txt

[Open file](../repository/core/examples/panel/bot/MOT20-02.txt)

Stores an example of per-frame BoT-SORT tracking outputs for MOT20-02.

- Ten-column MOTChallenge result per row: frame,id,x,y,w,h,conf,a,b,c
- One-based frame numbers and one-based top-left coordinates
- Within-frame output row order preserved for deterministic identity matching

**Inputs:** Static existing tracker outputs; tracking execution: none

**Outputs:** Text input read by score_tracker.py or the track parser

**Usage:** Inspect the format to see how BoT-SORT connects to the standard scoring interface; this file is for MOT20-02.

**Caution:** Requires: original within-frame row order. This guide checked only the first row column count; numerical track analysis is outside its scope.

**Current SHA256:** `954c994cdab1e8761dc23c98e4d0ef6be965559a8b86572d34a6364f80449abb`

## core/examples/panel/byte/MOT20-01.txt

[Open file](../repository/core/examples/panel/byte/MOT20-01.txt)

Stores an example of per-frame ByteTrack tracking outputs for MOT20-01.

- Ten-column MOTChallenge result per row: frame,id,x,y,w,h,conf,a,b,c
- One-based frame numbers and one-based top-left coordinates
- Within-frame output row order preserved for deterministic identity matching

**Inputs:** Static existing tracker outputs; tracking execution: none

**Outputs:** Text input read by score_tracker.py or the track parser

**Usage:** Inspect the format to see how ByteTrack connects to the standard scoring interface; this file is for MOT20-01.

**Caution:** Requires: original within-frame row order. This guide checked only the first row column count; numerical track analysis is outside its scope.

**Current SHA256:** `3fe9642f87b315acafe1b75ebd4b8a511cc4c8c727c0bba639be1590f985ac4a`

## core/examples/panel/byte/MOT20-02.txt

[Open file](../repository/core/examples/panel/byte/MOT20-02.txt)

Stores an example of per-frame ByteTrack tracking outputs for MOT20-02.

- Ten-column MOTChallenge result per row: frame,id,x,y,w,h,conf,a,b,c
- One-based frame numbers and one-based top-left coordinates
- Within-frame output row order preserved for deterministic identity matching

**Inputs:** Static existing tracker outputs; tracking execution: none

**Outputs:** Text input read by score_tracker.py or the track parser

**Usage:** Inspect the format to see how ByteTrack connects to the standard scoring interface; this file is for MOT20-02.

**Caution:** Requires: original within-frame row order. This guide checked only the first row column count; numerical track analysis is outside its scope.

**Current SHA256:** `70825f995d3da644fe85c5d9fea562781a7cd637084f32759b909ccfbd75889c`

## core/examples/panel/oc/MOT20-01.txt

[Open file](../repository/core/examples/panel/oc/MOT20-01.txt)

Stores an example of per-frame OC-SORT tracking outputs for MOT20-01.

- Ten-column MOTChallenge result per row: frame,id,x,y,w,h,conf,a,b,c
- One-based frame numbers and one-based top-left coordinates
- Within-frame output row order preserved for deterministic identity matching

**Inputs:** Static existing tracker outputs; tracking execution: none

**Outputs:** Text input read by score_tracker.py or the track parser

**Usage:** Inspect the format to see how OC-SORT connects to the standard scoring interface; this file is for MOT20-01.

**Caution:** Requires: original within-frame row order. This guide checked only the first row column count; numerical track analysis is outside its scope.

**Current SHA256:** `278445fb7e8f057eed59e218fc168c8cb32cd13488fce063b1e26fd105c25d3c`

## core/examples/panel/oc/MOT20-02.txt

[Open file](../repository/core/examples/panel/oc/MOT20-02.txt)

Stores an example of per-frame OC-SORT tracking outputs for MOT20-02.

- Ten-column MOTChallenge result per row: frame,id,x,y,w,h,conf,a,b,c
- One-based frame numbers and one-based top-left coordinates
- Within-frame output row order preserved for deterministic identity matching

**Inputs:** Static existing tracker outputs; tracking execution: none

**Outputs:** Text input read by score_tracker.py or the track parser

**Usage:** Inspect the format to see how OC-SORT connects to the standard scoring interface; this file is for MOT20-02.

**Caution:** Requires: original within-frame row order. This guide checked only the first row column count; numerical track analysis is outside its scope.

**Current SHA256:** `6736ef5a6e659fbcaeca032ec55ab4e4fcda6aa3cafba65dcbaceb4f687aace8`

## core/examples/panel/source_manifest.json

[Open file](../repository/core/examples/panel/source_manifest.json)

Describes how saved outputs from the three panel trackers were converted into standard text.

- Methods and source-file records for byte, oc, and bot
- Row conversion conventions for frame,id,x,y,w,h and other fields
- Statements preserving emitted row order and unfiltered, uninterpolated outputs, with M4 outside the conversion scope

**Inputs:** Data access: none

**Outputs:** Provenance and conversion notes for panel track text

**Usage:** Confirm the tracker identity, input provenance, and coordinate conversion before consulting the corresponding text file.

**Caution:** Scope: project runs of the authors' code on existing detections. Official author-released result files have separate provenance.

**Current SHA256:** `031863474b3cc1a387a1a9ce1110c7d59548f6c46290974680e8410250b51e06`

## core/examples/yolox_v11/cache_manifest.json

[Open file](../repository/core/examples/yolox_v11/cache_manifest.json)

Lists the sequences, frame files, per-gate events, and expected-result bindings for the v11 cache.

- 01/02 metadata and fingerprints for frames and per-gate events files
- Paths, sizes, and SHA256 values for expected scoring references
- Frame and box coordinate conventions, with identity decisions reconstructed outside the cache

**Inputs:** Data access: none; score.score reads this manifest

**Outputs:** Index used by the scorer to locate the cache and verify integrity

**Usage:** Consult to see exactly which bundled files v11 reproduction reads.

**Caution:** Scope: existing output caches. A fresh model or tracker run requires a separate execution record.

**Current SHA256:** `5a9a8f3bec7af9d9ad94fb08e8e48eb927e7b1c7c2ce97020c5cd67e20f7134b`

## core/examples/yolox_v11/MOT20-01/gates/H_30/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-01/gates/H_30/events.json)

Stores cached final v11 events for the H_30 horizontal virtual gate in MOT20-01.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-01/H_30; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `c7c780cf79a8a581e2ce58c1aeec10eb9a2d08d1b9d06a35ccf292f686303dae`

## core/examples/yolox_v11/MOT20-01/gates/H_50/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-01/gates/H_50/events.json)

Stores cached final v11 events for the H_50 horizontal virtual gate in MOT20-01.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-01/H_50; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `bae5f3da696b1a0f74d55264367e3cb1f40de458972ae2b36a093e54ef4b17bb`

## core/examples/yolox_v11/MOT20-01/gates/H_70/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-01/gates/H_70/events.json)

Stores cached final v11 events for the H_70 horizontal virtual gate in MOT20-01.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-01/H_70; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `12beebfff44d19e3a85bb921f879d94ad394bf6ba86d930b3946dd29148fe73c`

## core/examples/yolox_v11/MOT20-01/gates/V_25/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-01/gates/V_25/events.json)

Stores cached final v11 events for the V_25 vertical virtual gate in MOT20-01.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-01/V_25; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `2c59a6d14c76d6ccf196a33eb3b274a4f77a55c87ae042fae26fff5b7284931e`

## core/examples/yolox_v11/MOT20-01/gates/V_50/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-01/gates/V_50/events.json)

Stores cached final v11 events for the V_50 vertical virtual gate in MOT20-01.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-01/V_50; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `6fed866ddf3e7b88ce9f57c08061852fd995ab51c5d9c7e9791c39540ee9083d`

## core/examples/yolox_v11/MOT20-01/gates/V_75/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-01/gates/V_75/events.json)

Stores cached final v11 events for the V_75 vertical virtual gate in MOT20-01.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-01/V_75; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `a2bd1b362215807928693f0c63478a1151699565a0d7749bb4c30b6daa01f6e6`

## core/examples/yolox_v11/MOT20-01/output_boxes.jsonl.gz

[Open file](../repository/core/examples/yolox_v11/MOT20-01/output_boxes.jsonl.gz)

Stores cached track boxes actually emitted by v11 for MOT20-01.

- One frame per line: frame, source_frame, time_s, outputs
- Each output contains raw_detection_index, track_id, box, and original_track_id
- Original detection indices retained for deterministic identity association

**Inputs:** Static v11 output cache; detection/tracking execution: none

**Outputs:** Input used by score.score to reconstruct per-frame identity associations

**Usage:** Read alongside scoring.schema.json to inspect the v11 reproduction input format for MOT20-01.

**Caution:** Scope: actual tracker output boxes. original_track_id records track provenance before processing; GT identity is determined separately. This guide checked only the first row fields.

**Current SHA256:** `02ff17065f07f2facce5381dcd74d293756fe5238460c511ddd08334e9318362`

## core/examples/yolox_v11/MOT20-02/gates/H_30/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-02/gates/H_30/events.json)

Stores cached final v11 events for the H_30 horizontal virtual gate in MOT20-02.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-02/H_30; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `2a4198b9f5e0bd8e03430027301e6c0a96bdbeeea05b78d19e3e5521b52a8fa8`

## core/examples/yolox_v11/MOT20-02/gates/H_50/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-02/gates/H_50/events.json)

Stores cached final v11 events for the H_50 horizontal virtual gate in MOT20-02.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-02/H_50; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `8d27284a0c2f0c13442ab846175768f77ef6d3759fbde4729c99574791020fb6`

## core/examples/yolox_v11/MOT20-02/gates/H_70/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-02/gates/H_70/events.json)

Stores cached final v11 events for the H_70 horizontal virtual gate in MOT20-02.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-02/H_70; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `521cb3d123149d21d52fa30ccd2608b041dd1e7dad03cc588792854ed1b33626`

## core/examples/yolox_v11/MOT20-02/gates/V_25/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-02/gates/V_25/events.json)

Stores cached final v11 events for the V_25 vertical virtual gate in MOT20-02.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-02/V_25; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `ae41a91c36a924888b9370c9444fe83d367e62b9cdd316f75a81e0739cbc0d4b`

## core/examples/yolox_v11/MOT20-02/gates/V_50/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-02/gates/V_50/events.json)

Stores cached final v11 events for the V_50 vertical virtual gate in MOT20-02.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-02/V_50; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `732dd046d4c279aaca55a7e11800d7b160d89c5bd44dacb9b538e698ca188e21`

## core/examples/yolox_v11/MOT20-02/gates/V_75/events.json

[Open file](../repository/core/examples/yolox_v11/MOT20-02/gates/V_75/events.json)

Stores cached final v11 events for the V_75 vertical virtual gate in MOT20-02.

- sequence, gate_id, and metadata bind the sequence and gate
- final_events stores direction, first target-region frame/time, position, and track/event IDs
- Nonempty events retain deduplication groups, member IDs, and member-event provenance

**Inputs:** Static cache of final events already decoded

**Outputs:** Event input used by score.score to recompute identity decisions and matching

**Usage:** Read to locate the v11 event input for MOT20-02/V_75; gate geometry is in labels/geometry.json.

**Caution:** Scope: final decoded events with identity decisions recomputed later. Complete C1/R1/R2 diagnostics are outside this cache; empty arrays are valid. This guide checked only the fields.

**Current SHA256:** `d103fc141a61bf5fcca45161520461466da2de402cfa85f2ec8e346dd07a1e86`

## core/examples/yolox_v11/MOT20-02/output_boxes.jsonl.gz

[Open file](../repository/core/examples/yolox_v11/MOT20-02/output_boxes.jsonl.gz)

Stores cached track boxes actually emitted by v11 for MOT20-02.

- One frame per line: frame, source_frame, time_s, outputs
- Each output contains raw_detection_index, track_id, box, and original_track_id
- Original detection indices retained for deterministic identity association

**Inputs:** Static v11 output cache; detection/tracking execution: none

**Outputs:** Input used by score.score to reconstruct per-frame identity associations

**Usage:** Read alongside scoring.schema.json to inspect the v11 reproduction input format for MOT20-02.

**Caution:** Scope: actual tracker output boxes. original_track_id records track provenance before processing; GT identity is determined separately. This guide checked only the first row fields.

**Current SHA256:** `5d5b85bcea1aa18c2bc46c29a487ff327a41f600062743748b3386fcde7cb6e4`

## core/examples/yolox_v11/SCORING_INTERFACE.md

[Open file](../repository/core/examples/yolox_v11/SCORING_INTERFACE.md)

Explains what the bundled reduced v11 cache retains and which stages it can reproduce.

- Retained/omitted table for output boxes, final events, GT, labels, and expected values
- Identity and event scoring rules
- Meaning of globally optimal matching ranges and the anonymous view

**Inputs:** Data access: none

**Outputs:** Documentation of the cache interface and interpretive limits

**Usage:** Read before the v11 example, especially to distinguish identity reconstruction from rerunning the full pipeline.

**Caution:** Scope: reconstruction from retained outputs. Original detection, tracking, M4, and complete C1/R1/R2 decoding require materials beyond this reduced cache.

**Current SHA256:** `3ea6e7bc6bbe1b627334de1df28d13a4c71bfd00995df02b9247aeffc132ff97`

## core/examples/yolox_v11/source_manifest.json

[Open file](../repository/core/examples/yolox_v11/source_manifest.json)

Records the historical provenance and field allowlist of the reduced v11 cache.

- Source names, lengths, and SHA256 values of the originally saved files
- Retained fields for frames, output boxes, events, and member events
- Removed fields and the resulting limitations

**Inputs:** Data access: none

**Outputs:** Provenance and field notes for cache purification/export

**Usage:** Consult to check whether identity answers were carried into the cache or to learn which diagnostic fields were omitted.

**Caution:** Scope: source names provide traceability; current reproduction uses the bundled cache.

**Current SHA256:** `7fdef248e9202b9c7c79500cb97bf3fb8cffe39d7b1c0c8ed4cc509e9e4be5f9`

## core/expected/panel_bot.json

[Open file](../repository/core/expected/panel_bot.json)

Stores historical expected CPU self-test results for BoT-SORT on 01/02.

- Primary, per-sequence, and per-gate result structures
- Per-gate candidate/confirmed/final event summaries and final-event lists
- Provenance bindings, comparison policy, and position tolerance

**Inputs:** Static regression reference read by score_tracker.py --self-test

**Outputs:** Expected dictionary compared by regression.compare

**Usage:** Read alongside src/regression.py to understand what the bot self-test compares.

**Caution:** Scope: software regression expectations. Human verification is a separate evidence source. This guide checked only the structure.

**Current SHA256:** `2fb92ddfaaa8e0c168452881b4004b6bcd01c4d403e22e0e62903c4fa6571bf3`

## core/expected/panel_byte.json

[Open file](../repository/core/expected/panel_byte.json)

Stores historical expected CPU self-test results for ByteTrack on 01/02.

- Primary, per-sequence, and per-gate result structures
- Per-gate candidate/confirmed/final event summaries and final-event lists
- Provenance bindings, comparison policy, and position tolerance

**Inputs:** Static regression reference read by score_tracker.py --self-test

**Outputs:** Expected dictionary compared by regression.compare

**Usage:** Read alongside src/regression.py to understand what the byte self-test compares.

**Caution:** Scope: software regression expectations. Human verification is a separate evidence source. This guide checked only the structure.

**Current SHA256:** `1e55b3316671c0967bae9334e69c4d79b647c36470475d1fd131b17a21f8178f`

## core/expected/panel_oc.json

[Open file](../repository/core/expected/panel_oc.json)

Stores historical expected CPU self-test results for OC-SORT on 01/02.

- Primary, per-sequence, and per-gate result structures
- Per-gate candidate/confirmed/final event summaries and final-event lists
- Provenance bindings, comparison policy, and position tolerance

**Inputs:** Static regression reference read by score_tracker.py --self-test

**Outputs:** Expected dictionary compared by regression.compare

**Usage:** Read alongside src/regression.py to understand what the oc self-test compares.

**Caution:** Scope: software regression expectations. Human verification is a separate evidence source. This guide checked only the structure.

**Current SHA256:** `317c0c1cef99c37dd4a17c2d16b50ef291d4e11a06302dbe2219ef471acd7ee5`

## core/expected/yolox_v11_main.json

[Open file](../repository/core/expected/yolox_v11_main.json)

Stores the historical primary scoring reference that v11 cache reproduction must match.

- Overall and per-sequence summaries in main
- Per-gate results in units
- Source files, applicability, and a flag identifying the reference as numerical regression evidence

**Inputs:** Static expected values referenced by cache_manifest.expected

**Outputs:** Reference used by score.score to check agreement with historical results

**Usage:** Inspect the structure to understand the scope of reproduce.py parity comparisons.

**Caution:** Scope: explicitly labeled numerical expectations. Identity decisions are reconstructed from the retained inputs; new matching ranges are additional outputs beyond historical numerical parity.

**Current SHA256:** `850a1a12e0fa8caafc1bcf8dcb9c77703aaafd4ea644ee4e53620f536e2cdd11`

## core/inspect_event.py

[Open file](../repository/core/inspect_event.py)

Rebuilds development labels and displays one event, first rescoring the input tracks when needed.

- --event-id and --list-misses modes
- Sealing of new scoring evidence and Inspector invocation
- Optional rendering and preservation of the original exception and read ledger

**Inputs:** 01/02 GT and seqinfo; optional tracks and images for the selected sequence

**Outputs:** event.json or misses.jsonl, read ledger, and receipt; optional PNG files and a tracker scoring directory

**Usage:** Consult this entry point when reusable scoring evidence is unavailable and new evidence is needed.

**Caution:** Execution: --tracks invokes scoring. For existing sealed results, use inspect_saved_event.py.

**Current SHA256:** `843a4229b0aa80867d3dd8fc648f2c8e9c58ebbbafb26031b616beb45791308c`

## core/inspect_saved_event.py

[Open file](../repository/core/inspect_saved_event.py)

Inspects existing scoring evidence using an externally retained SHA256, without rescoring.

- Explicit --score-dir and --evidence-sha256
- Single-event inspection, miss filtering, and optional rendering
- Separate inspection_receipt.json and failure records

**Inputs:** 01/02 GT, original tracks, a sealed scoring directory, and its retained SHA256; optional images

**Outputs:** New event.json or misses.jsonl, read ledger, and inspection_receipt.json

**Usage:** Prefer this entry point to recheck an event or a list of misses from an existing trusted sealed run.

**Caution:** Requires: the original, separately retained fingerprint and a new output location separate from the package and scoring directories. Reuse covers already sealed evidence.

**Current SHA256:** `2eabf2217ba9a0bd81f59d66c0e7c5f2890155fc3d92a6ff615218a11a15fb0c`

## core/labels/build_run.json

[Open file](../repository/core/labels/build_run.json)

Records the duration and scope of the original label build.

- cpu_s and elapsed_s
- no_inference, no_tracking, no_scoring, and no_human_verification flags

**Inputs:** Data access: none

**Outputs:** Brief receipt for the historical build

**Usage:** Read to distinguish label generation from model inference, tracking runs, or human review.

**Caution:** Scope: the original build's execution record and timing.

**Current SHA256:** `a91110769cb3a9f5ad8882c2a81f49b572d669d1dac9b669be1d95bc25bdbb7f`

## core/labels/geometry.json

[Open file](../repository/core/labels/geometry.json)

Stores frozen pixel geometry for the virtual gates and regions on both sides in 01/02.

- Gate orientation, relative position, line coordinates, and segment extents
- tunnel/plaza polygons and gate-facing edges
- Midpoint body height, gap width, region depth, and geometry check fields

**Inputs:** Static derived configuration produced by frozen_labels_census.make_lines

**Outputs:** Geometry parameters shared by labels, the event chain, and rendering

**Usage:** Read to see which spatial regions gate names such as H_30 and V_50 denote.

**Caution:** Scope: image-pixel geometry. Requires matching sequence and gate keys; metric ground-plane calibration is outside this representation.

**Current SHA256:** `91e7c0fed4e061af4804556fc07b07db7cf24403daca144867fd7ec1b1254270`

## core/labels/height_models.json

[Open file](../repository/core/labels/height_models.json)

Stores the frozen G1 body-height relationships fitted to the two development sequences.

- coefficients and coefficient_order
- Fitting coordinate ranges, original image dimensions, and parameter formulas
- Metadata on fitting rank, precision, and NumPy version

**Inputs:** Static derived parameters produced by frozen_labels_census.fit_model

**Outputs:** Body-height models used for gate geometry and system-event confirmation

**Usage:** Read alongside adapter and chain to understand how event depth is expressed in body-height units.

**Caution:** Scope: derived body-height parameters. Preserve their precision, values, and explicitly recorded fitting range.

**Current SHA256:** `c98f3d9899c84c9e48c8159b7f0ca08d9ce2ffe9c6f72ebf5012ab86ef72002f`

## core/labels/lineage_enrichment.jsonl.gz

[Open file](../repository/core/labels/lineage_enrichment.jsonl.gz)

Stores separate supplementary provenance and along-gate projection information for each reference event.

- Source, target, and confirmation GT line numbers keyed by event_id
- Observation-support frame/time intervals and missing, invalid, and gap counts
- Along-gate projection and explicit flags marking physical intersections as unestimated

**Inputs:** Static supplementary table produced by lineage.enrich_labels from derived events and geometry

**Outputs:** Line-delimited JSON for locating supporting observations

**Usage:** Read the field dictionary and locate the corresponding row when explaining which observations support an event.

**Caution:** Scope: supplementary provenance; original scientific fields remain fixed. Positions represent projections along the gate. This guide checked only the first row's fields.

**Current SHA256:** `2a7674d9a6e445e56ba2563d259b75fdefc8b775e279a22b5d1eb77657036ab1`

## core/labels/read_ledger.jsonl

[Open file](../repository/core/labels/read_ledger.jsonl)

Records the development source files actually read during label construction and their fingerprints.

- Sequence, input kind, and reading purpose
- Byte counts and SHA256 values

**Inputs:** Static build ledger; data access: none

**Outputs:** Traceability record for the original label-build inputs

**Usage:** Consult to verify the GT/seqinfo provenance of a label build.

**Caution:** Scope: reads from the historical label build. This guide inspected only the record fields.

**Current SHA256:** `78b496bea6af6c1b3b4143e8ef27a1a04cbd6888c2f7967c4de20ac8358b4f0c`

## core/labels/reference_line_map.jsonl

[Open file](../repository/core/labels/reference_line_map.jsonl)

Maps event row numbers in the current package to logical row numbers in the historical reference file.

- event_id
- local_jsonl_logical_line and reference_jsonl_logical_line

**Inputs:** Static provenance mapping; performs no computation

**Outputs:** Mapping from local row numbers to historical logical row numbers

**Usage:** Look up an event ID when row numbers in the filtered file differ from historical references.

**Caution:** Scope: JSONL logical row numbers used for provenance. Original gt.txt physical line numbers and scientific-value comparisons are separate.

**Current SHA256:** `606d13add20e8813ae945981a7401d8418770173e60462af7e807391670f4eea`

## core/labels/source_manifest.json

[Open file](../repository/core/labels/source_manifest.json)

Summarizes source-input bindings and frozen-function provenance for the derived labels.

- Sequences, types, and fingerprints of GT/seqinfo inputs
- File and function provenance in scientific_source_files
- Scope statements covering derived labels, with full GT and media outside the copied/read materials

**Inputs:** Data access: none

**Outputs:** Label provenance manifest

**Usage:** Consult to trace labels to the functions and development-input versions that produced them.

**Caution:** Scope: source paths identify provenance. The manifest describes the inputs and functions used to derive labels.

**Current SHA256:** `164479909c9c0dc600d09868f50554918030273bf0e5cc5928cf891f2f2ef8d1`

## core/labels/summary.json

[Open file](../repository/core/labels/summary.json)

Stores sequence metadata and overall, historical-window, and per-gate summaries from label construction.

- metadata, windows, and lines for the two development sequences
- Overall completion flag and metadata on derivation semantics
- Dependency versions, license, and QC fields from original generation

**Inputs:** Static label-build summary produced by labels.build_labels

**Outputs:** Sequence dimensions, lengths, and summaries used by the scorer and Inspector

**Usage:** Read for an initial understanding of label-file organization and sequence metadata.

**Caution:** Scope: historical-window summaries and full-sequence primary scoring have distinct definitions. QC fields reflect the original generation snapshot; this guide inspected existing statistics.

**Current SHA256:** `fbe3c73302d7bbf6e08f70ed4a4504d3d4ca71c5a242aed561a9b98417073695`

## core/labels/transitions.jsonl.gz

[Open file](../repository/core/labels/transitions.jsonl.gz)

Stores complete region-transition records derived from the reference annotations for 01/02.

- Event ID, gate, direction, track ID, and first target-region observation time
- confirmed, confirmation, and frozen_transition support information
- Visibility attributes, source frames/GT line numbers, and audit fields

**Inputs:** Static derived data produced by labels.build_labels

**Outputs:** Line-delimited JSON read for reconstruction parity checks, scoring, and event inspection

**Usage:** Read the schema first to understand a reference event, then locate it by an explicit event ID.

**Caution:** Scope: confirmation follows the frozen rules, and event time denotes the first target-region observation. Human review and exact physical crossing time are separate questions. This guide checked only the first row's fields.

**Current SHA256:** `62fe5e800278b5bb98194bd66de64c5b9d68f7924085e66199f5aa624f2467c7`

## core/LICENSE_CODE

[Open file](../repository/core/LICENSE_CODE)

Provides the MIT license for the project's original code and copies of frozen pure functions.

- MIT permission, attribution-retention requirement, and disclaimer
- Scope explicitly excluding derived data, weights, and third-party dependencies

**Inputs:** Data access: none

**Outputs:** Code license text

**Usage:** Read before copying or modifying original code in the package.

**Caution:** Scope: original code and frozen pure-function copies. Data examples and upstream software retain their own licenses.

**Current SHA256:** `555b127532b4bb7d1a4717b87001d68bc5584750a395d6a0a949d94ace512615`

## core/MANIFEST.json

[Open file](../repository/core/MANIFEST.json)

Pins the entire core package to a verifiable version using file paths, lengths, and SHA256 values.

- Per-file path, bytes, and sha256
- Development sequences, version, and source-package binding
- Records of anonymous-copy, presentation-layer, and documentation changes

**Inputs:** Data access: none; verify_package reads this table and bundled files

**Outputs:** Basis for whole-package integrity verification

**Usage:** Consult to confirm package membership or understand why an entry point rejects extra files.

**Caution:** Scope: release_status and similar fields reflect manifest-generation time. Integrity coverage comprises the listed package files; the manifest itself is outside its recursive hash coverage.

**Current SHA256:** `5ed3695735246dff4e0e6a3831c422bda16648b50ada7d1ed346f58a9f4ee87e`

## core/PROTOCOL.md

[Open file](../repository/core/PROTOCOL.md)

Stores the interface rules and regression acceptance criteria fixed before v0.1 implementation began.

- Ten-column MOTChallenge input, coordinate conversion, and row-order conventions
- Frozen event chain, identity scoring, and regression criteria R1-R5
- Development-sequence boundaries and claim scope

**Inputs:** Data access: none

**Outputs:** Protocol text for implementation and result comparison

**Usage:** Read to understand why a threshold or comparison criterion is fixed.

**Caution:** Scope: the historically frozen protocol. Regression comparisons require preserving its original criteria.

**Current SHA256:** `e46ebc5dc9a1df92a2ee0485aab596c7f8052bb981dd38ee6dca0e26e7277036`

## core/PROTOCOL.md.sha256

[Open file](../repository/core/PROTOCOL.md.sha256)

Records the SHA256 fingerprint of the fixed PROTOCOL.md version.

- One SHA256 text record
- Corresponding target name PROTOCOL.md

**Inputs:** Data access: none

**Outputs:** Verification reference for the protocol version

**Usage:** Consult to check whether the protocol text still matches the original frozen version.

**Caution:** Scope: byte equality of the protocol version. Scientific correctness requires separate evidence.

**Current SHA256:** `7079bd7f096ef621967ba2a125af8282e68854a70833b627edf2fcc7b955b74d`

## core/README.md

[Open file](../repository/core/README.md)

Introduces the development sample's capabilities and entry points for reproduction, scoring, and event inspection.

- Single-command reproduction and MOTChallenge track-scoring instructions
- Explanations of coordinates, time, visibility strata, and identity matching
- Event details, miss lists, and optional rendering

**Inputs:** Data access: none

**Outputs:** Operating instructions and explanations of result meaning

**Usage:** Read first when entering core/, then choose an entry point for the task.

**Caution:** Scope: versions and release-readiness statements reflect the packaging snapshot. Consult the overall guide for current review conclusions.

**Current SHA256:** `d668324e1b0d3e312e5c872836f8441b93c659d105526eb11998603ebe505241`

## core/REPORT_v0_1.md

[Open file](../repository/core/REPORT_v0_1.md)

Records v0.1 interface construction, provenance checks, and regression validation at that time.

- Added files and function provenance
- Historical precheck and regression results
- Attempt log, commands, and applicability limits

**Inputs:** Data access: none

**Outputs:** Historical build and validation report

**Usage:** Read to trace how v0.1 was built and which comparisons were performed.

**Caution:** Scope: existing runs recorded in this report. This guide explains that evidence within its original environment and data scope.

**Current SHA256:** `d24ad98360f25bf8025ed4d490e354e50837dc1791baa9ffe95030217bcbc24a`

## core/reproduce.py

[Open file](../repository/core/reproduce.py)

Rebuilds labels from user-supplied development GT, then recomputes scores for the bundled v11 cache.

- Whole-package hash, input-path, and resource-budget checks
- Reconstruction and content-parity checks for labels and the supplementary provenance table
- Cache scoring and success/failure receipts

**Inputs:** Explicit MOT20-01/02 GT and seqinfo; bundled labels, v11 examples, expected values, and frozen code

**Outputs:** labels, scores, label_parity.json, and run receipts in a new directory

**Usage:** Use to rebuild labels and reproduce the bundled v11 cache; this guide only explains the code.

**Caution:** Execution: rebuilds labels and computes scores. Requires a new output directory outside the package.

**Current SHA256:** `66ba70732dc072a2336286122eec5b1da06aeb113f1e993589d49fc2b500af40`

## core/requirements-inspection.txt

[Open file](../repository/core/requirements-inspection.txt)

Adds the Pillow version required for optional image rendering and the full synthetic checks.

- Reference to requirements.txt
- Pillow==11.3.0

**Inputs:** Data access: none

**Outputs:** Rendering dependency declaration

**Usage:** Read when render_event or synthetic image checks are needed.

**Caution:** Scope: dependency declarations. Installation is an external preparation step.

**Current SHA256:** `6d3d71589b7c2236418b8a61863664c561446ea33d308ee98beb7aad1f37bdb6`

## core/requirements.txt

[Open file](../repository/core/requirements.txt)

Pins the NumPy version for core CPU reproduction.

- numpy==2.2.6
- Comments on the reference CPython version and external installation

**Inputs:** Data access: none

**Outputs:** Dependency version declaration

**Usage:** Read when preparing the same runtime environment or investigating numerical-environment differences.

**Caution:** Scope: dependency declarations. Installation is an external preparation step.

**Current SHA256:** `583b58fe9c8bfa70ace81d92aa3af6e952f49fee42bad1cf884e4a27f2f1f93c`

## core/schemas/labels_lineage_fields.json

[Open file](../repository/core/schemas/labels_lineage_fields.json)

Explains projection-position, support-interval, and missing-frame fields in the supplementary provenance table.

- Unclipped projection definition of gate_position_u
- Physical intersection marked as unestimated and source-annotation interpolation as unknown
- Distinction between observed endpoints, missing frames, and invalid points

**Inputs:** Data access: none

**Outputs:** Field dictionary for lineage_enrichment

**Usage:** Read alongside labels/lineage_enrichment.jsonl.gz when tracing provenance.

**Caution:** Scope: observed support intervals. Statistical uncertainty and any interpolation in the original annotations require separate information.

**Current SHA256:** `5962e41746c98a0808376b65aa8c389ffbe3dba64eebd8120ecae6dcb5f8f43a`

## core/schemas/labels_schema.json

[Open file](../repository/core/schemas/labels_schema.json)

Explains key fields and coordinate/time semantics in the complete reference-transition file.

- Stable event IDs and local logical row numbers
- Confirmation, source line numbers, observation time, and interpolation notes
- Development-sequence scope and original limitation wording

**Inputs:** Data access: none

**Outputs:** Dictionary of label-field descriptions

**Usage:** Read first to understand transitions.jsonl.gz fields.

**Caution:** Scope: field semantics and the QC state at file creation. Current review records provide the latest assessment.

**Current SHA256:** `6580093639ce8c66ccd232172db1461bbdf8ac9b2a4e4404d71aac624f9f034a`

## core/schemas/scoring.schema.json

[Open file](../repository/core/schemas/scoring.schema.json)

Uses JSON Schema to describe input/output structures for the v11 numerical cache and scoring results.

- Definitions of binding, outputBox, frame, and finalEventRequired
- Optimal-matching-range structure
- Required scoring-report fields and fixed scope

**Inputs:** Data access: none

**Outputs:** Machine-readable structural definitions and semantic comments

**Usage:** Read when developing a parser or learning output-box and final-event fields.

**Caution:** Scope: structure and semantic comments. Runtime validation also checks hashes, ordering, and semantics; the Schema URL serves as an identifier.

**Current SHA256:** `3563f5791a5f0e44e1dd43835020a1a4df426b45d163856f3c4c8da399364cf3`

## core/score_tracker.py

[Open file](../repository/core/score_tracker.py)

Provides a command-line scoring entry point for user MOTChallenge tracks or the three bundled tracker examples.

- Mutually exclusive --tracks and --self-test
- Label reconstruction followed by the frozen event chain and scoring
- Per-tracker regression comparisons, tables, and receipts

**Inputs:** 01/02 GT, seqinfo, and two track text files; self-test mode reads panel and expected

**Outputs:** labels, per-tracker scoring results, and complete.json in a new directory

**Usage:** Consult this entry point to connect existing tracker outputs to the sample.

**Caution:** Execution: rescoring with output-box bottom-center event points. Row order participates in deterministic tie-breaking. Requires Python assertions to remain enabled; python -O disables them.

**Current SHA256:** `65a344605e01d4fb6d6c1ec3ad1feaa3e822e8813a9b41cb1a3719110f3ab259`

## core/src/__init__.py

[Open file](../repository/core/src/__init__.py)

Marks src as a Python package with import behavior limited to package initialization.

- Development-sample package docstring only
- Package marker with data reads and computation handled by other modules

**Inputs:** Data access: none

**Outputs:** Runtime outputs: none

**Usage:** Consult to understand the src package boundary.

**Caution:** Scope: Python package initialization.

**Current SHA256:** `0f5f1b2edd3795fef8a344716973e3513b6f8177f63bade5ce940588834093a3`

## core/src/audit_integrity.py

[Open file](../repository/core/src/audit_integrity.py)

Checks that saved per-frame identity audits are complete and correspond row by row to the original track outputs.

- Checks for missing frames, duplicate frames, row order, and counts
- Consistency checks for boxes, track IDs, statuses, and threshold fields
- Structural correspondence between assignments and identity observations

**Inputs:** Parsed audit records, track-frame mapping, and sequence length; data access: none

**Outputs:** Integrity summary or FrameIdentityIntegrityError

**Usage:** Read to distinguish genuinely empty frames from missing evidence.

**Caution:** Scope: structural audit integrity using saved assignments. Requires hash binding at the higher layer.

**Current SHA256:** `77bd4b52ccf47975b8b58149e52f5f7359139267c55fe10f56742856ada4dcdc`

## core/src/events.py

[Open file](../repository/core/src/events.py)

Adapts track boxes into observations for the frozen event chain and invokes it for each gate.

- Verification of frozen-function provenance manifests and module bindings
- Conversion from boxes to points and event observations
- Single-gate execution and compact final-event summaries

**Inputs:** Package path, verified-read callback, parsed track boxes, geometry, and body-height models

**Outputs:** Frozen API, observation lists, per-gate events, and final-event summaries

**Usage:** Read when following tracker_score.score_tracks to see how events are generated from output boxes.

**Caution:** Scope: orchestration of frozen rules through the standard box-bottom-center input.

**Current SHA256:** `4f8830e0ea5cc86aca42b965c40146ccd018228b7804ee53aada1009bd773e93`

## core/src/evidence_seal.py

[Open file](../repository/core/src/evidence_seal.py)

Seals the contents of the six inspector evidence files from new scoring runs and verifies existing seals.

- Six fixed evidence members and path checks
- File-size, SHA256, and package-manifest bindings
- Loading checks anchored by an externally retained fingerprint

**Inputs:** Newly completed scoring directory or existing evidence directory, package-manifest fingerprint, and retained evidence fingerprint

**Outputs:** inspection_evidence_manifest.json or a verified binding map

**Usage:** Read to understand why saved-result inspection requires the original SHA256 or why changed files cause errors.

**Caution:** Scope: content integrity of the six listed evidence members, anchored to the retained original seal. Algorithm correctness requires separate evidence; an existing seal must be preserved.

**Current SHA256:** `76a8cacee13de7b22e156323ed4f973466247ad395aab43331744c97bc494b4d`

## core/src/frozen_events/__init__.py

[Open file](../repository/core/src/frozen_events/__init__.py)

Declares the frozen event-function directory as a Python subpackage.

- Module description of frozen pure functions only
- Import-time data input/output: none

**Inputs:** Data access: none

**Outputs:** Runtime outputs: none

**Usage:** Consult to understand the frozen_events package structure.

**Caution:** Scope: Python subpackage initialization; execution is through the calling entry points.

**Current SHA256:** `584d4674fb941352ac8841b8d323ce6de65531dc1b01663234b29e5ad5afa9fe`

## core/src/frozen_events/adapter.py

[Open file](../repository/core/src/frozen_events/adapter.py)

Processes one gate over a complete sequence with the frozen extraction, confirmation, and deduplication functions.

- Wrapping of an externally fitted G1 body-height model
- Normalization of frame clocks, regions, and observations
- Generation of candidates, C1 evidence, R1+R2 groups, and final events

**Inputs:** Full-sequence observations, sequence metadata, external model, and polygons on both sides

**Outputs:** Complete single-gate event records and function-provenance audit

**Usage:** Read to understand the overall invocation order of the frozen event chain.

**Caution:** Requires: the supplied fitted model and explicit range, complete sequence scope, and the frozen handling of boundaries and missing points.

**Current SHA256:** `1290edbd86a16ff88a8e8d7d5481dee816ef261809be84debae758db4ab637bc`

## core/src/frozen_events/chain.py

[Open file](../repository/core/src/frozen_events/chain.py)

Collects frozen scientific functions for transition extraction, confirmation, and duplicate-event handling.

- Polygon distances and per-track transition extraction
- Target-region depth evidence and G1 body-height conversion
- R1 merging, R2 directional evidence, and other retained variants
- Keypoint and hybrid-reference-point selection functions

**Inputs:** In-memory observations, events, geometry, models, and fixed configuration

**Outputs:** Transitions, confirmation details, event groups, and reasons for retention or removal

**Usage:** Follow calls from adapter to investigate why a final event was merged or retained.

**Caution:** Scope: the current adapter enables R1+R2. Consult its calls to determine which retained variants and point-selection functions are active.

**Current SHA256:** `0e0bfb5f3fe68b49dd6ceea8af2923aef8b143cf65bb34f316d78af04173b7e8`

## core/src/frozen_events/event_view.py

[Open file](../repository/core/src/frozen_events/event_view.py)

Adds standardized frame-number and time fields to one output observation.

- Copy of the original output dictionary
- Removal of raw_detection_index when its value is null
- Assignment of zero-based frame, one-based source_frame, and time_s

**Inputs:** One in-memory output record and a zero-based frame number

**Outputs:** Observation dictionary used by the event chain

**Usage:** Read to check how tracker output connects to the event chain.

**Caution:** Scope: the frozen 25 fps time definition.

**Current SHA256:** `05a4e9a7e77d65f0d7e1f1c436cda091db77f685e9edfc42f50781cc1d024947`

## core/src/frozen_events/point.py

[Open file](../repository/core/src/frozen_events/point.py)

Obtains a box-bottom-center point under the frozen boundary rules.

- Box-bottom-center calculation
- Finite-value and image-boundary checks
- Point, invalidity reason, and out-of-bounds flag

**Inputs:** In-memory xyxy box and image width/height

**Outputs:** Valid point or None, with explanatory flags

**Usage:** Read to check why an output box cannot produce an event point.

**Caution:** Scope: boundary-invalid points are excluded from event extraction; their boxes may still participate in identity association.

**Current SHA256:** `21f4a33f76ac0975c6d6b65efa2552b362befb6ec0e259a592f9417ac3d64813`

## core/src/frozen_events/provenance.json

[Open file](../repository/core/src/frozen_events/provenance.json)

Records source fingerprints for each file and copied member in the frozen event chain.

- Paths, lengths, and SHA256 values for source and bundled output files
- Member line numbers, source snippets, and AST fingerprints
- Correspondence between the original loading namespace and panel function audits

**Inputs:** Data access: none

**Outputs:** Provenance and integrity evidence for frozen event code

**Usage:** Consult to verify origin in the frozen implementation; consumed by events.load_api.

**Caution:** Scope: historical paths identify provenance. events.load_api consumes the bundled implementation and bindings.

**Current SHA256:** `457d7854ee6f151b1cc073396de38db6261d69581d363a9ad17757dbd355bb51`

## core/src/frozen_labels_census.py

[Open file](../repository/core/src/frozen_labels_census.py)

Stores frozen scientific functions for parsing development GT, constructing virtual gates, and determining reference events.

- GT/seqinfo parsing and development-input constants
- Body-height fitting, six virtual gates, and observation points
- Reference confirmation, visibility, and population-summary functions

**Inputs:** Caller-supplied GT text, sequence metadata, observations, and NumPy module; file access is handled by the caller

**Outputs:** Parsed rows, body-height models, geometry, confirmation, and attribute dictionaries

**Usage:** Start from labels.build_labels to understand the computational definition of reference labels.

**Caution:** Scope: functions and development constants from the frozen copy. Reference confirmation uses GT body height; system confirmation uses the G1 model.

**Current SHA256:** `318d4761a1d5ca24dddce5977763cba4fbe3dca3a4567f62d46ee1736082d379`

## core/src/frozen_labels_regions.py

[Open file](../repository/core/src/frozen_labels_regions.py)

Stores frozen functions for region distances and cross-region transition extraction from tracks.

- Distance from a point to polygon boundaries
- tunnel, plaza, and gap region decisions
- Segmented extraction of source-to-target observation transitions by track

**Inputs:** In-memory polygons and track observations; data access: none

**Outputs:** Event lists, track segments, and extraction statistics

**Usage:** Read to understand when a transition is recorded and when missing track observations trigger a reset.

**Caution:** Scope: event time is the first target-region observation. Extraction uses observed transitions; exact physical intersection with the finite centerline remains outside this definition.

**Current SHA256:** `637d18ea00ded921ba7be8ff8264aebbc445888d7c346460c8712df3b9f262a1`

## core/src/frozen_score/__init__.py

[Open file](../repository/core/src/frozen_score/__init__.py)

Declares the frozen scoring-function directory as a Python subpackage.

- Description of frozen pure scoring functions only
- Import-time data input/output: none

**Inputs:** Data access: none

**Outputs:** Runtime outputs: none

**Usage:** Consult to understand the frozen_score package structure.

**Caution:** Scope: Python subpackage initialization; scoring is through the calling entry points.

**Current SHA256:** `9d9394e5f1615ae7d22a9a274e6ce15c8239ee22438f440707b2fa2d151949f7`

## core/src/frozen_score/aggregate.py

[Open file](../repository/core/src/frozen_score/aggregate.py)

Combines per-gate scores into overall and visibility-stratified statistics.

- Aggregation of hits, references, and all final-event counts
- Consistency checks for identity-status denominators
- Stratified scores and compatibility fields for historical clean precision

**Inputs:** List of per-gate result dictionaries; data access: none

**Outputs:** Summary dictionary with exact Fraction and decimal representations

**Usage:** Follow score.py or tracker_score.py to understand the denominators in final tables.

**Caution:** Scope: all final events remain in the denominator, including unknown, ambiguous, and ignored identities. Historical compatibility fields are reported separately from the primary score.

**Current SHA256:** `17b83db898956ecbd15cd2f4c4b3e7e58da6776fa43f8195528eafd496bdcf8a`

## core/src/frozen_score/e1.py

[Open file](../repository/core/src/frozen_score/e1.py)

Implements frozen E1 v2 rules for box-level identity association and event matching.

- Box IoU graph and one-to-one assignment
- Assignment margins, containment, and per-frame evidence
- Event matching constrained by direction, time, position, and identity
- Evidence on member matchability across equivalent optima

**Inputs:** In-memory output boxes, GT boxes, predicted events, reference events, and a matching solver

**Outputs:** Identity records, event pairs, anonymous feasible edges, and optimal-member audits

**Usage:** Read to understand how a hit is determined to concern the same person.

**Caution:** Scope: identity-correct hits require the identity constraints as well as spatial feasibility. pools retains support for adapting the older system.

**Current SHA256:** `8edc931b0a02aee872e7a20f2ab67e1921322b180a80de321488ae1d9c95fc02`

## core/src/frozen_score/identity.py

[Open file](../repository/core/src/frozen_score/identity.py)

Aggregates per-frame identity observations into conservative event-level identity decisions.

- GT parsing for identity use with class retention
- Observation votes and modal decisions
- Handling of identity conflicts before/after the event and unknown states

**Inputs:** GT text, per-frame identity observations, event anchor frame, and class mapping

**Outputs:** Per-frame GT pools, class table, event identity status, and voting evidence

**Usage:** Read to understand the origins of known, ambiguous, ignore, and mixed_unknown.

**Caution:** Scope: track IDs and GT identities have separate roles. Insufficient or conflicting observations retain uncertainty in the event identity state.

**Current SHA256:** `ab33874ce2cd7ecf55b3d335331309fd69b6a9dc058e59bb00378186c607192a`

## core/src/frozen_score/labels_view.py

[Open file](../repository/core/src/frozen_score/labels_view.py)

Converts derived reference labels into stable records used by the scorer.

- Stable numeric keys and event-ID handling
- Exact fractional time derived from frames
- Mapping of reference-event coordinates, identity, visibility, and support information

**Inputs:** One in-memory reference event and its source-row information

**Outputs:** Standardized GT event view

**Usage:** Read to understand how label fields enter the matching rules.

**Caution:** Requires: fixed development sequences and gates, with consistent time, body-height, and visibility fields.

**Current SHA256:** `1df49add65704dcfed0e0c698d92802d4f284d6041833a465e2ef160d2acae6e`

## core/src/frozen_score/matching.py

[Open file](../repository/core/src/frozen_score/matching.py)

Solves feasible bipartite matching with exact arithmetic and examines ranges across equivalent optima.

- Checks for stable keys, feasible edges, and Fraction costs
- Maximization of match count followed by minimization of cost
- Secondary-count bounds and existence queries under fixed primary objectives

**Inputs:** Stable keys on both sides, feasible edges, exact costs, and optional secondary weights; data access: none

**Outputs:** Matched pairs, optimal cost, ranges, and witness solutions

**Usage:** Read to understand deterministic ties, globally optimal ranges, or member ambiguity.

**Caution:** Scope: only listed edges are feasible. Secondary objectives preserve the optimal match count and primary cost.

**Current SHA256:** `bf40affe41d742c07b826303f92062ef391be54123517ac260060eaddcf5b0ae`

## core/src/frozen_score/provenance.json

[Open file](../repository/core/src/frozen_score/provenance.json)

Records source provenance for frozen identity, matching, label-view, and aggregation functions.

- Bindings between each module's source file and bundled file
- Function line numbers, snippet fingerprints, and AST fingerprints
- Statements that scientific functions remain unchanged and old script main functions remain outside the package imports

**Inputs:** Data access: none

**Outputs:** Provenance and hash-check table for frozen scoring code

**Usage:** Consult to trace the scorer to its original implementation; read by both scoring orchestrators.

**Caution:** Scope: source paths are provenance references for the bundled scoring functions.

**Current SHA256:** `227d72b7e340d7fba1da38d8dd7976dc2d9f7283e14d9f5a122dd8f9ba58b461`

## core/src/image_paths.py

[Open file](../repository/core/src/image_paths.py)

Checks the original path identity of requested development images before rendering, including links and directory junctions.

- Layer-by-layer lstat checks for symlinks and Windows reparse points
- Restriction to sequence/img1 and specified six-digit frame filenames
- Path-identity checks before and after resolution

**Inputs:** Image directory, 01/02 sequence name, and requested frame numbers; file metadata only

**Outputs:** Canonical directory and image paths in request order

**Usage:** Read when investigating rejected rendering paths or learning the I1 protection.

**Caution:** Scope: file-metadata and path-identity checks. Pixel contents and atomic protection against changes between check and read are outside this check.

**Current SHA256:** `532078a0b53f8a468c0f021ac1859affc50850aa88e982af79fbb054538724c9`

## core/src/inspection.py

[Open file](../repository/core/src/inspection.py)

Organizes verified reference labels and scoring audits into readable event evidence.

- Filtering of misses after reading existing global canonical pairings
- Source/target observations, visibility windows, and identity-valid support
- Complete evidence binding and per-frame integrity checks
- Optional image overlays at fixed time offsets

**Inputs:** Bundled derived labels and explicit GT; optional tracks, sealed scoring evidence, and local images

**Outputs:** Event details and miss lists; PNG files and render_manifest.json when rendering

**Usage:** Enter through inspect_saved_event.py or inspect_event.py to explain an event's evidence.

**Caution:** Scope: presentation of saved pairings and identity evidence. Missing output support describes the available system evidence; visual visibility and causal explanations require separate assessment.

**Current SHA256:** `9f32ebe70ef596480f6d22997b3b964c5b312bf74f2abd3c2a44dde39c0630b6`

## core/src/labels.py

[Open file](../repository/core/src/labels.py)

Orchestrates derivation of complete crossing labels from development GT and adds traceable metadata.

- Explicit input-set, hash, and resource-limit checks
- Calls to frozen census and region functions to generate labels, geometry, and body-height models
- Audit fields, provenance manifests, read ledgers, and failure records

**Inputs:** Explicit 01/02 GT and seqinfo mappings

**Outputs:** transitions, geometry, height_models, summary, source_manifest, read_ledger, and build_run

**Usage:** Follow build_labels calls from reproduce.py or score_tracker.py to understand label construction.

**Caution:** Scope: includes unconfirmed events, with confirmation determined by frozen rules. Missing observations remain missing; human confirmation is a separate evidence source.

**Current SHA256:** `252d539cef3bf0963af3e560e25f6ed44975eb58745ffd5593eb30a17d333018`

## core/src/lineage.py

[Open file](../repository/core/src/lineage.py)

Adds a separate table describing source frames, original GT line numbers, and observation intervals for every derived event.

- Position projection along the gate
- GT line numbers for source, target, and confirmation observations
- Notes on missing frames, invalid points, and unestimated physical intersections

**Inputs:** Derived transitions.jsonl.gz and geometry.json

**Outputs:** Separate lineage_enrichment.jsonl.gz and build metadata

**Usage:** Read to trace the supporting frames of an event or distinguish its observation interval from its physical crossing time.

**Caution:** Scope: supplementary provenance with the original scientific fields preserved. Positions are along-gate projections; physical crossing locations remain unestimated.

**Current SHA256:** `91589e80d57b2135243616e279627010610ee6267dc96bddc3b0aedeb48977e3`

## core/src/motchallenge.py

[Open file](../repository/core/src/motchallenge.py)

Strictly parses ten-column MOTChallenge tracking results and converts coordinates.

- Per-line checks for finite values, frame numbers, track IDs, positive dimensions, and duplicate rows
- Conversion from one-based top-left coordinates to zero-based continuous xyxy
- Preservation of within-frame file order and original line numbers

**Inputs:** Track text string and sequence length; file access is handled by the caller

**Outputs:** Track boxes grouped by frame and input statistics

**Usage:** Read when connecting a custom result file or investigating input-format errors.

**Caution:** Requires: every input row to be valid. Coordinates and observations are preserved through parsing, and within-frame order determines identity tie-breaking keys.

**Current SHA256:** `63b752284f7daf9d167c202373dc130b71521f747da548ecc42abca44710dbcc`

## core/src/regression.py

[Open file](../repository/core/src/regression.py)

Compares newly computed panel results against bundled historical expectations item by item.

- Exact comparisons of primary, per-sequence, and per-gate summaries
- Comparisons of final event IDs, frames, directions, and member lists
- Position round-trip errors and bounded difference records

**Inputs:** In-memory expected, report, units, and events; data access: none

**Outputs:** PASS/FAIL, check results, and difference-detail dictionary

**Usage:** Read to understand how score_tracker.py --self-test determines agreement.

**Caution:** Scope: exact comparisons except for the position tolerance fixed in advance by the protocol.

**Current SHA256:** `dcb84522be6064fd6dcb8de230f7519e944a281b5e6c7bb3e467b56d841d7155`

## core/src/score.py

[Open file](../repository/core/src/score.py)

Reconstructs identity associations from existing v11 output boxes and final events, then scores full-sequence events.

- Verification of the reduced cache and frozen scoring code
- Per-frame identity decisions and per-gate event matching
- Equivalent optimal-matching ranges, aggregation, and parity comparison with historical results

**Inputs:** 01/02 GT, rebuilt labels, yolox_v11 cache, and expected references

**Outputs:** scores.json, units.json, matching_ranges.json, identity/matching audits, and receipts

**Usage:** Enter through reproduce.py to understand independent reconstruction of identity decisions during cache reproduction.

**Caution:** Scope: identity reconstruction and event scoring from retained outputs. Matching ranges describe equivalent optima.

**Current SHA256:** `dc6e8602791858f04e2efba3ec91f2073e72c3c0932d22a95b8a78ac139c1fbd`

## core/src/tracker_score.py

[Open file](../repository/core/src/tracker_score.py)

Connects event extraction, identity association, and per-gate scoring for standard track outputs.

- Strict track parsing and per-frame identity audits
- Frozen event chain using output-box bottom centers
- Per-gate and per-sequence summaries and ranges across all optimal matchings

**Inputs:** 01/02 GT, rebuilt labels, track files, package path, and a new output directory

**Outputs:** Scoring report, event summaries, complete event-chain records, and identity/matching audits

**Usage:** Follow score_tracker.py or the new-evidence inspection entry point to read the complete scoring workflow.

**Caution:** Requires: caller verification of rebuilt-label parity. The identity-precision denominator includes all final events.

**Current SHA256:** `9916a2b8e232e1c78ba8a48875331cab8b1c2829c41f2cdbc7284a1132c7520f`

## core/STATUS.md

[Open file](../repository/core/STATUS.md)

Describes the original sample's acceptance boundaries and release readiness at that time.

- Component checks completed at that time
- Distinction between integrated receipts and component passes
- Historically listed release-preparation tasks

**Inputs:** Data access: none

**Outputs:** Historical status notes

**Usage:** Read to understand restrictive wording retained in early versions.

**Caution:** Scope: outstanding and not_reviewed reflect the original file's historical state. Current review conclusions are recorded separately.

**Current SHA256:** `30c2f48ae4b3ffa79c300675da3078ed066a8f40b060b643fa16c5cdefe1af3c`

## core/tests/scratch_support.py

[Open file](../repository/core/tests/scratch_support.py)

Selects a parent directory outside the package for synthetic-test temporary files.

- INSPECTOR_TEST_SCRATCH environment setting
- Default .inspector_synthetic_scratch path
- Rejection of explicitly configured scratch directories inside the source package

**Inputs:** Environment variables and current working directory; no real-data reads

**Outputs:** Writable synthetic temporary-directory path

**Usage:** Read to understand why check_inspector.py writes test files outside the package.

**Caution:** Scope: temporary-file support for synthetic tests.

**Current SHA256:** `1a6ed1160638417be3f74322aafb9cf83b814128102001387353c092bc2290e1`

## core/tests/test_audit_integrity_round2.py

[Open file](../repository/core/tests/test_audit_integrity_round2.py)

Uses invented per-frame records to check the identity-audit integrity validator.

- Cases for truly empty frames, sparse inputs, and single-pass records
- Cases for missing frames, duplicates, disorder, box/ID mismatches, and invalid types
- Contradictory status, assignment-pair, and numerical-field cases

**Inputs:** In-memory fake data constructed by code; no real GT or tracks required

**Outputs:** unittest results when executed

**Usage:** Read after changes to audit_integrity.py to learn which errors should be rejected.

**Caution:** Scope: static reading for this guide. The tests assess audit-integrity behavior; scientific assignment correctness is a separate validation question.

**Current SHA256:** `aea255d29ccbdcef07e9901669c90af90f72c5533f50f2f24ba1cc29d39c5181`

## core/tests/test_evidence_seal_round2.py

[Open file](../repository/core/tests/test_evidence_seal_round2.py)

Uses synthetic files to check whether evidence sealing and external fingerprint binding detect changes.

- Complete sealing of six members and deterministic-byte cases
- Rejection of missing files, incomplete receipts, and overwriting old seals
- Fault cases involving altered compressed bytes, manifests, and path/hash structures

**Inputs:** Newly created synthetic evidence files

**Outputs:** unittest results and temporary synthetic files when executed

**Usage:** Read to understand trust conditions in evidence_seal.py or when changing the seal format.

**Caution:** Scope: synthetic evidence files. This guide inspected the code statically.

**Current SHA256:** `0e704fffc6e06c12c3592d8c4a9fa70defd1be7d624fe9d15f4e86cc1d4498bd`

## core/tests/test_image_paths_round2.py

[Open file](../repository/core/tests/test_image_paths_round2.py)

Checks that image-path validation rejects invalid frames, symbolic links, and directory junctions.

- Standard development-image paths and invalid frame-number cases
- Real links and simulated Windows reparse metadata
- Checks for post-resolution path changes and absence of file-content reads

**Inputs:** Temporary placeholder files/directories and simulated path metadata

**Outputs:** unittest results when executed

**Usage:** Read to understand why image_paths.py checks original paths layer by layer.

**Caution:** Scope: path identity using placeholders and metadata. This guide inspected the code statically.

**Current SHA256:** `b4421e7703963db6d2d46b2fcc3a15be1cc53355c593082696f61f084459b1f0`

## core/tests/test_inspection_synthetic.py

[Open file](../repository/core/tests/test_inspection_synthetic.py)

Checks pairing explanations, miss filtering, and support-region semantics in event inspection.

- Distinction between identity matching and anonymous proximity
- Exclusion of unconfirmed events from misses, complete member records, and single-pairing constraints
- Global matching before visibility filtering and distinction between spatial and temporal support

**Inputs:** Events, pairing audits, and observations constructed in code

**Outputs:** unittest results when executed

**Usage:** Read to check that Inspector presentation preserves scoring semantics.

**Caution:** Scope: invented event and audit inputs. Human verification of real data is separate; this guide inspected the code statically.

**Current SHA256:** `78427c01996dea8f2f156ae06a0195743874de54c6a9609335066cfc3623af59`

## core/tests/test_inspector_integration_round2.py

[Open file](../repository/core/tests/test_inspector_integration_round2.py)

Uses complete combinations of invented files to test integration of Inspector and both command-line entry points.

- InventedFixture with a three-frame fake sequence, a hit, and a miss
- Error chains for complete seals with missing frames/box mismatches and changed input hashes
- Preservation of failure ledgers and original exceptions
- Checks that saved-result inspection avoids rescoring and resealing

**Inputs:** Temporary synthetic labels, tracks, scoring audits, and mocks; no real data

**Outputs:** unittest results and temporary evidence when executed

**Usage:** Read to understand how the engineering protections work together or when changing CLI failure handling.

**Caution:** Scope: resealing creates synthetic fault cases in tests. Existing real evidence retains its original seal. This guide inspected the code statically.

**Current SHA256:** `5ad0d1af967ec642155ae714c86b086430c7377da28f7906c369bc5335859e7b`

## core/tests/test_rendering_round2.py

[Open file](../repository/core/tests/test_rendering_round2.py)

Uses program-generated color-block images to check actual rendering outputs and exception handling.

- Five fixed frame offsets, boundary clipping, and deduplication
- GT/system box colors and input/output hash receipts
- Missing images, dimension mismatches, existing directories, and mid-run failures

**Inputs:** Generated color-block images and in-memory fake records; requires Pillow

**Outputs:** Test PNG files, rendering manifest, and unittest results when executed

**Usage:** Read when changing render_event to understand its presentation and recordkeeping contract.

**Caution:** Scope: generated synthetic graphics. This guide inspected the code statically.

**Current SHA256:** `26d6e0eee352f912c291f69c64c6780b225c27176d201ac0f5d995015ce5954d`

## core/tests/test_saved_inspection_cli_round2.py

[Open file](../repository/core/tests/test_saved_inspection_cli_round2.py)

Uses a mock inspector to check that the saved-result inspection command consumes the original evidence as recorded.

- Explicit external SHA256 and event/list mode forwarding
- Prevention of scoring, retroactive sealing, and writes to the original directory
- Missing arguments, incorrect digests, output conflicts, optional rendering, and failure records

**Inputs:** Temporary synthetic files and FakeInspector

**Outputs:** unittest results, fake inspection receipts, and failure records when executed

**Usage:** Read when changing inspect_saved_event.py arguments or its output contract.

**Caution:** Scope: command behavior with intercepted scientific workers. Scientific reproduction requires its own execution evidence. This guide inspected the code statically.

**Current SHA256:** `bd2cb68500ca298143936d74e90c7f271ab4365c77c3178f260d6a8a36ce7fed`

## DATA.md

[Open file](../repository/DATA.md)

Describe bundled derived materials, lawful external inputs to prepare, and data and weight sources.

- Separates distribution scopes for 01/02 development, 03/05 confirmation, stadium and human review materials
- Shows the GT/seqinfo directory layout
- Lists public sources, sizes and local SHA values for fixed weights and archives
- Treats code, data, dependency and weight licenses separately

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Read when preparing inputs or checking provenance; the document does not download anything.

**Caution:** The listed SHA values identify locally acquired files. Upstream authentication, current link availability and current license status require their corresponding evidence; this guide retains the historical checks.

**Current SHA256:** `0cd098e874219100db4a21a694041e58f14745ea9ceaa11d9af848c8a59811be`

## DATA_LICENSE

[Open file](../repository/DATA_LICENSE)

State the license scope for derived labels, generated geometry and numerical examples.

- Declares CC BY-NC-SA 3.0 and links to the legal text
- Requires original-data attribution and change notices
- Excludes original images, videos, complete GT, code and third-party software

**Inputs:** License guidance for distributing or reusing bundled derived data.

**Outputs:** No files.

**Usage:** Read alongside core/ATTRIBUTION.md and core/CHANGES.md.

**Caution:** Its ATTRIBUTION.md and CHANGES.md references retain the original core-relative layout; use core/ from the outer repository. Rights-chain review has its own status.

**Current SHA256:** `1e41fc636502b14a6c426aa0602ddeb497893a6085af36da6186f76de6fa67c9`

## docs/claims_and_limits.md

[Open file](../repository/docs/claims_and_limits.md)

Organize the evidence, supported conclusions and scope of each experiment.

- Limits the project to a resource and conditional empirical diagnostics
- Reviews confirmation, E1/E2, ReID, E3/E4 and stadium evidence
- Separates historical independent scoring, repository CPU checks and cross-machine acceptance
- Preserves disclosures about GPU nondeterminism, prior exposure, human QC and unresolved rights

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Use as a claim-boundary reference when writing papers, reports or project introductions.

**Caution:** The guide status note records later v2 and Q3_v2 reviews. Automatic attribution describes stored pipeline outputs. Human review assesses visual observability; causal conclusions require additional evidence. The baseline combines established tracking components.

**Current SHA256:** `5008486baadfa1b7a5fd90cca8b61f97722bec83375984de7dc8ce8289cdb6e8`

## docs/HANDOFF_CHECKLIST.md

[Open file](../repository/docs/HANDOFF_CHECKLIST.md)

Provide the reading, verification, human-review and release-check sequence for collaborators.

- Start with claim limits and CPU interface checks
- Separate frozen-source/adaptor review from GPU acceptance
- Preserve stopped approaches, unknowns and matching ties
- Manage answers separately and check attribution, cross-machine reproduction and privacy before release

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Check existing evidence item by item before handing off to collaborators.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. Unblinding follows its explicit authorization, and the second reviewer supplies an independent human judgment.

**Current SHA256:** `f041e6306f486f89b815ecdeaa2b057278ca47067c8c5791c315bb4e9e3e8566`

## docs/NATIVE101A_STATUS_ADDENDUM.md

[Open file](../repository/docs/NATIVE101A_STATUS_ADDENDUM.md)

Record an existing native v11 development-equivalence receipt so it is not mistakenly rerun as untested.

- Binds the REGRESSION_RECEIPT path and SHA
- Records comparison of 3,211 frames, 12 gates, M4, matching and 161,840 identity observations
- Reports 86/180, 203/210, 569/712 and CPU timing
- Distinguishes scientific comparison from byte equality of whole JSON rows or compressed files and retains the prior preflight incident

**Inputs:** Summary of an existing receipt; this file loads neither the receipt nor inputs.

**Outputs:** No runtime results.

**Usage:** Understand what the native-adapter equivalence comparison actually covered.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. The receipt compares scientific fields; file-byte equality and later acceptance have separate evidence.

**Current SHA256:** `e92e311f224c8f5e4dc2289bfa5f5a9869f1b7ed16b9e83b6849833e2dc1e51d`

## docs/PIPELINE_PATCHDIFF.md

[Open file](../repository/docs/PIPELINE_PATCHDIFF.md)

Explain preserved source code and path/input/output changes for portable interfaces.

- Copying scope of 54 complete files and 16 physical source nodes
- Permitted functions/constants and omitted application wrappers
- Detection, tracking, native-scoring and confirmation adapter comparisons
- Reasons for excluding complete files and new wrapper fixes such as MOT coordinates +1

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Review porting differences alongside pipeline_frozen_map.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. Identify verbatim slices and vendor compatibility copies by their precise provenance; new wrappers have separate acceptance records.

**Current SHA256:** `d893a69057524aee44cb557e686d0b4c6270236276ee5272c3ca1410e2a0458a`

## docs/PIPELINE_PORTABILITY.md

[Open file](../repository/docs/PIPELINE_PORTABILITY.md)

Give technical users each portable entry point's full contract and actual validation scope.

- Explicit resource paths, size/SHA bindings, complete frames and new external outputs
- Detection-cache and three-panel output contracts
- Native v11 raw-footpoint, M4, event and dedicated identity-scoring contracts
- Confirmation-control generation steps and inputs for nine analysis primitives
- Environment dependencies and scopes of 16 pipeline and 10 native-scoring synthetic tests

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Consult when connecting manifests or distinguishing CLI preflight from execution.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. Check dependencies and input completeness for each command. Each analysis primitive covers its specified part of a historical experiment.

**Current SHA256:** `10b3f83c758b56effc690fea0ed22502c2c7af6d77ef3055468f1172b7d501f7`

## FROZEN_CODE_MAP.json

[Open file](../repository/FROZEN_CODE_MAP.json)

Identify files copied from frozen sources, extracted as slices or changed for presentation engineering.

- 114 entries: 82 complete copies, 16 verbatim node slices, 2 presentation revisions and 14 presentation-support copies
- Source paths, sizes, SHA values and slice boundaries
- Presentation revisions retain previous_provenance and original preimages
- Lists 5 excluded complete application files and the reasons

**Inputs:** Existing frozen sources, permitted slices and presentation integration records.

**Outputs:** A static provenance map compared against current files by the verifier.

**Usage:** Look up repo_path to distinguish complete copies from partial ports.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. Top-level native-equivalence status and some source fields are historical. Preserve the distinction between complete source copies and extracted slices.

**Current SHA256:** `cc976e24e08bd571c1f6d34a10be70dfa6195dfcd8fe9cb39c244b054c5d8db5`

## HISTORY.md

[Open file](../repository/HISTORY.md)

Preserve how the research direction changed and why specific approaches stopped.

- Early pixel-porting, geometry blind spots and the unsuccessful G1 route
- Shift toward public identity and visibility evaluation
- Stopping boundaries for G1, T3, HeadGate, D1, GateLink and ReID
- Later E1-E4 diagnostics, YOLOX baselines, confirmation and resource packaging

**Inputs:** Documentary sources from historical logs, reviews, reports and receipts.

**Outputs:** Static research history; no historical experiments.

**Usage:** Read to understand the motivation and avoid repeating stopped approaches.

**Caution:** Use the guide status note for the later approved zip and current Q3_v2. Each stopping decision applies to its specified frozen configuration; unresolved explanations retain their unknown status.

**Current SHA256:** `b1471e543d7a7886a29e8e4f0efaccd8a1e3f5577809f52eeec4ffba092db0e5`

## INTEGRATION_CANDIDATE.md

[Open file](../repository/INTEGRATION_CANDIDATE.md)

Explain inspector engineering integration, presentation revisions and their provenance limits.

- Integrates integrity adapters, saved-score inspection and synthetic tests
- Explains the presentation_layer_revision status of two presentation files
- Documents exact-hash and line-number exceptions in the repository verifier
- Provides normal and stdlib-only check_inspector entry points

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Consult for integration changes, existing receipts and the audit patch.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. Old unsealed scores retain their status; integrity checking and rescoring are separate operations.

**Current SHA256:** `87698e4b142b91ac861c1702466b5c7931be1e25ed7e92bdf460478fea31fac6`

## LICENSE_CODE

[Open file](../repository/LICENSE_CODE)

License project-authored code and explicitly identified copies of its own pure functions under MIT.

- MIT permission to use, modify and distribute
- Copyright-notice retention and warranty disclaimer
- A Scope section excluding data, weights, original MOTChallenge data and third-party dependencies

**Inputs:** Scope guidance for code reuse or distribution.

**Outputs:** No files.

**Usage:** Establish code provenance from the ledger before applying the corresponding license.

**Caution:** Apply each license according to provenance: project code, vendor code and numerical data have separate scopes.

**Current SHA256:** `555b127532b4bb7d1a4717b87001d68bc5584750a395d6a0a949d94ace512615`

## MANIFEST.json

[Open file](../repository/MANIFEST.json)

Provide file sizes and SHA256 bindings for the delivered directory.

- The files list binds 236 files and excludes the manifest itself
- Records the historical candidate status
- Records presentation-overlay provenance and the documentation-patch SHA
- States that scientific computations and synthetic suites were not rerun for this version

**Inputs:** Packaged repository files and version information.

**Outputs:** A static manifest for verifier comparisons.

**Usage:** Check for missing, additional or byte-modified files.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. Manifest equality establishes version agreement; scientific correctness has separate evidence. Total directory size includes MANIFEST itself.

**Current SHA256:** `f2816cf4b665fd7343084a7a3ba8f988a07639e59d8bce7fb22b2b0ee494c4fb`

## metadata/core_frozen_map.json

[Open file](../repository/metadata/core_frozen_map.json)

Preserve the original core-resource provenance copied from an anonymous candidate.

- Source package, original candidate and source MANIFEST SHA
- core_code_files lists 26 original code files and agreement with the candidate
- all_core_files lists the original 80 core paths, sizes and SHA values
- Records the privacy scan and unchanged scientific rules at that time

**Inputs:** File versions from the original core copy.

**Outputs:** Static mapping also used by the native scorer to verify invoked core sources.

**Usage:** Trace frozen scientific-core provenance alongside root FROZEN_CODE_MAP.

**Caution:** This original 80-file snapshot is supplemented by the root map for later inspect_event.py/inspection.py presentation revisions and support files. Use the root map for the current inventory.

**Current SHA256:** `d70de0f2ae6afd0dfff7b45d990e62b80c8bfbdd2d6e65da129c6def3855f640`

## metadata/docs_sources.json

[Open file](../repository/metadata/docs_sources.json)

Connect documentary statements and table cells to specific historical source versions.

- 36 sources: S01-S34 and two R2 supplements
- Each records original-project relative path, SHA, size, read scope and whether copied in full
- table_transcriptions binds 138 RESULTS header/data rows and individual cell strings
- States that documentation work did not recompute results and records patch provenance

**Inputs:** Provenance records for historical documents, tables and receipts.

**Outputs:** Static documentation lineage.

**Usage:** Look up S identifiers or RESULTS numbers for source paths and line numbers.

**Caution:** This ledger traces documentary sources and table transcriptions. Experiment inputs and distribution status require their own manifests; scientific values retain their historical scoring evidence.

**Current SHA256:** `dcaeca87ed7afe1ed8b214a8f78568b25551b30feca5479dd7b1058fcbb3d3bb`

## metadata/human_materials_map.json

[Open file](../repository/metadata/human_materials_map.json)

Bind copied human-review protocols, empty templates, synthetic checks and root licenses to their sources.

- 11 verbatim-copy entries
- 5 Q2/Q3 protocols through #87
- Two Q2/Q3 HTML templates and their synthetic check scripts
- repo_path, original_project_path, bytes, sha256 and role

**Inputs:** Protocol, template and license versions selected at delivery.

**Outputs:** Static source map.

**Usage:** Verify which original protocol version a review template corresponds to.

**Caution:** This historical map ends at #87. The #111 additions and current 93-item Q3_v2 material/answer manifests belong to separate packages.

**Current SHA256:** `e70c589ac183c4da16980a2365a8e749cc32641585c906dc6d0d681502a5615d`

## metadata/inspector_verifier_compatibility.patch

[Open file](../repository/metadata/inspector_verifier_compatibility.patch)

Show the repository verifier's narrow exception for an intentionally invalid synthetic path.

- Targets line 102 of core/tests/test_evidence_seal_round2.py
- Removes the associated absolute_machine_path finding only when the complete file SHA matches
- Reports reviewed_exception_hash_changed if the SHA changes

**Inputs:** Text difference between the original and candidate verifiers.

**Outputs:** Static patch text; it does not apply itself.

**Usage:** Compare with verify_repository.py to assess whether the exception is sufficiently narrow.

**Caution:** The exception applies only to its bound file version and line. The remaining absolute-path findings, numeric-line exceptions and scientific-hash checks retain their usual handling.

**Current SHA256:** `c64a051a720fabfc5b2de43fb47ebf0dcf2f35e6508058709c092a032c1adc82`

## metadata/native_v11_scoring_status.json

[Open file](../repository/metadata/native_v11_scoring_status.json)

Record reused native-scoring core functions and historical validation status in machine-readable form.

- functions_reused lists label, E1 pool/assignment, identity, matching, range and aggregation functions
- Separates saved native final_events from actual post-M4 tracker_rows
- Records an existing receipt path/SHA and 10 synthetic checks
- Retains previous_status_record and explains conservative historical status emitted by runtime scripts

**Inputs:** Saved validation notes and provenance mappings.

**Outputs:** Static status record; no regression execution.

**Usage:** Identify reused scientific functions and the exact regression receipt.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. confirms_existing_receipt_only and execution_authorization_granted preserve the scope of this receipt-only update.

**Current SHA256:** `84f566dabf2777511a959e99f9f7e0f1329b1867488d8242847b629ddc96c767`

## metadata/pipeline_frozen_map.json

[Open file](../repository/metadata/pipeline_frozen_map.json)

Record original sources for ported detection, tracking, analysis and confirmation modules.

- 54 complete source/license copy entries
- 16 physical-node slices with node names, original file SHA, line ranges and slice SHA
- Reasons for excluding 5 complete application files
- Empty scientific_changes and slice-authorization notes

**Inputs:** Existing project adapters and permitted nodes.

**Outputs:** Provenance mapping for review and verification.

**Usage:** Look up a module by repo_path and distinguish files from fragments.

**Caution:** Source paths refer to the original project. Check distribution status for each referenced source; GPU and real-data regression have separate receipts.

**Current SHA256:** `b7daba8f54cd64bf6c9312aa69af3df5317543052ceb5fbc459d93eccfe9882f`

## metadata/practical_v2_documentation.patch

[Open file](../repository/metadata/practical_v2_documentation.patch)

Preserve line-by-line evidence of practical v2 wording changes.

- Clarifies region transitions, first target-region entry and finite-line intersections
- Clarifies the anchor for the visibility window
- Recasts NOT_REAL_DATA_REGRESSED as historical and adds the existing local receipt
- Covers README, core README, VERIFY, PIPELINE and related docs

**Inputs:** Differences between prior and revised documentation.

**Outputs:** Static unified diff.

**Usage:** Understand why wording changed or review the documentation-only scope.

**Caution:** Use this historical diff for review. The candidate already incorporates these changes; scientific implementations retain their existing versions.

**Current SHA256:** `487cef3646038ee3dbb0b451bb47ecc3f00e7a398d263c7c221d135646a9ca94`

## metadata/practical_v2_documentation_ledger.json

[Open file](../repository/metadata/practical_v2_documentation_ledger.json)

Bind before-and-after hashes for each practical v2 documentation update.

- changes records old_sha256/new_sha256 for 10 paths
- Binds the source-patch SHA
- States no code or result changes and preservation of original status
- Records the added README historical-status banner

**Inputs:** Documentation versions before/after the update and their diff.

**Outputs:** Static change ledger.

**Usage:** Review which files this documentation revision affected.

**Caution:** Use current MANIFEST for current file integrity. This ledger preserves the update history alongside later acceptance records.

**Current SHA256:** `49804cd71cf62db5f98204f576a1dfd0a67ce77908215f98f888391ba9ff847b`

## metadata/privacy_reviewed_exceptions.json

[Open file](../repository/metadata/privacy_reviewed_exceptions.json)

Record manually reviewed privacy-scan false positives and required third-party attribution.

- A specific compressed-label line/JSON field is an integer GT physical line number
- The exception binds file SHA, line, field path and required_type
- Separately records retention of the original SORT author's attribution/contact in OC-SORT

**Inputs:** Specific verifier pattern matches and existing manual review.

**Outputs:** Narrow exceptions and attribution notes read by the verifier.

**Usage:** Locate the bound file version and field when reviewing a scan false positive.

**Caution:** Apply each exception only when its bound file, line and type conditions hold. Review matching digits elsewhere independently.

**Current SHA256:** `0df075023da24ccab1ddaa212b752b89bcd095e788e22b1fb3f457a4885ef43e`

## metadata/reference_environment101.json

[Open file](../repository/metadata/reference_environment101.json)

Record software versions observed during packaging and the environment-validation scope.

- Python 3.10.18 and versions of 8 distributions including NumPy, Torch and SciPy
- Windows reference platform
- Same-machine CPU regression was performed; clean-machine installation and packaged GPU execution were not verified
- Explicitly excludes wheel verification and a complete environment lock

**Inputs:** Installed-distribution metadata from the reference environment.

**Outputs:** Static environment description.

**Usage:** Consult when investigating environment differences or preparing reproduction.

**Caution:** Use the version list as environment metadata. Cross-hardware numerical agreement and installable dependency closure require separate validation.

**Current SHA256:** `610510dac793df9096c642ea37bb035bc46e3230a12d77d2995322fa04d47282`

## PIPELINE.md

[Open file](../repository/PIPELINE.md)

Explain the stages from reference labels, detections or tracks to crossing events and identity scores.

- Label reconstruction and cached-output regression
- Standard-track scoring and event inspection
- Pixel detection, three tracker panels, native v11 generation and dedicated scoring
- Analysis primitives and confirmation-command generation
- Separates self-checks, real-input regression and acceptance on another machine

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Choose an entry point by stage, then consult the portability document for its input contract.

**Caution:** Read delivery status as historical and use the guide status note for the later approved zip and current Q3_v2. Uppercase command paths are placeholders; outputs use new external locations.

**Current SHA256:** `b320b759481657808b55a59b15f70688cbed4b1bb878beb4599306130692a4aa`

## PRACTICAL_V2_STATUS.md

[Open file](../repository/PRACTICAL_V2_STATUS.md)

State that practical v2 changes only documentation semantics and historical status descriptions.

- Does not change scientific functions, parameters, results or execution authorization
- Retains the prior 124 engineering checks and 4 genuine-symlink skip records
- Distinguishes conservative runtime status from existing receipts recorded in metadata

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Read to verify the scope of this documentation revision.

**Caution:** Use the guide status note for later approved zip and current Q3_v2 status. This revision carries forward the earlier engineering and scientific receipts.

**Current SHA256:** `03e668cb3e88526a2c527460a6816571b22a203e7d4f784e05b8d3cb70f383c7`

## protocols/human_qc/q2_protocol84_v1.md

[Open file](../repository/protocols/human_qc/q2_protocol84_v1.md)

Freeze Q2's comparison of events unrecovered across systems and its blind visual-evidence review.

- Uses only 180 low-visibility 01/02 reference events and existing outputs of five systems
- Retains U_UNRESOLVED when input/output lineage is missing
- Fixes sampling and anonymous pages for jointly unrecovered events and controls recovered by at least 3 systems
- Asks visibility before/after the event and whether a true crossing occurred
- Permits unblinding only after both reviewers lock answers; interpretation uses uncertainty ranges and fixed practical criteria

**Inputs:** Static protocol; does not sample, render, read or generate human answers.

**Outputs:** Specifications for future manifests, blind pages and independent judgments; no execution.

**Usage:** Understand Q2's question, grouping, sampling and interpretation boundaries.

**Caution:** Q2 addresses shared recovery failures; Q3 addresses label reliability. Human confirmation establishes visual crossing and visibility evidence for the sampled events.

**Current SHA256:** `32d44f30c85e9163a457e23bd81ae8b15a4b54bc14a7d55780e68f7348e7a7a9`

## protocols/human_qc/q3_amendment86_v1.md

[Open file](../repository/protocols/human_qc/q3_amendment86_v1.md)

Narrow the base Q3 design to an executable material-production contract for 01/02 development inputs.

- At most 18 confirmed, 4 unconfirmed and 4 no-event windows; targeted U layer disabled
- Excludes by Q2 event_id only, without reading groups or answers
- Fixes field mapping, sampling API, seeds and window semantics
- Freezes default +/-2-second and expanded +/-5-second clips, with a static target hint after the first complete viewing
- Specifies time budgets, agreement denominators, e/u identification scope and material limits

**Inputs:** Static protocol; does not sample, render, read or generate human answers.

**Outputs:** Future material manifests, pages, rendering ledgers and statistical specifications; no human judgments.

**Usage:** Understand historical Q3 template fields, viewing gates and administrative status.

**Caution:** The packaged chain ends at #87; use the separate current 93-item Q3_v2 package and #111 additions. Material READY records preparation status. Human QC has its own completion gate. Distinguish the 26-item maximum, 23 actual items and later 77-item batch.

**Current SHA256:** `f97b0573332a1473550fcd5b18c1d864a12042ddcf2785edd5059471bc62a3d5`

## protocols/human_qc/q3_amendment87_v1.md

[Open file](../repository/protocols/human_qc/q3_amendment87_v1.md)

Register expansion and merging rules for the old Q3 batch while declaring that no answers had yet been entered.

- Retains 23 old items and adds 54 confirmed items, totaling 77: 72 confirmed, 4 unconfirmed and 1 search window
- Nine confirmed items in each of eight strata, a fixed expansion seed and new orders for two reviewers
- References old materials unchanged, keeps the template and isolates batches
- Estimates workload and preserves unknown/incomplete states
- Restricts zero-error binomial planning references and a stratified without-replacement bound for the 644-item population

**Inputs:** Static protocol; does not sample, render, read or generate human answers.

**Outputs:** Preregistered specifications for the old 77-item batch; no sampling or human-result computation.

**Usage:** Explain the historical 77-item figure in review/README and the #86-to-#87 expansion.

**Caution:** The packaged chain ends at #87; the current 93-item Q3_v2 and #111 additions are separate. The old confirmed-sample denominator is 72 of 77 items. Applying the zero-error bound requires resolution of all unknowns under the protocol.

**Current SHA256:** `5078265dccd8edae8f335bb4701022285ee02d2e3c89fd95e18fd565825f5058`

## protocols/human_qc/q3_protocol_v1.md

[Open file](../repository/protocols/human_qc/q3_protocol_v1.md)

Define the initial design for independent two-person review of derived crossing labels.

- Initial plan of at most 120 items and 180 minutes per reviewer
- Confirmed-event, unconfirmed-transition and no-event-window populations and seeds
- Questions about crossing, direction, identity, time interval and supporting frames
- Blind prompts, 60-second budget and distinct unreviewed, technical-failure and visually uncertain states
- Sampling weights, agreement/kappa, disagreements and versioned correction rules

**Inputs:** Static protocol; does not sample, render, read or generate human answers.

**Outputs:** Sampling and human-review specifications inherited by later versions.

**Usage:** Read the basic concepts, then follow explicit overrides through v2, #86 and #87.

**Caution:** The packaged chain ends at #87; #111 additions are outside this repository. Use the separate current 93-item Q3_v2 formal package. MOT17, HT21 and 03/05 appear as early future plans.

**Current SHA256:** `77439ad9f601fa5bb591dd5a757fc3cae3487888e0ad350ddd77add46dc5fdb6`

## protocols/human_qc/q3_protocol_v2_78d.md

[Open file](../repository/protocols/human_qc/q3_protocol_v2_78d.md)

Add targeted review of E1 unknown categories to Q3 while accounting for it separately from probability sampling.

- Reduces the confirmed probability-sample quota from 96 to 84 to reserve 12 U slots
- Six U codes, 01/02 slot allocation, fixed choice API and stable sorting
- Merges duplicate events for display while retaining selection routes
- Asks only about visual support for reference events, not hidden system correspondences
- Distinguishes DOCUMENTS_READY, SAMPLING_READY and CONFIRMATION_READY

**Inputs:** Static protocol; does not sample, render, read or generate human answers.

**Outputs:** Explicit amendments to v1; does not generate U samples.

**Usage:** Study the early U-layer design and its relationship to later #86 restrictions.

**Caution:** The packaged chain ends at #87. The current 93-item Q3_v2 and #111 additions are separate packages. #86 disables U slots for that round; the 12 slots remain an early plan. The filename v2 identifies this historical protocol revision.

**Current SHA256:** `581279bfd8445f15236caea64bf3da25afd45f376c8c8e007d5584c94d3b90f1`

## README.md

[Open file](../repository/README.md)

Introduce the research question, metrics, shortest usage path and reading order.

- Explains detection, tracking, region transitions, IVR, precision and visibility
- Provides CPU self-check, label reconstruction, standard-track scoring and inspection examples
- Distinguishes the standard-track interface from native v11 and lists reading entry points and unfinished work

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Read this first, then follow PIPELINE, RESULTS or DATA for your purpose.

**Caution:** Read its status as a delivery-time snapshot and use the guide status note for the later approved zip and current Q3_v2. Events represent rule-based region transitions; finite-line intersection and human confirmation require separate evidence.

**Current SHA256:** `7772974d56df8eb3aaae81b7b409f82c2f64d2a5b50d397c7129dc754d86aa08`

## requirements-cpu.txt

[Open file](../repository/requirements-cpu.txt)

Pin the Python package dependency for the minimal CPU path.

- Pins only numpy==2.2.6
- Comments name CPython 3.10.18 as the reference
- Requires the user to install explicitly in their own environment

**Inputs:** A pip requirements reader.

**Outputs:** Configures NumPy if the user installs it.

**Usage:** Use when preparing the minimal CPU environment; this guide did not install it.

**Caution:** Prepare Python separately. Pillow and full GPU/tracking dependencies belong to additional environments.

**Current SHA256:** `04376ba6be5561ddf59d1accc1736be6e70c82eb2f4093854a96485f8b78de08`

## RESULTS.md

[Open file](../repository/RESULTS.md)

Collect transcribed research tables with a stated evidence level for each table.

- Development identity-crossing and frame-level tracking tables
- Aggregate stadium rule-pairing summary
- E1 automatic attribution and E2 fixed-deletion summaries
- 03/05 confirmation tables, frozen integer criteria H-A/H-B and disclosures

**Inputs:** Historical writing tables and recomputation-receipt summaries identified in the source ledger.

**Outputs:** Static tables; no metric recomputation.

**Usage:** Read each table's provenance and limitations alongside its numbers.

**Caution:** These tables preserve historical transcriptions. Interpret each with its own event or frame denominator, dataset, evidence level and per-sequence decision rule; pooled values provide descriptions.

**Current SHA256:** `ffce18fe1589394bff63b131470d2dfbe6b43c6d03e5b9feb215f59472110898`

## review/q2/r15e30_blind_review_template.html

[Open file](../repository/review/q2/r15e30_blind_review_template.html)

Provide an empty local-browser interface for Q2's three blind visual judgments.

- The dataset defaults to an empty list and validateData refuses to start
- Public-field allowlist, anonymous IDs and local-video path checks
- Playback, frame stepping, reference time, zoom and pan
- No default answers for before_visible, after_visible or crossed
- Saves by batch/reviewer code, backs up before edits and imports/exports the same code

**Inputs:** A valid public manifest injected into id=dataset by an organizer; later independent human answers.

**Outputs:** Local browser answers and pre-edit records, with manual JSON export.

**Usage:** Use for Q2 after populating the public manifest under its original schema; this guide only read its source.

**Caution:** Populate formal items through the public schema and keep private group mappings in the research-side allocation file. Reviewer codes separate records; authentication and real-video playback require their own checks.

**Current SHA256:** `2d37c49dc6ab99e24af2a5846add601c0c64db311e8fd55726e7641e5e9f1612`

## review/q2/r15e30_blind_review_template_check.js

[Open file](../repository/review/q2/r15e30_blind_review_template_check.js)

Check Q2 template validation rules using synthetic manifests and answers.

- Reads HTML scripts and extracts validation functions through a VM
- Checks valid synthetic manifests, empty templates, duplicate IDs, private fields and video paths
- Checks reviewer/batch mismatches, invalid answers, unknown items and versions
- Statically rejects network-send APIs and reports the template SHA and 19 checks

**Inputs:** The adjacent empty template and internally constructed synthetic data.

**Outputs:** Console PASS summary or an error exit; no real answers are written.

**Usage:** Developers can check the Q2 template with Node; not executed for this guide.

**Caution:** These VM checks cover validation logic. Real-browser playback, localStorage acceptance and human QC have separate validation steps.

**Current SHA256:** `40f7d7febbfdd8ad8b49cbe7de804a8c988e768c200ff93054c8c256e9a07364`

## review/q3/review_template.html

[Open file](../repository/review/q3/review_template.html)

Provide the historical local Q3 development-review interface, separating target review from no-event-window search.

- __PUBLIC_ITEMS_JSON__ placeholder; QC86Core restricts public fields, protocol SHA and identical item sets for both reviewers
- No visual default answers for four target questions, search candidates, intervals or support frames
- Static target hints may be loaded manually only after natural full playback of the main clip
- 60 seconds per item and 120 minutes per session; technical failure, unlocated targets and incomplete viewing are separate states
- Saves by manifest digest and reviewer code; locking prevents import overwrite or timer reset

**Inputs:** A legally populated public manifest and local media from an organizer; later independent human answers.

**Outputs:** Local state, pre-edit records and user-downloaded JSON backups.

**Usage:** Understand #86/#87 interface logic or organize materials under the same protocol contract.

**Caution:** The packaged chain ends at #87; current Q3_v2 contains 93 items in a separate formal package, with #111 additions elsewhere. Replace the placeholder before formal use, retain uncertain labels, and export backups for cross-device preservation.

**Current SHA256:** `b19fe6125b7a1847315a35dbdc9e1da01750ffafc5fd548772354c155128a97c`

## review/q3/synthetic_ui_test.js

[Open file](../repository/review/q3/synthetic_ui_test.js)

Check Q3 template validation and interaction states with fully synthetic data and a simulated DOM.

- Three invented target, search and unlocatable items
- Simulated DOM driver loading the template core and original UI script
- 29 checks cover hint gating, timing, locking, save failures, imports, technical states and interval submission
- Records script/template/fixture hashes, Node version and check scope

**Inputs:** An output path containing synthetic; reads the adjacent template and uses in-script synthetic fixtures.

**Outputs:** result.json or failure.json in the output directory and a console summary.

**Usage:** Check historical Q3 template behavior during development; not executed for this guide.

**Caution:** The script accepts paths containing synthetic and may create directories recursively. Follow the stricter README recommendation of a new external directory. Its scope is simulated interaction; real media playback and human storage have separate validation.

**Current SHA256:** `f20ad8883a4be1b7817200771b7f8f64c297e2f6b1770739c5fe7c1749332e27`

## review/README.md

[Open file](../repository/review/README.md)

Explain that the delivery contains Q2/Q3 protocols and empty interfaces, and distinguish the two review tasks.

- Q2 checks visual evidence for remaining unrecovered events; Q3 checks reference-label support
- Describes the historical 77-item batch while stating that this directory contains no media or answers
- Explains template injection and protocol precedence
- Covers local saving, independent devices/materials, backups and synthetic-check limits

**Inputs:** Reading guidance; receives no answers.

**Outputs:** No pages or results.

**Usage:** Read first when entering the review directory.

**Caution:** The packaged chain ends at #87. Use the separate current 93-item Q3_v2 package and #111 additions. The 77-item figure records historical material production; current package size and completed human reviews have separate counts.

**Current SHA256:** `3a0b6db91a04f5873868cc35588e8ff57de4477cd95492e96d6a259e7dd11cdd`

## scripts/analysis.py

[Open file](../repository/scripts/analysis.py)

Expose a short repository-root entry point for frozen analysis primitives.

- Adds the repository root to sys.path
- Imports src.analysis.cli.main
- Returns main's exit code when run as a script

**Inputs:** The underlying CLI receives ACTION, --input and --out.

**Outputs:** The underlying CLI writes the selected analysis JSON.

**Usage:** Use for explicit-input actions such as e2-mask, d1-gaps and headgate-project.

**Caution:** The underlying CLI implements the algorithms. Each primitive covers its specified operation within a historical experiment.

**Current SHA256:** `e6d8c4bb1a451f83f5106a1f770f61ac07a0e33cee58e4c59a6ab86bf2d06988`

## scripts/confirm.py

[Open file](../repository/scripts/confirm.py)

Expose the confirmation-control command generator as an outer script.

- Repository-root import adaptation
- Delegation to src.confirm.cli.main
- Docstring emphasizes command generation only

**Inputs:** The underlying CLI receives an external workspace, manifest/approval paths and SHA values, and output directory.

**Outputs:** The underlying CLI deploys control copies and creates command files.

**Usage:** Prepare an explicitly bound confirmation-control plan.

**Caution:** This entry point prepares command files. Scientific execution and reconfirmation require their corresponding explicit authorization and receipts.

**Current SHA256:** `8b4230e4888677b688761c71df3953a1deeeaa6da5f7e8811489bf007462b141`

## scripts/detect.py

[Open file](../repository/scripts/detect.py)

Provide an outer command for detection from an explicit pixel manifest.

- Adds the repository root to the import path
- Delegates to src.detect.cli.main
- Notes that only the CLI is imported before explicit execution

**Inputs:** The underlying CLI receives --manifest and optional --out, --device and --execute.

**Outputs:** Preflight results, or detection cache and manifest after execution.

**Usage:** Use for the pixel-to-shared-YOLOX-cache stage.

**Caution:** This wrapper delegates to the detector CLI. Default preflight checks inputs; --execute requests actual inference.

**Current SHA256:** `bdd623fa551f3c5e774a6dd7338143d9960301b7642940e99c54bd6620c68f42`

## scripts/inspect_event.py

[Open file](../repository/scripts/inspect_event.py)

Call the frozen core's per-event evidence inspector from the outer repository.

- Imports only resource_entry.run
- Forwards to core/inspect_event.py
- States that local-image rendering requires an explicit request

**Inputs:** An event ID or missed-event list options, reference inputs, optional tracks and local images.

**Outputs:** The core produces event evidence and optional rendering.

**Usage:** Trace reference support, system matching and identity evidence.

**Caution:** Use core/inspect_saved_event.py for the separate saved-score inspection workflow.

**Current SHA256:** `461b23aa15f970afbb1904f1044ab28f862a9b53a4aa75c55655e6d6affd9190`

## scripts/native_v11.py

[Open file](../repository/scripts/native_v11.py)

Expose v11 generation that preserves original detection-footpoint semantics.

- Adds the repository root to the import path
- Delegates to src.track.native_v11.main
- States explicit development-only inputs and M4/native-event support

**Inputs:** The underlying CLI receives a native_v11 input manifest and explicit execution output path.

**Outputs:** Native frames, stitch, per-gate events and native_manifest.

**Usage:** Use when original detection footpoints and M4 event semantics are required.

**Caution:** Pair the generated events with score_native_v11.py for identity scoring. Standard-track decoding uses a separate event definition.

**Current SHA256:** `27dbbf4e0191701233667981363bdf3c64800401c4f8f7394e9e7e23ec3903b0`

## scripts/reproduce.py

[Open file](../repository/scripts/reproduce.py)

Call the frozen core's label-reconstruction and cache-regression entry point from the outer repository.

- Imports only resource_entry.run
- Passes the fixed reproduce.py entry name to the shared wrapper

**Inputs:** GT/seqinfo roots and new external output arguments forwarded through resource_entry to core.

**Outputs:** The core rebuilds labels and checks the cached example.

**Usage:** Use for the minimal CPU resource-reconstruction path.

**Caution:** This path reads the existing numerical cache. See core/reproduce.py for the reconstruction contract; detection and native tracking are separate stages.

**Current SHA256:** `ee785c381fbde184828bf36d75f1436cf72e1e500f524309d0ddba7c57622de1`

## scripts/resource_entry.py

[Open file](../repository/scripts/resource_entry.py)

Handle paths, output protection and isolated-process environments for three CPU core entry points.

- ENTRIES permits only reproduce, score_tracker and inspect_event
- Normalizes explicit paths and rejects abbreviated path arguments, repository-internal outputs and existing outputs
- Removes interfering Python environment variables, hides CUDA and fixes threads to 1
- Launches a new Python process from core to avoid collision between two src packages

**Inputs:** A fixed core entry name and CLI arguments.

**Outputs:** Subprocess return code; the core entry writes actual artifacts.

**Usage:** Shared by the three resource scripts; inspect it for their path contract.

**Caution:** The wrapper rejects -O to preserve frozen assertions. Prepare the required scientific dependencies separately from CPU environment settings.

**Current SHA256:** `f32240d6811f0acc7544ece589fb4d5cb8579414297f93ec2046153a93d542a6`

## scripts/run_resource_synthetic.py

[Open file](../repository/scripts/run_resource_synthetic.py)

Run two synthetic test groups for resource wrappers and the older core inspector in sequence.

- Rejects optimized Python
- Runs unittest discovery for tests/test_resource_adapters.py
- Runs core/tests/test_inspection_synthetic.py
- Inherits the CPU environment and returns immediately on a nonzero status

**Inputs:** An existing Python environment; no real-data arguments.

**Outputs:** Test logs and a success/failure exit code.

**Usage:** Check minimal resource adapters and legacy synthetic inspection behavior; not executed for this guide.

**Caution:** Coverage is limited to these two synthetic groups. Native scientific regression, GPU execution, human review and other repository tests have separate checks.

**Current SHA256:** `82b2ea8e95b90f027db09da8c020f8e5d5beadc4150698496ac561908d0c609c`

## scripts/score_native_v11.py

[Open file](../repository/scripts/score_native_v11.py)

Expose dedicated identity scoring for native final_events as an outer command.

- Adds the repository root to the import path
- Delegates to src.score.native_v11.main
- Comments explicitly exclude event redecoding and inference

**Inputs:** The underlying CLI receives 01/02 native-output directories, GT/seqinfo roots and optional --execute.

**Outputs:** Preflight results, or native-event identity scores and evidence.

**Usage:** Reconstruct identity associations and matching for saved native_v11 events.

**Caution:** This consumes native-event semantics. score_tracker.py consumes standard-track semantics. --execute requests scoring after preflight.

**Current SHA256:** `f8766dacab163f646996aaf7d7a1c5940136d91db684ef92451c13c50f5d8943`

## scripts/score_tracker.py

[Open file](../repository/scripts/score_tracker.py)

Call standard MOTChallenge-track scoring or panel self-checks from the outer repository.

- Imports only resource_entry.run
- Forwards to the fixed core/score_tracker.py entry

**Inputs:** Standard tracks or --self-test, GT/seqinfo roots and a new output path.

**Outputs:** The core generates track-derived events, scores and regression receipts.

**Usage:** Connect your own 01/02 tracks or check the three bundled panel references.

**Caution:** This interface derives events from track-box bottom-centres. Native v11 uses raw-detection footpoints through its dedicated interface.

**Current SHA256:** `caae85381addf2b68047e678ad9eb90a5153469d58c1f9ee573703c7ffa5238b`

## scripts/track.py

[Open file](../repository/scripts/track.py)

Provide a short command for adapting cached detections to three author trackers.

- Adds the repository root to the import path
- Delegates to src.track.cli.main
- Propagates downstream status through SystemExit

**Inputs:** The underlying CLI receives a cache directory, byte/oc/bot method, optional GMC and --execute.

**Outputs:** Preflight results, or MOT tracks, observation audit and track_manifest after execution.

**Usage:** Select a tracker panel after preparing the YOLOX cache.

**Caution:** Execution status comes from the downstream run. The lower layer checks the GMC contract required by bot.

**Current SHA256:** `80ed04d1b6384f8c368635969b64232e20f043353dc678e9ccec554c263811fa`

## scripts/verify_repository.py

[Open file](../repository/scripts/verify_repository.py)

Statically scan the delivery directory for manifest agreement, frozen hashes and obvious sensitive-content patterns.

- Enumerates files, computes SHA values, parses Python syntax and decompresses text
- Flags forbidden media/weights, absolute paths and specified identity tokens, with email findings separated for review
- Applies two narrow exceptions only at exact hashes
- Checks FROZEN_CODE_MAP and MANIFEST and writes a new external audit report

**Inputs:** A new external --report JSON path and repeatable --forbid-token arguments.

**Outputs:** JSON report of per-file hashes, findings, exceptions and check counts, plus exit status.

**Usage:** Check delivery integrity before release; this guide read the source without running the auditor.

**Caution:** This auditor checks packaged text and compressed data using fixed patterns. Broader privacy review and scientific-result validation require separate evidence.

**Current SHA256:** `fff122a42e44159dbddaaabda2c0a30843a664a5cc94be3acc0742d00e18b232`

## src/analysis/cli.py

[Open file](../repository/src/analysis/cli.py)

Modern adapter connecting explicit JSON inputs to frozen analysis functions.

- Dispatches E1 attribution, E2 deletion masks, and D1 gap analysis
- Integrates HeadGate projection, GateLink, M4, and ReID rule fragments
- Checks development-set scope and a new output path before writing JSON

**Inputs:** action, --input JSON, --out

**Outputs:** Analysis-result JSON for the selected action

**Usage:** Scripts call main; start here to understand the available analyses

**Caution:** MOT20-01/02 only; oracle and descriptive results provide evidence classifications, with causal and performance claims requiring separate validation.

**Current SHA256:** `6c336bc8edd97659df5efdb363582d86aac02d887a12d77307f97d87ac082a4a`

## src/analysis/fragments/r15_reid93_analysis__decision.py

[Open file](../repository/src/analysis/fragments/r15_reid93_analysis__decision.py)

Retained legacy ReID fragment that decides whether to retain a candidate using exact counts.

- Checks overall and per-sequence high-visibility and precision floors
- Assigns a decision tier from the increase in low-visibility correct counts
- Includes exact fractions and the rule hash

**Inputs:** Aggregated report

**Outputs:** decision, check details, thresholds, and recomputation-pending status

**Usage:** Assembled by fragment_namespace for reid-decision

**Caution:** Requires Fraction, fraction_value, and RULES_SHA in the assembled namespace; decisions follow exact-count rules, with statistical significance outside their scope.

**Current SHA256:** `04a62fbe57c0e66f2760b1974abfe5d5718c6671bc3bd67126e51f55dd69f5fe`

## src/analysis/fragments/r15_reid93_analysis__fraction_value.py

[Open file](../repository/src/analysis/fragments/r15_reid93_analysis__fraction_value.py)

Retained legacy function fragment converting counts to exact rational and decimal values.

- Returns None when the denominator is zero
- Preserves numerator, denominator, exact string, and floating-point value

**Inputs:** Numerator n and denominator d

**Outputs:** Fraction dictionary or None

**Usage:** Populates precision fields in the ReID decision fragment

**Caution:** Depends on Fraction in the assembled namespace; operates on supplied counts.

**Current SHA256:** `d0000687a9ab417867b83187bf05e16fa82b52f564089e9548b41d284e6b67a8`

## src/analysis/fragments/r15_reid93_analysis__RULES_SHA.py

[Open file](../repository/src/analysis/fragments/r15_reid93_analysis__RULES_SHA.py)

Constant fragment fixing the source hash of the ReID decision rules.

- Defines only the complete SHA256 constant
- Records the rule version used in decision results

**Inputs:** No runtime input

**Outputs:** RULES_SHA string

**Usage:** Assembled with the ReID functions by fragment_namespace

**Caution:** Source-binding constant identifying the rules used.

**Current SHA256:** `139115c4ed43682eeae22840bf20339af73b65a82b0765c2abbc34ffede095c4`

## src/analysis/fragments/r15_reid93_analysis__sidecat.py

[Open file](../repository/src/analysis/fragments/r15_reid93_analysis__sidecat.py)

Retained legacy fragment classifying whether support frames exist before and after an event.

- Reads source/target spatial-region frame counts
- Returns both, before_only, after_only, or neither

**Inputs:** One support dictionary

**Outputs:** One support category

**Usage:** Called in batches by the reid-support adapter action

**Caution:** Describes the presence of evidence on either side while preserving existing identity assignments.

**Current SHA256:** `fa673ac1ff0eaa8da099e9e41c90c31660ca1de50427d8fa5ef654063a92e1c2`

## src/analysis/frozen/r15e27_headgate_inference.py

[Open file](../repository/src/analysis/frozen/r15e27_headgate_inference.py)

Frozen streaming integration projecting HeadGate head boxes into tracking events.

- Loads the head detector lazily and retains raw detections
- Explicitly selects the head anchor and frozen projection
- Connects MOT and stadium event engines

**Inputs:** Full native frame stream, detections, metadata, frozen calibration, and externally constructed executors

**Outputs:** Detections, tracking points, events, and audit metadata

**Usage:** headgate-project uses HeadProjection; HeadGateInference.run handles complete streams

**Caution:** The stadium head-box center is an uncalibrated proxy. Validation covers synthetic cases; real-detector and held-out performance require separate evidence.

**Current SHA256:** `eb9f0ea5b265eb19e2aac416fcb26ee4176af9bcbe3ea18aa5f4f412ce6255a3`

## src/analysis/frozen/r15e28_e1_core78a_v2.py

[Open file](../repository/src/analysis/frozen/r15e28_e1_core78a_v2.py)

Frozen E1 computations for detection support, identity matching, and event-failure attribution.

- Builds raw-detection and output-box pools and checks their mapping
- Performs one-to-one matching, track segmentation, and event matching
- Uses a fixed priority to distinguish recovery, unknown identity, missing detections, and linking/decoding problems

**Inputs:** In-memory detections, output boxes, GT support, and an external exact solver

**Outputs:** Match records, evidence pools, attribution categories, and details

**Usage:** Pure functions used by analysis and scoring adapters

**Caution:** Operates in memory and classifies evidence. Causal interpretation requires separate evidence; the caller validates and supplies the solver.

**Current SHA256:** `d6342df4fa8befca129d02124030e05205e6fb80a9e2f6c753a6782615aee11b`

## src/analysis/frozen/r15e28_e2_masks.py

[Open file](../repository/src/analysis/frozen/r15e28_e2_masks.py)

Frozen candidate implementation of E2 observation deletion under the protocol.

- Splits segments at identity, visibility changes, and frame gaps
- Generates iid/block deletion with exact retention ratios and fixed seeds
- Constructs one baseline and 24 degraded conditions

**Inputs:** Observation records, retention ratio, seed, mode, and original frame rate

**Outputs:** Immutable retained/deleted records and segment statistics

**Usage:** The e2-mask action or make_grid produces controlled missing-input conditions

**Caution:** Marked synthetic-validated candidate; scope is observation masking. GT validity, tracking, and I/O are handled separately.

**Current SHA256:** `f323aa2dda434f02aa46f0a36636d033c0719455c8b3fb6cb9f0a6e111b41887`

## src/analysis/frozen/r15e29_gap_core81.py

[Open file](../repository/src/analysis/frozen/r15e29_gap_core81.py)

Frozen D1 descriptive statistics for observation gaps within the same track ID.

- Distinguishes endpoint time differences from genuinely missing frame counts
- Evaluates rectangular regions, gap direction, and temporal compatibility
- Bins gaps by duration and includes synthetic self-checks

**Inputs:** Observation timelines by track ID, fps, and gate-line geometry

**Outputs:** Gap list, direction, and temporal/distance descriptions

**Usage:** The d1-gaps action calls gaps

**Caution:** Describes gaps within IDs and preserves existing event results; duplicate or non-increasing frames within an ID raise errors.

**Current SHA256:** `4049fc3528b2ca6e22a66861e17f0b3369c93b77e8d75f449ccb8b211d2b1c41`

## src/analysis/frozen/r15e32_gatelink_oracle.py

[Open file](../repository/src/analysis/frozen/r15e32_gatelink_oracle.py)

Retained GateLink oracle comparator linking tracks with ground-truth identities.

- Linearly interpolates boxes within same-ID gaps
- Links different IDs using identity votes at track endpoints
- Retains fixed development paths and transformation logs in the legacy main

**Inputs:** MOT-format rows, valid identity mapping, and maximum gap G

**Outputs:** Bridged/linked rows and counts of added rows and links

**Usage:** The portable analysis entry point calls only bridge_same_id/oracle_link

**Caution:** oracle_link uses GT identities as an oracle comparator; the legacy main contains historical I/O paths.

**Current SHA256:** `715d389d58907c3be5ad2a38025e6f4b0aae902fab3c63138f76812a7fb80c51`

## src/confirm/cli.py

[Open file](../repository/src/confirm/cli.py)

Deploys frozen confirmation-control code to an external workspace and generates commands only.

- Checks the external deployment path and symbolic links/reparse points
- Copies verified production_v1 files byte for byte
- Calls the original command generator without starting workers

**Inputs:** External workspace, manifest/approval paths and hashes, and out

**Outputs:** External control code, commands.json, and command text

**Usage:** Use generate_workspace during confirmation preparation

**Caution:** Scope is preparation and command generation. Execution requires separate authorization; approval contents and scientific assets remain unopened.

**Current SHA256:** `89f7b22ffad95b3141832788ce52fdbe4616dab90b4d99c4b670645490728e91`

## src/confirm/production_v1/command.py

[Open file](../repository/src/confirm/production_v1/command.py)

Frozen control-layer utility generating bound commands or collecting receipts for completed units.

- Statically checks local worker functions and source bindings
- Generates complete stage-by-stage PowerShell commands
- Validates and aggregates completion receipts into a fixed handoff index

**Inputs:** Explicit manifest, hashes, and approval references; collection also requires authorized control information

**Outputs:** commands.json, commands.ps1, or all_units.json

**Usage:** Called by confirmation-adapter generate; collect_receipts supports stage handoff

**Caution:** Generation prepares commands; detection, tracking, and scoring occur in their execution stages. Receipt collection requires separately authorized control inputs.

**Current SHA256:** `c20c195c94461dd5d5ca50ccfe6596187df5d97a6f8c389eb358de5843b6cdc5`

## src/confirm/production_v1/manifest.py

[Open file](../repository/src/confirm/production_v1/manifest.py)

Frozen confirmation-control layer checking scope, file bindings, resource limits, and read/write receipts.

- Defines stages, seven systems, and development/confirmation sequence scopes
- Validates manifest, approval, freeze, interpreter, and paths
- Uses Ctx for controlled reads/writes and complete/fail records

**Inputs:** Bound manifest, approval, freeze, Request, and resource configuration

**Outputs:** Controlled execution context, read/write ledger, and completion or failure receipts

**Usage:** Shared control foundation for production_v1/run.py and the receipt collector

**Caution:** An approval hash establishes content binding. Human consent and data-read authorization are separate requirements from hashes and runtime-library registration.

**Current SHA256:** `6dcd47c32132a3306cc3fae4e2078ef8aa4a550cec8e4fec727c4e1128b016a9`

## src/confirm/production_v1/reference_score.py

[Open file](../repository/src/confirm/production_v1/reference_score.py)

Frozen confirmation adapter for legacy reference import, full-panel sealing, and E1-v2 scoring.

- Imports explicitly selected P2/O1 references unchanged
- Checks 14 completed units across seven systems and two sequences
- Recomputes identities from actual output boxes and applies per-sequence decision rules

**Inputs:** Controlled context, completed-unit/seal references, and bound reference/scoring assets

**Outputs:** Reference copies, seal.json, scores.json, and scoring audit

**Usage:** The import_reference, seal, and score stages of run.py

**Caution:** The I/O wrapper has a separate held-out regression requirement. Aggregate results are descriptive; confirmation decisions require each sequence to pass.

**Current SHA256:** `0d31ea79f9cdaa1de48c6e3926243e82db30a51aa68c73a77de6eecc491931f1`

## src/confirm/production_v1/run.py

[Open file](../repository/src/confirm/production_v1/run.py)

Single-stage dispatch entry point for the frozen control layer.

- Parses export/consume/import/seal/score requests
- Validates the complete local code closure before loading a worker
- Claims a resource slot and releases it after recording completion or failure

**Inputs:** Stage, sequence/system, control-file hashes, and handoff/seal references

**Outputs:** Technical stage receipts or STOP errors

**Usage:** Run commands generated by command.py after external authorization

**Caution:** Confirmation-set execution requires external authorization. Missing approval, hashes, resources, or workers stop execution.

**Current SHA256:** `92d984db1da5cb7e1bb43f9cb2445b7231715d41f9bbb633c19de957fe345625`

## src/confirm/production_v1/workers.py

[Open file](../repository/src/confirm/production_v1/workers.py)

Frozen production orchestration connecting explicit assets to original detection, tracking, and event code.

- Loads selected AST fragments or pure modules after hash verification
- Shares one YOLOX export and independently resets each CPU consumer
- Handles native v11 events and panel output boxes separately, writing audits and handoff records

**Inputs:** Ctx, Request, and bound images/cache/geometry/G1/policy/parameter assets

**Outputs:** Detection cache, track/event files, source audit, and stage-handoff receipts

**Usage:** production_v1/run.py calls export_yolox or consume

**Caution:** Orchestration preserves scientific arithmetic; workers consume non-GT assets. Development regression and confirmation authorization have separate evidence requirements.

**Current SHA256:** `ee6b25265e4711577c8e5d4cdd1f162a8b582e25d14428fa158f5b41a3938110`

## src/detect/cli.py

[Open file](../repository/src/detect/cli.py)

Modern entry point exporting frozen YOLOX detections from an explicit per-image manifest.

- Validates only the manifest and development sequences by default
- Checks local weights and every original-image binding during execution
- Saves native-coordinate detections and a cache manifest frame by frame

**Inputs:** Pixel manifest; execution requires --out, --execute, and local runtime dependencies

**Outputs:** detections.jsonl.gz, cache_manifest.json, or validation-only status

**Usage:** Detection-stage entry point producing caches for downstream tracking

**Caution:** Development 01/02 only; uses the specified local model and weights. Bitwise reproduction requires separate evidence.

**Current SHA256:** `34bfd168bb4b766987e520a95128fd2614d2091fe2d8c0525ef50ceeb104b134`

## src/detect/frozen/r15_yolox82e_detector.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_detector.py)

Frozen adapter dedicated to the YOLOX-X/MOT17 detector.

- Builds the specified one-class network and strictly verifies weights
- Loads and fuses in FP32 before converting to half precision
- Preprocesses, applies NMS, and restores native xyxy coordinates

**Inputs:** Locally bound weights, device, and native BGR images

**Outputs:** YOLOX82EDetector and per-frame boxes/scores/classes/metadata

**Usage:** Used by detect.cli.export on explicit execution

**Caution:** Detection adapter with lazy Torch, weight, and CUDA loading; preserves the existing detector implementation.

**Current SHA256:** `2167c6bb02ccb240b479da85ef3e3fd55d9dcb4c6945e32c413b439b1ea1da76`

## src/detect/frozen/r15_yolox82e_vendor/__init__.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/__init__.py)

Lightweight initializer marking the private third-party detection-source package.

- Contains only a package docstring
- Explicitly states that import performs no initialization

**Inputs:** Python package import

**Outputs:** Package namespace

**Usage:** Used when importing the private YOLOX dependency closure

**Caution:** Package namespace initialization only; model, weight, and data loading occur elsewhere.

**Current SHA256:** `402926cb779b3db7eebe40e74d58b9188589f07897b06339327de675b86e599b`

## src/detect/frozen/r15_yolox82e_vendor/fusion.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/fusion.py)

Convolution and batch-normalization fusion functions extracted from upstream ByteTrack/YOLOX.

- Combines Conv and BatchNorm parameters
- Traverses the model and replaces BaseConv with its fused forward

**Inputs:** PyTorch convolution/BN layers or a model

**Outputs:** Fused convolution layer or model

**Usage:** Author-implemented fusion step in frozen detector loading

**Caution:** Upstream mathematical-function fragments retaining Megvii copyright.

**Current SHA256:** `109e9f9c5926c9753db1c0281038fb64816834e0fa9fd49c35b30a9ab2908be4`

## src/detect/frozen/r15_yolox82e_vendor/LICENSE.ByteTrack

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/LICENSE.ByteTrack)

Complete upstream MIT license retained with the detector vendor code.

- Includes the 2021 Yifu Zhang copyright notice
- Includes notice-retention conditions and the warranty disclaimer

**Inputs:** Human reading

**Outputs:** License text

**Usage:** Retain when distributing or reviewing ByteTrack-derived code

**Caution:** Defines the code license; model-weight licensing requires its own source.

**Current SHA256:** `e9d83751678cbaba6dfba902ea39215c423d93425e58f8450d6001f7261696f9`

## src/detect/frozen/r15_yolox82e_vendor/models/__init__.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/models/__init__.py)

Initializer marking the private model subpackage while avoiding upstream package initialization.

- Contains only a docstring
- States that model modules are imported explicitly

**Inputs:** Python package import

**Outputs:** Model-package namespace

**Usage:** Used when the frozen detector imports network modules on demand

**Caution:** Package namespace initialization; model construction and weight loading are handled by the detector.

**Current SHA256:** `59e4fb820ceff218276790e7c7784bb71ec0ab032118e4426333b9c854aa920a`

## src/detect/frozen/r15_yolox82e_vendor/models/darknet.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/models/darknet.py)

Retained upstream Darknet/CSPDarknet feature-extraction backbone.

- Builds hierarchical convolution, residual, and CSP layers
- forward returns features at the requested levels

**Inputs:** Image tensors and architecture parameters

**Outputs:** Multiscale backbone features

**Usage:** YOLOPAFPN internally uses CSPDarknet

**Caution:** Frozen third-party implementation requiring PyTorch.

**Current SHA256:** `37fd32ae7f7de29df646f7c457837834fcc0e4e08ce83034a6397092fbae6a62`

## src/detect/frozen/r15_yolox82e_vendor/models/losses.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/models/losses.py)

IoU and focal-loss implementations retained with the upstream model.

- Provides IoU/GIoU box losses
- Provides sigmoid focal loss

**Inputs:** Prediction tensors, target tensors, and loss parameters

**Outputs:** Loss tensors

**Usage:** Dependencies of the upstream training branch in YOLOXHead

**Caution:** Training code is retained for provenance completeness; NOTICE authorizes eval forward only. Training claims require separate execution evidence.

**Current SHA256:** `e4644f138ddb8658cc26a03e5d80bb0fcd4e91bb8b0085d695958aafd47a031e`

## src/detect/frozen/r15_yolox82e_vendor/models/network_blocks.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/models/network_blocks.py)

Retained basic building blocks of the upstream YOLOX network.

- Provides activations, standard/depthwise convolutions, and bottlenecks
- Includes residual, SPP, CSP, and Focus blocks
- Provides fused-convolution forward

**Inputs:** Tensors and layer-channel/convolution configurations

**Outputs:** Transformed feature tensors

**Usage:** Shared dependencies of Darknet, PAFPN, and the detection head

**Caution:** Third-party network components retained from upstream YOLOX.

**Current SHA256:** `250982431c53a5ed49c3e465266baeabe3e21a41eac941a8e5345c2e71e14a7d`

## src/detect/frozen/r15_yolox82e_vendor/models/yolo_head.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/models/yolo_head.py)

Retained upstream YOLOX multiscale classification, regression, and confidence head.

- Builds classification/regression branches and decodes grid outputs
- Retains bias initialization and training losses
- Retains dynamic-K label-assignment methods

**Inputs:** Multiscale features; the training branch also takes targets

**Outputs:** Inference detection tensors; the retained training branch can return losses

**Usage:** The YOLOX model calls YOLOXHead.forward

**Caution:** Frozen third-party head; the release adapter uses eval inference only.

**Current SHA256:** `c2e3a95d0c7980d6d27b0a8a58fc16a6a058630d3ac569830f823ff2566435dc`

## src/detect/frozen/r15_yolox82e_vendor/models/yolo_pafpn.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/models/yolo_pafpn.py)

Retained upstream YOLOX feature-pyramid fusion network.

- Calls CSPDarknet for feature extraction
- Fuses scales with upsampling, concatenation, and downsampling

**Inputs:** Image/feature tensors and channel-structure parameters

**Outputs:** Three levels of fused features

**Usage:** Default backbone component of YOLOX

**Caution:** Third-party feature-fusion implementation retained from upstream YOLOX.

**Current SHA256:** `bfeb522c87fc076659c804927751b503ef0185fe1cf8f9f7153369e9177a9627`

## src/detect/frozen/r15_yolox82e_vendor/models/yolox.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/models/yolox.py)

Retained model class connecting the upstream backbone and head into complete YOLOX.

- Combines YOLOPAFPN and YOLOXHead by default
- Dispatches inference results or losses according to training state

**Inputs:** Image tensors and optional training targets

**Outputs:** Detection tensors or an upstream training-loss dictionary

**Usage:** Used by build_model to construct the frozen network

**Caution:** Complete upstream model wrapper; this documentation task performed static inspection only.

**Current SHA256:** `a4d70f5ef75dfbb1da5394d886dc348c68cdfbb27ab725f36c313e981ba605ee`

## src/detect/frozen/r15_yolox82e_vendor/NOTICE.md

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/NOTICE.md)

Documents upstream provenance, license, and usage boundaries for the private YOLOX source copy.

- Identifies the FoundationVision/ByteTrack commit
- Documents retained copyright, two relocated imports, and unchanged mathematics
- States that training methods are retained but only eval forward is authorized

**Inputs:** Human reading

**Outputs:** Provenance and scope notes

**Usage:** Read when reviewing third-party provenance, preparing distribution, or understanding vendor boundaries

**Caution:** Documents source-code provenance and scope; model-weight licensing requires its own source.

**Current SHA256:** `b2035cb6031091837e5ab27b29d2023cc827b5069ddab68185703c992e40cdf5`

## src/detect/frozen/r15_yolox82e_vendor/postprocess.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/postprocess.py)

YOLOX postprocessing and box-overlap functions extracted from upstream.

- Converts center/size predictions to corner coordinates
- Filters by object/class confidence and performs class-aware NMS
- Provides tensor box IoU

**Inputs:** Model prediction tensors, class count, and thresholds

**Outputs:** Filtered detection lists or an IoU matrix

**Usage:** Dependencies of frozen detector inference and retained detection-head code

**Caution:** Postprocessing function fragments retained from upstream YOLOX.

**Current SHA256:** `669a6ae0a256c661ab824a8e4acbe855fdc0da16957aeb342a9418fee6b352c7`

## src/detect/frozen/r15_yolox82e_vendor/preprocess.py

[Open file](../repository/src/detect/frozen/r15_yolox82e_vendor/preprocess.py)

YOLOX image resizing, padding, and normalization function extracted from upstream.

- Resizes with aspect ratio preserved and pads with 114
- Converts channels, normalizes by mean/std, and permutes axes

**Inputs:** Image, input_size, mean, std, and swap

**Outputs:** Preprocessed image and resize ratio

**Usage:** Called by YOLOX82EDetector.predict_bgr

**Caution:** Frozen upstream function; preprocessing conventions must match the local weights.

**Current SHA256:** `822960b3dceda2f213719055b8b0f4a409f36a1ed157b7dddcf95fb2f17ddda6`

## src/detect/io.py

[Open file](../repository/src/detect/io.py)

Shared utilities for explicit inputs, source verification, and output isolation in portable entry points.

- Verifies relative paths, byte lengths, and SHA256 bindings
- Verifies frozen files against the ledger and assembles physical source fragments
- Restricts development scope, blocks networking/subprocesses, and isolates runtime caches

**Inputs:** Manifest paths/bindings, frozen-source prefixes, and new output paths

**Outputs:** Verified files/modules/namespaces and JSON outputs

**Usage:** Shared by detect, track, analysis, confirm, and other entry points

**Caution:** Frozen assertions must remain enabled; -O/-OO are rejected. Runtime outputs must use new paths outside the repository.

**Current SHA256:** `7ba6518ce644d2d271b9bd97ee367d839793f31d0fca92c2ed5fcb3a21a8c5ba`

## src/events/__init__.py

[Open file](../repository/src/events/__init__.py)

Exports an entry point deriving events from MOTChallenge tracks and scoring them with the frozen scorer.

- Defines a lazily importing main
- Forwards arguments to score_tracker.py through scripts.resource_entry.run

**Inputs:** Command-line arguments argv

**Outputs:** Return value/output from the delegated resource entry point

**Usage:** Used by python -m src.events or a direct main call

**Caution:** Forwarding layer; the scientific logic is in the frozen resource entry point.

**Current SHA256:** `9798e3af3d65f1d1adad684ea2414b74f79a646a2e8d6503f646e78cc016eeb4`

## src/events/__main__.py

[Open file](../repository/src/events/__main__.py)

Makes src.events runnable as a Python module.

- Imports main from the same package
- Uses the return value as the exit code under the __main__ guard

**Inputs:** Module-run arguments

**Outputs:** Process exit code and main output

**Usage:** Entered automatically by python -m src.events

**Caution:** Module-launch forwarding layer.

**Current SHA256:** `eaa037077d4d9638155389dcbaf1d4c3804ec5c30fcaf63430ed3798f60869c9`

## src/inspect/__init__.py

[Open file](../repository/src/inspect/__init__.py)

Exports the frozen CPU entry point for inspecting support evidence for one event.

- Defines a lazily importing main
- Forwards arguments to inspect_event.py through scripts.resource_entry.run

**Inputs:** Command-line arguments argv

**Outputs:** Return value/output from the delegated resource entry point

**Usage:** Used by python -m src.inspect or a direct main call

**Caution:** Forwarding layer; the scientific logic is in the frozen resource entry point.

**Current SHA256:** `e54075994df7483a999417ad357c44f57ffeea7943dcbda86dd83baa693c0b14`

## src/inspect/__main__.py

[Open file](../repository/src/inspect/__main__.py)

Makes src.inspect runnable as a Python module.

- Imports main from the same package
- Uses the return value as the exit code under the __main__ guard

**Inputs:** Module-run arguments

**Outputs:** Process exit code and main output

**Usage:** Entered automatically by python -m src.inspect

**Caution:** Module-launch forwarding layer.

**Current SHA256:** `eaa037077d4d9638155389dcbaf1d4c3804ec5c30fcaf63430ed3798f60869c9`

## src/labels/__init__.py

[Open file](../repository/src/labels/__init__.py)

Exports entry points for frozen label reconstruction and cached-reference scoring.

- Defines a lazily importing main
- Forwards arguments to reproduce.py through scripts.resource_entry.run

**Inputs:** Command-line arguments argv

**Outputs:** Return value/output from the delegated resource entry point

**Usage:** Used by python -m src.labels or a direct main call

**Caution:** Forwarding layer; the scientific logic is in the frozen resource entry point.

**Current SHA256:** `254e2c30190369e9d884d697801f00bcc46bf9d3263fa50d0c96299da6b45863`

## src/labels/__main__.py

[Open file](../repository/src/labels/__main__.py)

Makes src.labels runnable as a Python module.

- Imports main from the same package
- Uses the return value as the exit code under the __main__ guard

**Inputs:** Module-run arguments

**Outputs:** Process exit code and main output

**Usage:** Entered automatically by python -m src.labels

**Caution:** Module-launch forwarding layer.

**Current SHA256:** `eaa037077d4d9638155389dcbaf1d4c3804ec5c30fcaf63430ed3798f60869c9`

## src/score/__init__.py

[Open file](../repository/src/score/__init__.py)

Exports the frozen CPU track-scoring or bundled-panel regression entry point.

- Defines a lazily importing main
- Forwards arguments to score_tracker.py through scripts.resource_entry.run

**Inputs:** Command-line arguments argv

**Outputs:** Return value/output from the delegated resource entry point

**Usage:** Used by python -m src.score or a direct main call

**Caution:** Forwarding layer; the scientific logic is in the frozen resource entry point.

**Current SHA256:** `9355dc1f284d25e2397f9d95cdc2698771c113e451fa04b2ed847412651e4827`

## src/score/__main__.py

[Open file](../repository/src/score/__main__.py)

Makes src.score runnable as a Python module.

- Imports main from the same package
- Uses the return value as the exit code under the __main__ guard

**Inputs:** Module-run arguments

**Outputs:** Process exit code and main output

**Usage:** Entered automatically by python -m src.score

**Caution:** Module-launch forwarding layer.

**Current SHA256:** `eaa037077d4d9638155389dcbaf1d4c3804ec5c30fcaf63430ed3798f60869c9`

## src/score/native_v11.py

[Open file](../repository/src/score/native_v11.py)

Modern adapter recomputing identities from actual output boxes and scoring saved v11 native final events.

- Verifies frozen core code and input paths for 01/02
- Preserves native final_events positions and attaches recomputed identities
- Writes per-gate, binned, and aggregate scores with read/failure audits

**Inputs:** Native outputs for the two development sequences and explicit GT/seqinfo paths

**Outputs:** Scoring report, audit, and completion/failure receipts

**Usage:** Used by scripts/score_native_v11.py to score native v11 results

**Caution:** Scores the saved event decoding. Status remains NOT_REAL_DATA_REGRESSED; historical agreement requires separate regression evidence.

**Current SHA256:** `91249ac50de9cd4948a9eeb47a352b4c0717f0efe319c68d0cf14d0586f54275`

## src/track/cli.py

[Open file](../repository/src/track/cli.py)

Modern entry point running three frozen author-version trackers from one explicitly bound YOLOX cache.

- Checks cache sequence, frame order, and hashes
- Calls byte/oc/bot and retains per-frame audits
- Converts to MOTChallenge coordinates and writes an output manifest

**Inputs:** Cache directory, method, and optional BoT GMC manifest; execution requires a new out

**Outputs:** Sequence .txt, observations.jsonl.gz, and track_manifest.json

**Usage:** Standard panel tracking stage; results then go to score_tracker.py

**Caution:** The default validates metadata only. BoT requires an explicit GMC binding; ReID is disabled and M4 is outside this entry point.

**Current SHA256:** `27fd920fccd8ec26909346023dc86d062bd23822a3b3f09d8f79e6808ac0b5f9`

## src/track/fragments/r15e24_inference___bound_bytes.py

[Open file](../repository/src/track/fragments/r15e24_inference___bound_bytes.py)

Retained legacy function fragment reading source through a controlled reader and checking its hash.

- Calls reader.read with a purpose and expected hash
- Verifies the bytes type and returns the source binding

**Inputs:** reader, path, sha, and purpose

**Outputs:** Source bytes and a path/bytes/sha256 dictionary

**Usage:** Used for companion adapter loading and idxfix verification

**Caution:** Requires caller-provided reader and _require; reads follow the controlled reader contract.

**Current SHA256:** `7e1bee5b9318552eeca41b98a9da5343952fe96e84317ac6bc949ccabb0dcb70`

## src/track/fragments/r15e24_inference___load_adapter.py

[Open file](../repository/src/track/fragments/r15e24_inference___load_adapter.py)

Retained legacy function fragment constructing an adapter module from bound bytes.

- Locates the adapter under the specified scripts root
- Uses _bound_bytes verification before compiling into an isolated namespace

**Inputs:** reader, filename, and SHA256

**Outputs:** Module object and source binding

**Usage:** Loads frozen r15e17_trackers.py for ByteTrackTracker

**Caution:** Depends on _root and companion functions; the executed object must be bound adapter source.

**Current SHA256:** `c6330f3f5f93415360ee2da9a9a56e29d5bf3a0f87aead05382845f20c458c87`

## src/track/fragments/r15e24_inference___register_packages.py

[Open file](../repository/src/track/fragments/r15e24_inference___register_packages.py)

Retained legacy helper fragment registering installed runtime-library directories.

- Locates specified installed packages with find_spec
- Registers read-only runtime-library trees with reader

**Inputs:** reader and a list of package names

**Outputs:** Package-name-to-directory mapping

**Usage:** Used when ByteTrackTracker initializes runtime dependencies

**Caution:** Missing packages raise errors and require prior installation. Runtime-library registration is separate from data-read authorization.

**Current SHA256:** `fff53fac4cd298eff725072c73fac8edb91c35f2169d40cd49bb2eff8f30affe`

## src/track/fragments/r15e24_inference___require.py

[Open file](../repository/src/track/fragments/r15e24_inference___require.py)

Retained condition-checking function shared by the legacy inference fragments.

- Raises RuntimeError when a condition fails
- Preserves the caller-provided error message

**Inputs:** Boolean condition and message

**Outputs:** No value on success; exception on failure

**Usage:** Used in the assembled namespace of companion inference fragments

**Caution:** Scope is assertion-style condition checking.

**Current SHA256:** `bfcf891dd8b6d6aaba9cdc3edbeb60d8d80cbb200fdd6a78791d27b34deb299b`

## src/track/fragments/r15e24_inference___seed.py

[Open file](../repository/src/track/fragments/r15e24_inference___seed.py)

Retained legacy function fragment seeding random libraries with a shared value.

- Seeds Python random and NumPy
- Optionally seeds Torch and CUDA

**Inputs:** use_torch Boolean and external SEED

**Outputs:** NumPy module and updated random state

**Usage:** Used when constructing frozen tracking/inference dependencies

**Caution:** Runs in the assembled fragment namespace; use_torch=True imports Torch and checks CUDA.

**Current SHA256:** `dc61600d8636596b36091199a9bd815575f28e5c23ac85fe93df31e0b974346b`

## src/track/fragments/r15e24_inference__ByteTrackTracker.py

[Open file](../repository/src/track/fragments/r15e24_inference__ByteTrackTracker.py)

Frozen legacy inference-class fragment wrapping ByteTrack while preserving complete raw-row indices.

- Constructs an independent idxfix ByteTrack for each sequence
- Supports updates with an image or known native dimensions
- Maps the final-column output index back to the complete raw-detection list

**Inputs:** Controlled reader, 25 fps, raw detections, and optional image/dimensions

**Outputs:** All raw rows with IDs, tracker_rows, and statistical metadata

**Usage:** Assembled by fragment_namespace for MethodTracker and the native pipeline

**Caution:** Requires companion helper fragments and runtime packages in an assembled namespace; wraps an existing tracker implementation.

**Current SHA256:** `12c19ed11304202e9ee7df4d60551ae6b088ef46528754563d370facd6c8a3fb`

## src/track/fragments/r15e24_inference__IDXFIX_SHA.py

[Open file](../repository/src/track/fragments/r15e24_inference__IDXFIX_SHA.py)

Frozen hash constant binding the index-fix source in the legacy inference script.

- Declares IDXFIX_SHA only
- Lets the loader verify the specified idxfix source file

**Inputs:** No runtime input

**Outputs:** Complete SHA256 string

**Usage:** Used with _bound_bytes when constructing ByteTrackTracker

**Caution:** Source-binding constant fragment.

**Current SHA256:** `c7799f637a10ae707a582c4fa40f1d6bc145106c0c4ebcb759c0963f1e0b9da0`

## src/track/fragments/r15e24_inference__SEED.py

[Open file](../repository/src/track/fragments/r15e24_inference__SEED.py)

Retained random-seed constant from the legacy inference script.

- Fixes SEED at 20261022
- Supplies a shared value to the companion _seed fragment

**Inputs:** No runtime input

**Outputs:** Integer seed

**Usage:** Assembled with inference fragments by fragment_namespace

**Caution:** Fixes the random seed; device-level bitwise reproducibility requires additional evidence.

**Current SHA256:** `a3e81347b3e65db0ea099be62e0fc53ce7a9a75d5c68b48b1b06f4e1cb40cfe1`

## src/track/fragments/r15e24_inference__TRACKER_ADAPTER_SHA.py

[Open file](../repository/src/track/fragments/r15e24_inference__TRACKER_ADAPTER_SHA.py)

Frozen hash constant binding tracker-adapter source in the legacy inference script.

- Declares TRACKER_ADAPTER_SHA only
- Fixes the expected content of r15e17_trackers.py

**Inputs:** No runtime input

**Outputs:** Complete SHA256 string

**Usage:** Used when ByteTrackTracker calls _load_adapter

**Caution:** Constant identifying the expected adapter source.

**Current SHA256:** `aa691a122dcde89c7ae3b59a442347765957afe0f24fc1842b29f49e7c265f1c`

## src/track/fragments/r15e24_run55__point_for.py

[Open file](../repository/src/track/fragments/r15e24_run55__point_for.py)

Retained legacy fragment selecting the raw-box bottom-center footpoint and applying boundary exclusions.

- Computes the bottom-edge center of an xyxy box
- Excludes nonfinite values and T2 boundary conditions
- Also reports whether the point is outside the image

**Inputs:** box, width, and height

**Outputs:** point or None, exclusion reason, and outside flag

**Usage:** Generates native v11 footpoints from raw detections

**Caution:** Preserves raw coordinates and depends on math. Replacing raw detection boxes with tracker output boxes changes this point definition.

**Current SHA256:** `e30c005e897d23ed9f76662b4c7358ce25e8822d062c5d1802e672cb3c2cdecc`

## src/track/fragments/r15e26_run_v2__fresh_raw.py

[Open file](../repository/src/track/fragments/r15e26_run_v2__fresh_raw.py)

Retained legacy function fragment clearing old identities and derived fields before replay.

- Checks that raw_detection_index is contiguous
- Copies raw boxes, scores, classes, and keypoints
- Resets track_id to None

**Inputs:** Saved raw-detection list

**Outputs:** Copies of raw detections for retracking

**Usage:** Called before MethodTracker replay

**Caution:** Preserves raw boxes and resets prior identity assignments; depends on copy and require.

**Current SHA256:** `3f230ac853f719ca41492730e44eac7d3547f8fbbfbab36dbcb558ddd652cc2a`

## src/track/fragments/r15e26_run_v2__MethodTracker.py

[Open file](../repository/src/track/fragments/r15e26_run_v2__MethodTracker.py)

Retained legacy class fragment changing admission thresholds while using the frozen idxfix association engine.

- Allows only .1 or .25 detection thresholds
- Validates output indices and maps them to complete raw rows
- Records low-score admissions and original output matrices

**Inputs:** gate, threshold, raw rows with cleared IDs, and native dimensions

**Outputs:** Raw rows with track IDs, tracker_rows, and metadata

**Usage:** Assembled by native_v11.method_tracker

**Caution:** Threshold adapter around the existing ByteTrack association engine; frame rate is fixed at 25.

**Current SHA256:** `eee4662f21f8a53cc951c1c8b692258e26cec518c7b3475c3857f46c00d423ee`

## src/track/frozen/event_sources/scripts/r15_dedup_direction.py

[Open file](../repository/src/track/frozen/event_sources/scripts/r15_dedup_direction.py)

Frozen source for R1/R2/R3 deduplication and direction rules on confirmed events.

- Builds groups from saved events and observations of one clip
- Evaluates support within specified open/closed time windows
- Returns complete decision details, including rejected groups

**Inputs:** Single-clip events, observations, and variant

**Outputs:** all_groups and per-group details

**Usage:** r15e24_events extracts transform_events and companion functions by source hash and uses R1+R2

**Caution:** Operates on supplied records; time comparisons use the specified boundaries exactly.

**Current SHA256:** `dbf70dc6eb38875250d4248f3b49f36c03bba0d0fd1bf7ac90241f4d20bcb9f7`

## src/track/frozen/event_sources/scripts/r15e3_e2_core.py

[Open file](../repository/src/track/frozen/event_sources/scripts/r15e3_e2_core.py)

Frozen legacy E3 region-transition state machine and rule-comparison source.

- Splits segments by the duration of absence of the original ID
- Uses the first observed target-region frame as the event time
- Retains same-ID line-crossing/region-event comparison and self-checks

**Inputs:** Saved observations with region distances, margin, and max_gap_s

**Outputs:** Region events, segments, extraction statistics, or comparison results

**Usage:** The event adapter extracts zone_from_distances/extract_region_events

**Caution:** Observation gaps retain their original spacing. Legacy top-level imports depend on historical modules; use the selective loader.

**Current SHA256:** `a9d4ef470e8adbd7b6cb0f0a0017c8592873a885b3ea2b5e9423c31484476c89`

## src/track/frozen/event_sources/scripts/r15e3_head.py

[Open file](../repository/src/track/frozen/event_sources/scripts/r15e3_head.py)

Frozen legacy E3 collection of head-to-foot affine fitting and point-selection functions.

- Averages confident keypoints and filters fitting samples
- Provides standardized rank checks, OLS, within-camera validation, and error summaries
- Selects box/head/hybrid points by version

**Inputs:** Detection boxes/keypoints, dimensions, external samples, or an existing model

**Outputs:** Fit/error records or selected points and provenance

**Usage:** The event adapter extracts only required point-selection functions; this file also explains related HeadGate principles

**Caution:** The complete source retains fitting functions; the portable event entry point uses point selection with supplied models.

**Current SHA256:** `e67a1c05abb9f5039433054aadfef9491a488c42b6bb336ffe4b20086afa2f17`

## src/track/frozen/event_sources/scripts/r15e3_regions_common.py

[Open file](../repository/src/track/frozen/event_sources/scripts/r15e3_regions_common.py)

Frozen geometry utilities for native-pixel polygon membership and nearest boundaries.

- Computes nearest edges, arc length, and signed distance
- RegionClassifier converts normalized regions to native coordinates
- Includes synthetic self-checks for convex/concave polygons

**Inputs:** 2D points and polygons; the complete class also accepts region JSON and dimensions

**Outputs:** Region name, signed distance, and boundary position

**Usage:** r15e24_events extracts only nearest_boundary/signed_distance

**Caution:** The retained class constructor reads a region file. This guide used static inspection; the portable path receives explicit geometry.

**Current SHA256:** `e2dd5687f6b5574d1aa49a3396cba97baee453c20c6870e7515bc2a86f8f25e4`

## src/track/frozen/event_sources/scripts/r15e6_core.py

[Open file](../repository/src/track/frozen/event_sources/scripts/r15e6_core.py)

Frozen source for C1/C2 post-confirmation evidence in legacy E3 hybrid events.

- Infers local height from a footpoint and flags locations outside the fitted range
- Computes boundary distance and support before/after events
- Retains diagnostic/manual-review row generation and the legacy main

**Inputs:** Saved events, track segments, G1 model, polygons, and configuration

**Outputs:** Confirmation verdicts, evidence records, and legacy diagnostic outputs

**Usage:** r15e24_events extracts height_at_foot, edge_distance, and evidence by hash

**Caution:** The complete file retains historical dependencies and an I/O driver; the adapter selectively loads permitted nodes.

**Current SHA256:** `91bb6c597db1c404738f153d8ed86608b449c71aa4f48204d489ff8047447ded`

## src/track/frozen/r15_tracker_idxfix.py

[Open file](../repository/src/track/frozen/r15_tracker_idxfix.py)

Frozen wrapper repairing ByteTrack input-index provenance.

- IndexedDetections preserves original indices through slicing
- A factory creates an isolated BYTETracker subclass
- Sets STrack.idx to the complete update-input index

**Inputs:** Installed BYTETracker class, parameters, and original Boxes

**Outputs:** Isolated tracker class/outputs with correct index provenance

**Usage:** Used by the ByteTrack branch of SmokeTracker

**Caution:** Preserves the installed package, association, thresholds, and Kalman state. Validation scope is index provenance; event-identity accuracy needs separate evaluation.

**Current SHA256:** `477c3041fed126903e8e18de967e14da4a98775fef5ac4a4cf48a5eb611ac0d3`

## src/track/frozen/r15e17_trackers.py

[Open file](../repository/src/track/frozen/r15e17_trackers.py)

Frozen tracking-only adapter preserving original detection boxes and keypoints.

- Reads bound source/configuration through a controlled gate
- Constructs isolated trackers under P2/BoT configuration
- Audits GMC and maps output indices back to input rows

**Inputs:** kind, fps, gate, detection list, and image

**Outputs:** Original detections with IDs, diagnostic tracker_rows, and runtime metadata

**Usage:** ByteTrackTracker calls existing trackers through SmokeTracker

**Caution:** Scope is tracking adaptation; the caller supplies detections/images and is responsible for runtime isolation.

**Current SHA256:** `fceb7352bca9c75061371e6c6e27ad8c243a293a770010fae0a5e819a2b97599`

## src/track/frozen/r15e24_events.py

[Open file](../repository/src/track/frozen/r15e24_events.py)

Frozen MOT20 event adapter assembling verified legacy event functions.

- Extracts specified function/constant AST nodes by SHA
- Normalizes observations for one sequence and gate to the native frame clock
- Runs region transitions, observed C1, and R1+R2 in order

**Inputs:** Controlled source reader, observations, external G1/polygons, and 25 fps metadata

**Outputs:** Raw candidates, confirmation evidence, groups, final_events, and function audit

**Usage:** Used by native_v11.native_events and production workers

**Caution:** Scope is event derivation from supplied observations and models. Detection, tracking, identity matching, scoring, fitting, and invalid-point repair belong outside this adapter.

**Current SHA256:** `14ddf655a5ddf59861ba15fa7b3f712e3234b11b18e33aacf23114817dd924bb`

## src/track/frozen/r15e26_stitch_v2.py

[Open file](../repository/src/track/frozen/r15e26_stitch_v2.py)

Frozen one-pass M4 track linking that decides on original tracks and remaps IDs only.

- Validates the exact frozen policy before consuming frames
- Filters candidates using endpoint velocities, gate-line neighborhoods, and G1 heights
- Selects mutual unique best links and retains original IDs/matrices

**Inputs:** frames, namespace, fps, gate lines, G1, and clarification policy

**Outputs:** Remapped frames, links, ID mapping, candidate/rejection reasons, and statistics

**Usage:** Called by m4-stitch or the native v11 pipeline

**Caution:** Development 01/02 only; points remain unchanged. Exact cost ties are rejected, and linking uses one simultaneous pass.

**Current SHA256:** `a0e2b0f4a03189270a4b985be8dac99a1ba59e6f59b38be83946a1977f991ded`

## src/track/frozen/sota83c/bbox_overlaps_numpy.py

[Open file](../repository/src/track/frozen/sota83c/bbox_overlaps_numpy.py)

NumPy substitute translating the endpoint-inclusive IoU formula from cython_bbox 0.1.5.

- Validates finite float64 Nx4 inputs
- Computes overlaps using the upstream +1-pixel formula
- Retains upstream source hashes and copyright/license notes

**Inputs:** Two float64 arrays: boxes and query_boxes

**Outputs:** N by K IoU matrix

**Usage:** Used by vendor ByteTrack/BoT matching

**Caution:** Approved implementation substitute for the compiled extension; preserves the upstream arithmetic without epsilon, clipping, or width/height clamping.

**Current SHA256:** `254feb415b64d590e7de59f96a72130b6836302756c25dec36d58ee23f682947`

## src/track/frozen/sota83d/panel.py

[Open file](../repository/src/track/frozen/sota83d/panel.py)

Frozen unified adapter for three trackers using the authors' MOT17 parameters.

- Applies FP16-product admission while retaining original FP32 input scores
- Wraps byte/oc/bot and filters output area/aspect ratio
- Verifies per-frame BoT GMC-file consumption and retains output audits

**Inputs:** Raw detections, source_frame, method, sequence, dimensions, and BoT root directory

**Outputs:** Author output rows, retained output boxes, admission indices, internal frame numbers, and GMC records

**Usage:** track.cli.run constructs PanelTracker

**Caution:** Preserves the original admission rule: tracker calls occur only with admitted boxes. Panel settings disable ReID and omit M4/interpolation; native v11 follows a separate pipeline.

**Current SHA256:** `6a485ff44c980635a787f12a76d8e10e4168743e37f85d56aa92c8cdf1f00c7b`

## src/track/frozen/sota83d/vendor/__init__.py

[Open file](../repository/src/track/frozen/sota83d/vendor/__init__.py)

Marks the private package containing third-party tracker source copies.

- Contains only a package docstring
- Avoids importing upstream root packages

**Inputs:** Python package import

**Outputs:** Private vendor namespace

**Usage:** PanelTracker imports the selected vendor subpackage by method

**Caution:** Container for third-party source copies.

**Current SHA256:** `64f0ed44dffcd37d8fe405e5c598e330447100ec086c71a12283e6d285932eda`

## src/track/frozen/sota83d/vendor/bot/__init__.py

[Open file](../repository/src/track/frozen/sota83d/vendor/bot/__init__.py)

Marks the third-party bot tracker subpackage with deferred loading.

- Contains only the No eager imports note
- Leaves specific module selection to the caller

**Inputs:** Python package import

**Outputs:** Subpackage namespace

**Usage:** Used when PanelTracker lazily imports the selected method

**Caution:** Package initialization only; tracking computations reside in the implementation modules.

**Current SHA256:** `cedd223b068848334f5d814b369870eebc05b5a19c7207da6623b031c006ab1b`

## src/track/frozen/sota83d/vendor/bot/basetrack.py

[Open file](../repository/src/track/frozen/sota83d/vendor/bot/basetrack.py)

Retained upstream BoT-SORT base classes for track states and resettable IDs.

- Defines the additional LongLost state
- Maintains track history, features, and lifecycle fields
- Provides ID allocation and counter reset

**Inputs:** Track-state operations

**Outputs:** IDs, states, and base track properties

**Usage:** Inherited by bot_sort.STrack

**Caution:** Third-party track-management base class.

**Current SHA256:** `a0f717a5059ebfa626a63cea5b040a649acd7720072f503cabfa24d749f082f6`

## src/track/frozen/sota83d/vendor/bot/bot_sort.py

[Open file](../repository/src/track/frozen/sota83d/vendor/bot/bot_sort.py)

Retained third-party BoT-SORT tracking and camera-motion-compensation integration.

- STrack maintains box states and optional features
- Performs multistage association after GMC fusion
- Manages lost/removed tracks and duplicate removal

**Inputs:** Detections, images, BoT parameters, and GMC source

**Outputs:** Active track objects

**Usage:** Used by the bot branch of PanelTracker

**Caution:** Frozen panel settings are with_reid=False and cmc_method=file; retained source includes additional optional capabilities.

**Current SHA256:** `82a336dfe44bbc7f5736368fcbb0b6d044c9c7bf8e443b5d445d624fbcb85788`

## src/track/frozen/sota83d/vendor/bot/gmc.py

[Open file](../repository/src/track/frozen/sota83d/vendor/bot/gmc.py)

Retained BoT-SORT component for estimating or reading global camera motion.

- Supports ORB/SIFT/ECC/sparse-optical-flow branches
- Reads affine transforms from saved files
- Dispatches to implementations by method

**Inputs:** Images, detections, and method, or an existing GMC file

**Outputs:** Camera-motion affine matrix

**Usage:** The frozen panel BoT branch selects applyFile

**Caution:** Third-party implementation; the current entry point consumes explicitly bound GMC with original frame coverage.

**Current SHA256:** `c1cf477cd31170540b1ce2f10c708e3ea833f5275232766295f8f9e67e06eb28`

## src/track/frozen/sota83d/vendor/bot/kalman_filter.py

[Open file](../repository/src/track/frozen/sota83d/vendor/bot/kalman_filter.py)

Retained BoT-SORT Kalman filter representing boxes by center, width, and height.

- Uses an eight-dimensional x/y/w/h state and corresponding velocities
- Performs batch prediction, projection, and measurement updates
- Provides chi-squared thresholds and gating distances

**Inputs:** Box xywh measurements and state covariance

**Outputs:** Predicted/updated states and distances

**Usage:** Used by bot.STrack and matching

**Caution:** Third-party numerical module; w denotes width, while ByteTrack uses aspect ratio a.

**Current SHA256:** `c1a4c0acc71b9a91c0cdbe7b689f88712d68e7e8be4d7e54fb437f33fdbc9e5a`

## src/track/frozen/sota83d/vendor/bot/LICENSE

[Open file](../repository/src/track/frozen/sota83d/vendor/bot/LICENSE)

MIT license text retained in the bot directory.

- Retains the 2022 Nir Aharon copyright notice
- States notice-retention requirements and the warranty disclaimer

**Inputs:** Human reading

**Outputs:** License terms

**Usage:** Read and retain when distributing or reviewing the corresponding vendor code

**Caution:** The file text defines the documented code license; model-weight licensing requires its own source.

**Current SHA256:** `12a15474ca15cec568da311e6cd89e593e3cd2bb5b790e75b90e1608306a3a5f`

## src/track/frozen/sota83d/vendor/bot/matching.py

[Open file](../repository/src/track/frozen/sota83d/vendor/bot/matching.py)

Retained BoT-SORT box/feature distances and linear-association utilities.

- Computes IoU and predicted-box distances and supports box expansion
- Provides lap assignment and motion gating
- Retains embedding, IoU, and score fusion

**Inputs:** Tracks, detections, cost matrices, and thresholds

**Outputs:** Matches or cost matrices

**Usage:** Called by BoTSORT.update

**Caution:** Third-party functions; the current panel has ReID disabled, so feature branches remain outside the active configuration.

**Current SHA256:** `34edce37889a3ecac3f2c43183fe1ead77e4335201f96bf5d82a7c61cefb80f2`

## src/track/frozen/sota83d/vendor/byte/__init__.py

[Open file](../repository/src/track/frozen/sota83d/vendor/byte/__init__.py)

Marks the third-party byte tracker subpackage with deferred loading.

- Contains only the No eager imports note
- Leaves specific module selection to the caller

**Inputs:** Python package import

**Outputs:** Subpackage namespace

**Usage:** Used when PanelTracker lazily imports the selected method

**Caution:** Package initialization only; tracking computations reside in the implementation modules.

**Current SHA256:** `cedd223b068848334f5d814b369870eebc05b5a19c7207da6623b031c006ab1b`

## src/track/frozen/sota83d/vendor/byte/basetrack.py

[Open file](../repository/src/track/frozen/sota83d/vendor/byte/basetrack.py)

Retained upstream ByteTrack base classes for track states and IDs.

- Defines New/Tracked/Lost/Removed states
- Allocates global track IDs and stores base properties
- Provides lost/removed state markers

**Inputs:** Lifecycle calls on derived track objects

**Outputs:** IDs, states, and frame properties

**Usage:** Inherited by byte_tracker.STrack

**Caution:** Third-party infrastructure; the caller must reset class-level counters for independent sequences.

**Current SHA256:** `c938afcf7c516bba4a77155c2499fcae6f926df7a2faa6f73a4be1b073f9bb2d`

## src/track/frozen/sota83d/vendor/byte/byte_tracker.py

[Open file](../repository/src/track/frozen/sota83d/vendor/byte/byte_tracker.py)

Retained third-party ByteTrack track-state and per-frame association implementation.

- STrack predicts and updates boxes using Kalman state
- BYTETracker maintains active/lost/removed sets
- Provides track-set union, difference, and duplicate removal

**Inputs:** Detection boxes/scores, image dimensions, and tracker parameters

**Outputs:** List of activated track objects

**Usage:** Called by the byte branch of PanelTracker

**Caution:** Upstream vendor implementation; the local idxfix wrapper has its own indexing adaptation and threshold configuration.

**Current SHA256:** `3d2739eb8341f07fa46d0154b99e87ccd8ea09ed97e4ccaa6a981049fc57d6b2`

## src/track/frozen/sota83d/vendor/byte/kalman_filter.py

[Open file](../repository/src/track/frozen/sota83d/vendor/byte/kalman_filter.py)

Retained ByteTrack Kalman filter using box center, aspect ratio, and height.

- Uses an eight-dimensional x/y/a/h state and corresponding velocities
- Implements initialization, prediction, measurement projection, and update
- Computes Mahalanobis gating distances

**Inputs:** Box measurements, means/covariances, and motion parameters

**Outputs:** Updated states, covariance, or gating distances

**Usage:** Used by byte.STrack and matching

**Caution:** Third-party numerical module; a denotes aspect ratio, while BoT uses width.

**Current SHA256:** `9842d0dd9957c97e312d42e5789441add55082066d87cc051ac768143a46eb39`

## src/track/frozen/sota83d/vendor/byte/LICENSE

[Open file](../repository/src/track/frozen/sota83d/vendor/byte/LICENSE)

MIT license text retained in the byte directory.

- Retains the 2021 Yifu Zhang copyright notice
- States notice-retention requirements and the warranty disclaimer

**Inputs:** Human reading

**Outputs:** License terms

**Usage:** Read and retain when distributing or reviewing the corresponding vendor code

**Caution:** The file text defines the documented code license; model-weight licensing requires its own source.

**Current SHA256:** `e9d83751678cbaba6dfba902ea39215c423d93425e58f8450d6001f7261696f9`

## src/track/frozen/sota83d/vendor/byte/matching.py

[Open file](../repository/src/track/frozen/sota83d/vendor/byte/matching.py)

Retained ByteTrack assignment costs and association helpers.

- Provides IoU-based distance and lap linear assignment
- Retains feature distance, motion gating, and score fusion
- Uses the NumPy cython_bbox substitute for IoU

**Inputs:** Tracks/detections or cost matrices, and thresholds

**Outputs:** Match indices, unmatched sets, and fused costs

**Usage:** Used in BYTETracker.update association steps

**Caution:** Third-party functions; embedding helpers are retained while the current panel has ReID disabled.

**Current SHA256:** `b94735328311b0d4b7a8178d3417dc3cdff8b99e00d96fe034eb2a1c446a88f0`

## src/track/frozen/sota83d/vendor/oc/__init__.py

[Open file](../repository/src/track/frozen/sota83d/vendor/oc/__init__.py)

Marks the third-party oc tracker subpackage with deferred loading.

- Contains only the No eager imports note
- Leaves specific module selection to the caller

**Inputs:** Python package import

**Outputs:** Subpackage namespace

**Usage:** Used when PanelTracker lazily imports the selected method

**Caution:** Package initialization only; tracking computations reside in the implementation modules.

**Current SHA256:** `cedd223b068848334f5d814b369870eebc05b5a19c7207da6623b031c006ab1b`

## src/track/frozen/sota83d/vendor/oc/association.py

[Open file](../repository/src/track/frozen/sota83d/vendor/oc/association.py)

Retained OC-SORT box-similarity, motion-direction, and matching helpers.

- Provides IoU/GIoU/DIoU/CIoU and center distance
- Uses velocity directions and existing observations in association
- Returns matches and unmatched detections/tracks

**Inputs:** Detection boxes, predicted tracks, velocities, historical observations, and thresholds

**Outputs:** Similarity/cost matrices and match indices

**Usage:** OCSort.update uses associate and companion functions

**Caution:** Third-party implementation; KITTI and alternative-metric branches remain available in source beyond the active panel configuration.

**Current SHA256:** `c009a78eaa1c35c1d61217506255051ba882a7b99f9505cdec64da474ff0fbd7`

## src/track/frozen/sota83d/vendor/oc/kalmanfilter.py

[Open file](../repository/src/track/frozen/sota83d/vendor/oc/kalmanfilter.py)

Retained Kalman utilities used by OC-SORT, including observation freeze/resume mechanisms.

- KalmanFilterNew provides predict/update and freeze/unfreeze
- Retains steady-state, correlated-noise, batch, and RTS-smoothing interfaces
- Includes likelihood, Mahalanobis, and matrix-dimension checks

**Inputs:** State matrices, measurements, noise, and transition models

**Outputs:** State estimates, covariances, smoothing results, or diagnostic values

**Usage:** Used internally by ocsort.KalmanBoxTracker

**Caution:** Large third-party utility module; a valid model requires tracker-supplied matrix configuration.

**Current SHA256:** `165a2d5243f2b874e37d3a3ae8112402f5c53ddfb6eb6e2cddda3311c3a2cded`

## src/track/frozen/sota83d/vendor/oc/LICENSE

[Open file](../repository/src/track/frozen/sota83d/vendor/oc/LICENSE)

MIT license text retained in the oc directory.

- Retains the 2021 Yifu Zhang copyright notice
- States notice-retention requirements and the warranty disclaimer

**Inputs:** Human reading

**Outputs:** License terms

**Usage:** Read and retain when distributing or reviewing the corresponding vendor code

**Caution:** The file text defines the documented code license; model-weight licensing requires its own source.

**Current SHA256:** `e9d83751678cbaba6dfba902ea39215c423d93425e58f8450d6001f7261696f9`

## src/track/frozen/sota83d/vendor/oc/ocsort.py

[Open file](../repository/src/track/frozen/sota83d/vendor/oc/ocsort.py)

Retained third-party OC-SORT tracker based on SORT.

- Converts xyxy boxes to/from center/area/aspect-ratio states
- KalmanBoxTracker stores observations and motion directions
- OCSort updates and returns ID-tagged boxes

**Inputs:** Per-frame detections, dimensions, and OC parameters

**Outputs:** Box array with track IDs

**Usage:** Used by the oc branch of PanelTracker

**Caution:** Source credits Alex Bewley's SORT. The tracker supports empty-frame updates; this panel adapter follows its frozen admission-based call semantics.

**Current SHA256:** `122cc1c27d3321eac0debdf3ba782b76d189e1ac878256b8291ffeb4314fa979`

## src/track/native_v11.py

[Open file](../repository/src/track/native_v11.py)

Modern entry point combining frozen low-threshold tracking, raw-detection footpoints, M4, and native events.

- Verifies cache/geometry/G1/policy/detection source bindings
- Combines legacy tracking fragments and remaps IDs with M4
- Saves byte bindings for native events and actual tracker_rows

**Inputs:** Development-sequence native manifest and five explicitly supplied asset types

**Outputs:** frames.jsonl.gz, six-gate events.json, and native_manifest.json

**Usage:** Produces native v11 results for score_native_v11.py

**Caution:** Native events use raw_detection_box; identity scoring uses post_M4_tracker_rows. This entry point produces outputs for downstream scoring.

**Current SHA256:** `f7ee8018eea469d02f28dec83833e1cadafb35a42161eb9a03bee281aaf481f8`

## tests/test_native_v11_scoring.py

[Open file](../repository/tests/test_native_v11_scoring.py)

Synthetic-input tests of the native v11 scoring interface and data boundaries.

- Checks the output-box identity pool, M4 provenance, and preservation of native-event positions
- Checks that unknowns remain in the final precision denominator
- Checks cached-identity rejection, validation-only defaults, path-first checks, and output bindings

**Inputs:** Temporary manifests/boxes/GT dictionaries and mocks constructed within tests

**Outputs:** unittest assertion results

**Usage:** Read when validating the modern native_v11 adapter, or run in an authorized environment

**Caution:** Synthetic-data scope; this task performed static inspection only and accessed no real GT.

**Current SHA256:** `02448b81e86e3b65395d6e5606990755ad0dda6fe7f9f14311630c9e7a113a8f`

## tests/test_pipeline_portability.py

[Open file](../repository/tests/test_pipeline_portability.py)

Synthetic examples checking portable-entry-point wiring and frozen-function boundaries.

- Checks frozen provenance, bindings, and rejection of optimized Python
- Checks E2/D1/HeadGate/GateLink/E1/M4/ReID behavior
- Checks confirmation command generation, deployment paths, and raw-footpoint semantics

**Inputs:** In-test examples, temporary files, and mocks

**Outputs:** unittest assertion results

**Usage:** Synthetic contract validation after portable-pipeline changes

**Caution:** Uses synthetic inputs without models or datasets; real-data regression has a separate evidence requirement.

**Current SHA256:** `e155f3cbf8a50589c6e91a1342d9fe253a8075a0a1f15deb51f705295818f247`

## tests/test_resource_adapters.py

[Open file](../repository/tests/test_resource_adapters.py)

Synthetic-input tests of resource-entry arguments, output isolation, and MOT-row parsing.

- Rejects repository-local/existing outputs and abbreviated-argument bypasses
- Restricts launchable frozen resources and checks the CPU environment
- Checks MOT-row order, duplicates, and nonfinite values

**Inputs:** Temporary files, simulated command arguments, and synthetic MOT text

**Outputs:** unittest assertion results

**Usage:** Validates adapter boundaries in scripts.resource_entry and the frozen MOT reader

**Caution:** Uses synthetic text and temporary inputs; this task performed static inspection only, with real GT and bundled examples outside the read scope.

**Current SHA256:** `3c04b504427767cda7620cf706b4382f09c085cec3b4af06a36c4e660277f4c8`

## THIRD_PARTY_NOTICES.md

[Open file](../repository/THIRD_PARTY_NOTICES.md)

Point to upstream copyright and license notices that must be retained for each component.

- Lists YOLOX/ByteTrack model code and the three tracker vendor directories
- Explains retention of SORT author attribution and contact information
- Distinguishes adapted copies from complete upstream repositories
- Separates software licenses, weight licenses and release rights review

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Read alongside the relevant vendor LICENSE and NOTICE files.

**Caution:** Read delivery status as historical and use the guide status note for the later approved zip and current Q3_v2. Frozen hashes identify project-adapted copies; upstream authentication uses separate evidence.

**Current SHA256:** `1c604a8b28efa4a2f2f06558eddd3b2ea0b4c8e9f4a7adaf7f5dc7ee89c37fdd`

## VERIFY.md

[Open file](../repository/VERIFY.md)

Record which acceptance checks were performed during packaging and what they did not cover.

- CPU reconstruction and three standard-track self-check results and timings
- Resource, pipeline, native-scoring and synthetic Q2/Q3 check records
- Provenance relationship between frozen sources and adapters
- Historical pending regression gates and repository audit commands

**Inputs:** Reading material; no runtime parameters.

**Outputs:** No runtime results.

**Usage:** Determine which inputs, stages and fields a particular PASS covers.

**Caution:** Use the guide status note for the later approved zip and current Q3_v2. The earlier 84-complete-file/16-slice record precedes the current map with 2 presentation revisions and 14 support files. Synthetic UI acceptance and human review have separate evidence.

**Current SHA256:** `f4202009eedfc579b7802ebd4b61d2965d79d5368ae7c9c7e05cfe470d751d77`

