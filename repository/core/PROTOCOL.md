# Protocol: v0.1 tracker-output scoring interface and panel regression

Written 2026-10-24 (US Eastern) before any v0.1 code is run on real data. Its SHA256 is recorded in `PROTOCOL.md.sha256`. Any later deviation is recorded in `REPORT_v0_1.md`; this file is not edited after the hash is recorded.

## 1. Scope and boundaries

- Development sequences MOT20-01 and MOT20-02 only. No other sequence, test window, timeline, review label or private file is opened.
- No download, installation, training, detector or tracker execution. Reference interpreter: CPython 3.10.18, NumPy 2.2.6 (`data/venvs/r11_measure`).
- `release/mot20_crossing_events_v0/` and everything under `scripts/` are read only. The new package is `release/mot20_crossing_events_v0_1/`, created as a byte-identical copy of v0 (verified with `diff -r`) and then extended. Package build helpers and run outputs live outside the package under `data/r15/release_v0_1_build/`.
- No numerical rule of the event chain or the scorer is re-implemented. Frozen functions are copied verbatim and bound by hash.

## 2. What will be built

1. `src/frozen_events/`: verbatim copies of exactly the members that the panel run's event chain executed:
   - the members `scripts/r15e24_events.py::load_frozen` compiles: `r15e3_regions_common.py` (`nearest_boundary`, `signed_distance`), `r15e3_e2_core.py` (`zone_from_distances`, `extract_region_events`), `r15e6_core.py` (`height_at_foot`, `edge_distance`, `evidence`), `r15_dedup_direction.py` (constants `VARIANTS`, `SOURCE_ZONE`, `TARGET_ZONE`; `_event_frame`, `_event_key`, `_valid_point`, `_observation_detail`, `_window`, `transform_events`), `r15e3_head.py` (`finite_point`, `keypoint_mean`, `predict_height`, `select_point`), placed in one module whose global namespace equals load_frozen's (`math`, `defaultdict`, `Counter`, `deepcopy`, `np` plus the members);
   - the adapter members of `scripts/r15e24_events.py` (`C1_KEY`, `make_height_model`, class `FrozenEvents` including `evaluate_sequence_gate`);
   - `point_for` from `scripts/r15e24_run55.py` (the panel run extracted it by AST into a namespace containing only `math`);
   - `event_view` from `scripts/sota83d/event_view.py`.
   `provenance.json` records, per source file, its SHA256 and, per member, line span, source-segment SHA256 and `ast.dump(node, include_attributes=False)` SHA256 (the v0 `src/frozen_score` method). The build fails if any copied AST differs. The source-segment hashes must also equal the `event_functions` audit recorded by the panel run itself.
2. `score_tracker.py` CLI:
   `python -B score_tracker.py --gt-root GT --seqinfo-root SEQINFO --tracks DIR --out NEW_DIR`, with `--seqinfo-root` defaulting to `--gt-root`, and `python -B score_tracker.py --self-test --gt-root GT [--seqinfo-root SEQINFO] --out NEW_DIR`.
3. `examples/panel/{byte,oc,bot}/MOT20-0{1,2}.txt`: the three published-tracker panel outputs (`data/r15/sota_panel83d/run_v1/<m>/MOT20-0X/observations.jsonl.gz`, field `outputs[]`) written as MOTChallenge rows, one row per emitted output, frames ascending, rows within a frame in `emitted_output_index` order. Columns: `source_frame, track_id, repr(x1+1), repr(y1+1), repr(x2-x1), repr(y2-y1), conf, -1, -1, -1`, where conf is `repr(score)` and `-1` when the tracker emitted no score.
4. `expected/panel_<m>.json`: saved panel main aggregate, per-sequence aggregate and the 12 gate units (from `data/r15/sota_panel83d/scoring_v1/units.json`, SHA256 `bef68a6d...ce5b`, and `scores.json`, SHA256 `6988835c...3992`), plus a compact copy of every saved gate's final events (track ID, direction, frames, fragment, prediction/member IDs, crossing position) and candidate/confirmed counts from the 36 saved `events.json` files (all 57 files bound by `score_inputs.json` were re-hashed on 2026-10-24 with zero mismatches).
5. Documentation: README section for the interface, `CHANGES.md`, `REPORT_v0_1.md`, updated `MANIFEST.json` (same schema string so the copied v0 `reproduce.py` still verifies the package; adds `package_version: 0.1`).

## 3. Interface semantics fixed in advance

- `DIR` must contain exactly-named `MOT20-01.txt` and `MOT20-02.txt`; no directory search.
- Each nonblank line has exactly 10 comma-separated finite numbers. Frame and ID must be integer-valued; frame in `[1, seqLength]`; ID `>= 0`; `w > 0`, `h > 0`. Columns 7-10 are parsed for validity and otherwise ignored. A duplicate `(frame, id)` is an error. Anything else fails the run; nothing is repaired or dropped silently.
- Conversion to native zero-based continuous xyxy in float64: `x0 = x - 1`, `y0 = y - 1`, `x1 = x0 + w`, `y1 = y0 + h` (the convention of the frozen GT parser).
- Identity tie key: the row's order of appearance within its frame in the file (0, 1, ...), playing the role of the panel's `emitted_output_index`.
- Points: frozen `point_for(output_box, width, height)` (bottom-centre; invalid at `x0 <= 0`, `x1 >= width-1`, `y1 >= height-1`), `point_source = 'box_bottom_center'`; observations through frozen `event_view(output, frame0)`.
- Events: per gate, `FrozenEvents.evaluate_sequence_gate(observations, sequence, gate_id, width, height, nb_frames, fps=25, model=make_height_model(coefficients, {'head_x_norm': x_normalized, 'head_y_norm': y_top_normalized}), polygons=geometry polygons)`, with geometry and G1 models taken from the labels rebuilt from the user's GT (which must equal the bundled labels exactly, as in `reproduce.py`). Before the regression these values are checked for exact equality with the panel's parameters file (`data/r15/e26_method_dev/freeze_v11/parameters/parameters.json`, SHA256 `629170e0...519d`).
- Scoring: the package's frozen E1 v2 functions, identical to v0 `src/score.py`: per-frame identity from the same output boxes (`e1.assign`, IoU >= 0.5, margin >= 0.10), `identity.event_identity` in the +-25 frame window, `e1.event_matching` (same person and direction, <= 25 frames, <= one GT height), `aggregate`, and the all-optimal matching ranges. Identity precision denominator = all final events.
- Events are derived from output-box bottom-centres. Pipelines that place points on other boxes (for example our v11 pipeline, which uses raw detection boxes) are not expressible through this interface.

## 4. Regression criteria (acceptance)

Run `score_tracker` on each of the three examples. PASS requires all of:

- R1 (primary). Merged MOT20-01+02 identity-correct matches per visibility bin, low/mid_low/mid_high/high with denominators 180/171/163/210, and matched/final events:
  - byte: 83/142/149/206, 580/644
  - oc: 70/137/147/206, 560/593
  - bot: 84/142/150/208, 584/634
- R2. Per-sequence aggregates and all 12 per-gate units (N_GT, N_final, correct, per-bin correct/GT, identity-status counts) exactly equal to the saved panel scoring.
- R3. For each of the 36 sequence/gate units: raw-candidate, C1-confirmed and final event counts equal; the ordered final-event lists equal in prediction ID, track ID, fragment index, direction, source/target frame, group ID and member prediction IDs. Crossing positions are compared numerically: the maximum absolute coordinate difference is reported; a difference above `1e-9` px is flagged as not explained by the +1/-1 round trip. The maximum point difference over all emitted output rows is also reported.
- R4. Copied-function AST equality and source-segment hashes as in Section 2.
- R5. The copied v0 `reproduce.py` still passes inside v0.1 (yolox_v11 603/724, 665 final events).

Comparisons are exact (integers and strings); no rounding. If anything differs, the difference is diagnosed and reported as FAIL; rules, tolerances, inputs and expected values are not changed after results are seen. Software crashes may be fixed and rerun; every attempt is logged in the report.

Development-only diagnostics (not part of the package): per-frame identity agreement with the saved panel `*_output_identity.jsonl.gz`, and equality of the confirmed GT events used by the panel scorer (`transitions_dev_0102.jsonl.gz`, SHA256 `49a4adf3...957d`) with the package labels.

## 5. Not claimed

A PASS shows that the package's interface reproduces the saved panel numbers from MOTChallenge text. It is not an independent clean-machine reproduction, human label QC, a test-set result, or evidence about any tracker beyond these three saved runs.
