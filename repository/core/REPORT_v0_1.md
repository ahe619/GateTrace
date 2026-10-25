# v0.1 construction and regression report

Date: 2026-10-24. This package was assembled with AI assistance under human supervision. The protocol was written and hashed before any real-data run; every run attempt was logged. Key numbers were checked with a separately implemented AI-assisted driver. Scope: technical reproduction on the same machine; independent human validation remained pending.

**Result: all three regressions PASS** (byte, oc, bot), together with the gate-level event comparison and all supporting checks. Label human QC remained `not_reviewed`, and independent clean-machine reproduction was pending at the time of this report.

## 1. What was added
- `score_tracker.py`: the CLI. `--tracks DIR` scores `MOT20-01.txt` and `MOT20-02.txt`; `--self-test` scores `examples/panel/{byte,oc,bot}` and compares them with `expected/panel_*.json`.
- `src/frozen_events/chain.py`: verbatim copies of the 20 members compiled by `scripts/r15e24_events.py::load_frozen`, in its order. They share one namespace equal to load_frozen's (`math`, `defaultdict`, `Counter`, `deepcopy`, `np`).
- `src/frozen_events/adapter.py`: `C1_KEY`, `make_height_model` and `FrozenEvents`, copied verbatim.
- `point.py`: `point_for`, copied verbatim from `scripts/r15e24_run55.py`.
- `event_view.py`: `event_view`, copied verbatim from `scripts/sota83d/event_view.py`.
- `provenance.json`: for each source file, its SHA256; for each member, its line span, source-segment SHA256 and AST SHA256.
- Wrappers using the frozen numerical rules:
  - `src/motchallenge.py`: strict parsing and the +1/−1 conversion.
  - `src/events.py`: observation building and per-gate chain calls.
  - `src/tracker_score.py`: the v0 `src/score.py` loop with frozen E1 v2, run on freshly derived events.
  - `src/regression.py`: the self-test comparison.
- `examples/panel/{byte,oc,bot}/MOT20-0{1,2}.txt`: 447,812 rows written with `repr` precision, in each tracker's emitted row order. `examples/panel/source_manifest.json` records the sources.
- `expected/panel_{byte,oc,bot}.json`: the saved main and per-sequence aggregates, the 12 gate units, and the saved final events of all 36 gates.
- `PROTOCOL.md` (SHA256 `e46ebc5dc9a1df92a2ee0485aab596c7f8052bb981dd38ee6dca0e26e7277036`) and `PROTOCOL.md.sha256`.

`README.md` gained a "Score a tracker" section and `CHANGES.md` a v0.1 section. Of the 51 v0 files, the other 49 are byte-identical. The v0 package still verifies against its own manifest (`15e6bbaa…`).

## 2. Provenance

The AST hash is `sha256(ast.dump(node, include_attributes=False))` under CPython 3.10.18, the same method as v0 `frozen_score`. The builder refuses to write a copy whose AST or source segment differs from the source. For all 20 load_frozen members, the source-segment hashes and line spans equal the `event_functions` audit saved by each of the six panel runs. `point_for`'s source-file hash equals each run's `point_function_source`. A static check confirmed that every global name read by a copied member lies inside load_frozen's namespace.

| Source | SHA256 | Members |
|---|---|---|
| `r15e3_regions_common.py` | `e2dd5687…` | nearest_boundary, signed_distance |
| `r15e3_e2_core.py` | `a9d4ef47…` | zone_from_distances, extract_region_events |
| `r15e6_core.py` | `91bb6c59…` | height_at_foot, edge_distance, evidence |
| `r15_dedup_direction.py` | `dbf70dc6…` | VARIANTS, SOURCE_ZONE, TARGET_ZONE, _event_frame, _event_key, _valid_point, _observation_detail, _window, transform_events |
| `r15e3_head.py` | `e67a1c05…` | finite_point, keypoint_mean, predict_height, select_point |
| `r15e24_events.py` | `14ddf655…` | C1_KEY, make_height_model, FrozenEvents |
| `r15e24_run55.py` | `90d81ca9…` | point_for |
| `sota83d/event_view.py` | `35ed003f…` | event_view |

Output file hashes:
- `chain.py` `0e0bfb5f3fe68b49dd6ceea8af2923aef8b143cf65bb34f316d78af04173b7e8`
- `adapter.py` `1290edbd86a16ff88a8e8d7d5481dee816ef261809be84debae758db4ab637bc`
- `point.py` `21f4a33f76ac0975c6d6b65efa2552b362befb6ec0e259a592f9417ac3d64813`
- `event_view.py` `05a4e9a7e77d65f0d7e1f1c436cda091db77f685e9edfc42f50781cc1d024947`
- `provenance.json` `457d7854ee6f151b1cc073396de38db6261d69581d363a9ad17757dbd355bb51`

## 3. Pre-regression checks
- **Panel inputs unchanged:** all 57 files bound by `score_inputs.json` were re-hashed, with 0 mismatches.
- **Geometry and height models equal the panel parameters** (`parameters.json`, `629170e0…`): 12 polygon sets, 12 facing-edge sets, 2 coefficient sets, 2 fitting ranges and 2 native sizes, 30/30 exactly equal.
- **Confirmed GT events equal:** the panel scorer's events (from `transitions_dev_0102.jsonl.gz`) and the package labels agree in 12/12 sequence/gate units, 724 events in total.
- **Copied chain equals the original chain:** on the saved panel observations, it equals the original `load_frozen` in memory in 36/36 units. Its output also equals the saved `events.json` in 36/36 units (all fields except `function_audit`).
- **Saved points:** the saved `point` equals frozen `point_for` for all 447,812 rows.
- **Synthetic interface checks:** 20/20 pass.

## 4. Regression results

Run `data/r15/release_v0_1_build/runs/selftest_attempt1`: 03:46–03:49 EDT, exit code 0, 153.6 s. Results are merged over MOT20-01 and MOT20-02.

| Tracker | low /180 | mid_low /171 | mid_high /163 | high /210 | matched / final | R1 | R2 | R3 |
|---|---:|---:|---:|---:|---:|---|---|---|
| byte | 83 | 142 | 149 | 206 | 580/644 | PASS | PASS | PASS |
| oc | 70 | 137 | 147 | 206 | 560/593 | PASS | PASS | PASS |
| bot | 84 | 142 | 150 | 208 | 584/634 | PASS | PASS | PASS |

**R3:** the candidate, confirmed and final counts are equal in all 36 units. All 1,871 final events have the same prediction ID, track ID, fragment, direction, source and target frames, group ID and member IDs. The maximum crossing-position difference is 0.0 px (the bound was 1e-9 px).

**Round trip:** 740 of 447,812 boxes change, by at most 2.27e-13 px. 167 valid points change, by at most 2.27e-13 px. Point validity is unchanged, as are all final-event target points.

**Per-frame identities equal the saved panel scoring:**
- 0 differences in track ID, row index, GT ID, class or status.
- Assignment pairs are identical in all 6,422 frames.
- IoU and margin differ by at most 8.1e-15.

**R5:** `reproduce.py` inside v0.1 passes (`runs/reproduce_attempt2`: 603/724, 665 final events, parity PASS).

**Matching ranges:** the identity matching ranges collapse to a single value for all three trackers; in every bin, minimum = canonical = maximum.

**Independent recompute:** a separate subagent wrote its own driver (`data/r15/release_v0_1_build/independent_check/`) using only the original `scripts/` code on the six text files. Its numbers match the saved panel scores and units, the v0.1 run, and the saved final events (max position difference 0.0 px). It confirmed that `scripts/` and `release/` were unchanged.

## 5. Attempt log
1. Copied v0 to v0.1; `diff -r` showed them identical. Wrote and hashed the protocol at 03:39.
2. Built the frozen copies and the examples/expected files, once each.
3. Ran the Section 3 checks.
4. `selftest_attempt1`: PASS.
5. `reproduce_attempt1`: refused at manifest verification, because README and CHANGES were edited after the development manifest was built. The attempt ended before output creation. After rebuilding the manifest, `reproduce_attempt2`: PASS.
6. Independent recompute: PASS.
7. Built the pre-report manifest (`d3c4aa178d4e500c7aee284c6632c694ecbf7dc7c3103fd0445ea19a917f10c1`):
   - `runs/selftest_final`: SELF_TEST_PASS; units identical to attempt 1.
   - `runs/reproduce_final`: PASS, 603/665.

Rules, inputs, tolerances and expected values remained fixed after results were seen. At this stage of the build, the final package receipt still required a run after adding this file and rebuilding the manifest.

## 6. Commands
```
python -B score_tracker.py --gt-root GT --seqinfo-root SEQINFO --tracks DIR --out NEW_DIR
python -B score_tracker.py --self-test --gt-root GT --seqinfo-root SEQINFO --out NEW_DIR
python -B reproduce.py --gt-root GT --seqinfo-root SEQINFO --out NEW_DIR
```
Interpreter: `data/venvs/r11_measure` (CPython 3.10.18, NumPy 2.2.6). Build helpers and diagnostics are in `data/r15/release_v0_1_build/`.

## 7. Limitations
- **Bottom-centre points only.** Events are derived only from output-box bottom-centres, so v11 (which places points on raw detection boxes) cannot use this interface and stays on `reproduce.py`.
- **Development data only.** Scope: MOT20-01/02 with hash-bound GT. Test-set evaluation is outside this report.
- **Same machine and stack.** The parity evidence covers this machine, stack, and the recorded trackers. Clean-machine reproduction and human label QC remained separate requirements.
- **Row order matters.** Identity ties follow row order within a frame.
- **Panel provenance.** The panel outputs come from the project's runs of the authors' code on saved detections. Published result files from the authors have separate provenance.
- **No `-O`.** The CLI refuses `python -O`, because the frozen functions use `assert`.
- **Size.** The example files total about 44 MB.
