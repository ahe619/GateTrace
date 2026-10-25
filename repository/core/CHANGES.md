# Derived fields and retained sources

- Source GT coordinates are converted from MOT's 1-based x/y to the frozen 0-based continuous-box convention. Source frame numbers remain 1-based; time in seconds is `(source_frame - 1) / 25`.
- A simple height relation fitted from the development GT defines the frozen six virtual gates per sequence. The geometry is defined in image coordinates; metric ground-plane calibration is outside its scope.
- A transition is derived when an annotated body's valid bottom-centre point changes non-gap region. Rule confirmation, the original supporting observations, and unconfirmed transitions are preserved.
- The visibility field is the frozen mean of available GT visibility values in the event's ±25-frame support window. Its scope is the annotated body visibility over that window; instantaneous human judgments and face/head visibility require separate observations.
- Missing observations remain missing. Source-annotator interpolation is unspecified in these files and is recorded as unknown where applicable.
- `rule_confirmed` records confirmation under the frozen rule; visual evidence of the crossing is a separate question. Body boxes may include occluded/amodal extent, and the box bottom can be an estimate. Human QC remains `not_reviewed` in this sample.
- The example export removes local machine paths and precomputed identity judgments. The scorer rebuilds identity from actual output track boxes and the user-supplied public GT using the frozen E1 v2 rules.
- All-optimal matching ranges describe the minimum/maximum stratum counts among equally optimal global pairings. Their scope is ambiguity among equally optimal pairings; statistical confidence and sampling uncertainty require separate analyses.

Historical source data, frozen scripts and system outputs remain unchanged. The package consumes saved detector and tracker outputs and preserves their thresholds, event rules and scientific decision criteria.

# v0.1 (2026-10-24): tracker-output scoring interface

v0.1 is a copy of v0 with additions only. Of the 51 files listed in the v0 manifest, 49 are byte-identical; `README.md` and `CHANGES.md` are extended, and `MANIFEST.json` is regenerated and lists the changed and added files. `reproduce.py`, labels, the yolox_v11 example and its expected scores are unchanged.

Added:

- `score_tracker.py`: one-command scoring of MOTChallenge result files for MOT20-01/02, plus `--self-test`.
- `src/frozen_events/`: verbatim copies of the event-chain functions used by the published-tracker panel run (the 20 members compiled by the project's `load_frozen`, the `FrozenEvents` adapter and `make_height_model`, `point_for`, `event_view`), with `provenance.json` (source file SHA256; per member line span, source-segment SHA256 and AST SHA256). The source-segment hashes equal the function audit saved by each of the six panel runs.
- `src/events.py`, `src/motchallenge.py`, `src/tracker_score.py`, `src/regression.py`: input parsing, orchestration, scoring loop (same frozen E1 v2 functions and loop as `src/score.py`) and self-test comparison. Numerical rules are supplied by the frozen functions.
- `examples/panel/{byte,oc,bot}/MOT20-0{1,2}.txt`: the three saved panel tracker outputs as MOTChallenge rows (repr-precision coordinates, emitted row order), with `examples/panel/source_manifest.json`.
- `expected/panel_{byte,oc,bot}.json`: saved panel scores (main, per-sequence, 12 gate units) and saved final events per gate.
- `PROTOCOL.md` (+ `PROTOCOL.md.sha256`, written before any v0.1 code was run on real data) and `REPORT_v0_1.md`.

Changed: `README.md` (v0.1 title and a "Score a tracker" section), `CHANGES.md` (this section), `MANIFEST.json` (all files; same schema string so `reproduce.py` still verifies the package; adds `package_version`).

Preserved: every frozen scientific function, threshold, label, geometry, height model and scoring rule. The scorer derives events only from output-box bottom-centres; pipelines that place points elsewhere (such as v11 on raw detection boxes) are outside this interface.
