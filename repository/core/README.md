# GateTrace core: MOT20 development sample v0.1

CPU label reconstruction, track-output scoring and event inspection for GateTrace.

See the [coauthor guide](../../START_HERE.md) and owner-supplied standalone repository guide for project navigation.

**Local release candidate.** This sample supports only MOT20-01 and MOT20-02. It reproduces derived labels and evaluation on CPU from an existing system cache. Scope: a project development sample using established detector/tracker outputs. Official MOTChallenge benchmarking is outside this scope; independent reproduction and human reference validation were pending when this candidate was prepared.

**New in v0.1:** `score_tracker.py` scores any tracker's MOTChallenge-format output with one command (see "Score a tracker" below). Everything from v0, including `reproduce.py` and its yolox_v11 example, is unchanged; see CHANGES.md.

## What can a third party check?

Using their own copies of the official GT and sequence metadata, a reader can rebuild the complete virtual-gate transition population, inspect the source/target supporting frames, and recompute whether each included system event matches the same annotated person. The reader can compare anonymous and identity-qualified matching and inspect the range of visibility-stratum counts among equally optimal matchings. The cached outputs make the exact inputs, identity decisions and competing pairings available for inspection.

The contribution described here is reproducibility of the recorded evaluation. Novelty of event evaluation, identity-aware evaluation, or matching bounds, and the effectiveness of a particular repair, require separate scientific evidence.

## One command

Use Python 3.10.18 and NumPy 2.2.6 for the reference environment. NumPy is the only external runtime dependency. Prepare dependencies before execution; the program operates on local files. Obtain the original data yourself under its official terms; see ATTRIBUTION.md and DATA_LICENSE.

Expected source layout:

```text
YOUR_GT_TRAIN_ROOT/
  MOT20-01/gt/gt.txt
  MOT20-02/gt/gt.txt
YOUR_SEQINFO_TRAIN_ROOT/
  MOT20-01/seqinfo.ini
  MOT20-02/seqinfo.ini
```

From this package directory, run:

```text
python -B reproduce.py --gt-root YOUR_GT_TRAIN_ROOT --seqinfo-root YOUR_SEQINFO_TRAIN_ROOT --out NEW_RUN_DIRECTORY
```

If the GT and metadata are in one normal MOT20 train tree, omit `--seqinfo-root`. `NEW_RUN_DIRECTORY` must be a new path outside the package. Every source file is bound to its expected development hash; changed or incomplete inputs cause failure. Sequence selection uses explicit inputs.

The command verifies the package manifest, derives labels from the supplied GT, checks them against the bundled development label content, reconstructs identity associations from actual output track boxes, and recomputes the example scores. It compares the main counts to the saved reference and writes a completion receipt only after all checks pass. A failure preserves partial outputs and a failure record. Default limits are 900 seconds, 2 GiB new output, and at least 20 GiB free disk space. These limits govern execution resources; scientific thresholds remain fixed separately.

## Score a tracker (v0.1)

From this package directory, with the same GT and metadata roots as above:

```text
python -B score_tracker.py --gt-root YOUR_GT_TRAIN_ROOT --seqinfo-root YOUR_SEQINFO_TRAIN_ROOT --tracks YOUR_TRACKS_DIR --out NEW_RUN_DIRECTORY
```

`YOUR_TRACKS_DIR` must contain exactly `MOT20-01.txt` and `MOT20-02.txt` in the standard MOTChallenge result format, one row per output box: `frame,id,x,y,w,h,conf,-1,-1,-1`, with 1-based frame numbers and 1-based pixel left/top. Optional `--name` labels the run (default `tracker`).

What the command does:

1. Verifies the package manifest and the hash-bound GT/metadata, rebuilds the labels from your GT and checks them against the bundled labels, exactly as `reproduce.py` does.
2. Reads each result file strictly. Every nonblank row must have 10 finite numeric fields, an integer frame in `[1, seqLength]`, an integer ID `>= 0`, `w > 0`, `h > 0`, and a unique `(frame, id)`. Columns 7-10 are checked for validity only. Any invalid row stops the run; accepted coordinates and observations are preserved as supplied.
3. Converts each box to the frozen native zero-based continuous convention: `x0 = x-1`, `y0 = y-1`, `x1 = x0+w`, `y1 = y0+h` (the same convention as the GT parser).
4. Derives crossing events with the frozen event chain used for the published-tracker panel: each output's point is the **bottom-centre of the output box** (`point_for`; a point is invalid when `x0 <= 0`, `x1 >= width-1` or `y1 >= height-1`), then region-transition extraction with a 0.5 s track-gap reset, observed C1 confirmation (within 2 s of entry, some target-region point lies at least 0.2 G1 body heights from the target region's gate-facing edge) and R1+R2 de-duplication, per gate, with the package geometry and G1 height models.
5. Scores the final events with the frozen E1 v2 scorer. Identities are rebuilt from the **same output boxes**; within a frame, the row order in your file is the frozen tie key (the role of an emitted-output index), so keep your tracker's own row order.

Outputs in `NEW_RUN_DIRECTORY/<name>/`: `scores.json` (`summary_table` with matched/confirmed GT per visibility bin and identity precision = matched / all final events; full main aggregate, per-sequence aggregates, all-optimal matching ranges and input statistics), `units.json` (12 sequence/gate units), `final_events.json` (compact final events per gate), `events/<seq>/<gate>_events.json.gz` (full event-chain record per gate: candidates, C1 evidence, groups), `matching_ranges.json`, per-frame identity evidence and event-matching audits, plus a read ledger. The table is also printed.

**Interface limit.** Events are derived from output-box bottom-centres only. Pipelines that place event points on other boxes require a separate interface. For example, our YOLOX-X + v11 pipeline uses raw detection boxes, and v11 remains scored by `reproduce.py` from its cached final events. Under the frozen rule, boxes touching the image border give invalid event points while remaining available for identity association.

### Self-test (regression)

```text
python -B score_tracker.py --self-test --gt-root YOUR_GT_TRAIN_ROOT --seqinfo-root YOUR_SEQINFO_TRAIN_ROOT --out NEW_RUN_DIRECTORY
```

This scores the three published-tracker panel outputs in `examples/panel/{byte,oc,bot}/` (ByteTrack, OC-SORT and BoT-SORT author code, run by the project on the same saved MOT20-01/02 detections without re-detection; converted to MOTChallenge text from the saved panel run, see `examples/panel/source_manifest.json`) and compares them with `expected/panel_*.json`. It exits 0 and writes `complete.json` with status `SELF_TEST_PASS` only if all checks pass. Expected merged MOT20-01+02 results:

|Tracker|low /180|mid_low /171|mid_high /163|high /210|matched/724|matched / final events|
|---|---:|---:|---:|---:|---:|---:|
|byte|83|142|149|206|580|580/644|
|oc|70|137|147|206|560|560/593|
|bot|84|142|150|208|584|584/634|

The check also requires the per-sequence aggregates, all 12 gate units and every gate's candidate/confirmed/final event lists to equal the saved panel run. Crossing positions may differ only by floating-point rounding from the +1/-1 MOTChallenge coordinate round trip (bound `1e-9` px, fixed in PROTOCOL.md).

## Data and score semantics

- **12 virtual gates**, six per development sequence. Their image-space geometry is defined by the frozen GT height relation; real-world ground-plane calibration is outside that definition.
- The whole-sequence population contains **901 transitions: 724 rule-confirmed and 177 unconfirmed**. MOT20-01 contributes 90/74 transitions/confirmed, MOT20-02 contributes 811/650. The older core-window population is smaller (837/671); it is retained as metadata. The E1 v2 main score uses rule-confirmed events from the whole-sequence population described above.
- A valid body-box bottom-centre point changing from one non-gap region to the other produces a transition. Its timestamp is the first observed target-region entry. The recorded position is the reference point at that entry frame and remains fixed through C1 confirmation. The extractor evaluates region transitions; physical intersection with the finite centre-line segment is outside that test. Points outside both regions are treated as gap, so interpreting a region transition as a physical crossing of that finite segment requires further geometric evidence.
- The included example uses existing **YOLOX-X + v11 downstream** outputs. Identity association is rebuilt using the actual output trajectory boxes. The sample consumes the saved tracking and C1/R1/R2 event-decoding outputs.
- Main event matching requires the same GT person, the same direction, time difference at most 1 second, and native-image distance at most the frozen GT body height. Matching first maximizes cardinality, then minimizes total absolute time difference, then resolves ties deterministically.
- `IVR = identity-correct matched events / rule-confirmed GT events`. It measures recovery of the correct annotated person under these conditions. Ordinary frame-level detection recall has a separate definition. Identity precision uses **all final system events** in its denominator, including unknown, ambiguous and ignored identity states.
- Visibility is the original GT visibility averaged over available observations in the ±25-frame event window. The four bins are `[0,.25)`, `[.25,.5)`, `[.5,.75)`, and `[.75,1]`. A low value describes the recorded visibility measure; whether a body part is visually observable requires image evidence.
- A matching range describes all globally equivalent optimal pairings at fixed primary objectives. Its scope is ambiguity among equivalent optima; confidence intervals and generalization uncertainty require separate analyses. Strata are evaluated after global matching, with the global assignment retained.

Reference example, whole-sequence E1 v2 main view:

|Event visibility bin|Identity-correct matches / confirmed GT events|
|---|---:|
|low|99 / 180|
|mid_low|149 / 171|
|mid_high|150 / 163|
|high|205 / 210|
|all|603 / 724|

There are 665 final system events; identity precision is 603/665. The scorer reconstructs these values and each sequence/gate result. It also computes all-optimal bounds as additional outputs beyond the historical reference table. The anonymous `ALL_final` view uses all final events under anonymous eligibility; the older T3 clean-anonymous view uses a separate population definition.

## Contents

`labels/` contains the full transition population, geometry, fitted height models, metadata and support lineage. `examples/yolox_v11/` contains a sanitized numerical output cache from which identity decisions are reconstructed. `expected/` contains the explicitly identified saved score reference. `src/` contains project-authored frozen scientific function copies plus input/output wrappers; provenance manifests bind the copied functions. `MANIFEST.json` binds all package files. Runtime outputs go into the new directory chosen by the user.

v0.1 additions: `score_tracker.py`; `src/frozen_events/` (verbatim event-chain copies with `provenance.json`) and the wrappers `src/events.py`, `src/motchallenge.py`, `src/tracker_score.py`, `src/regression.py`; `examples/panel/` (three panel tracker outputs as MOTChallenge text); `expected/panel_*.json` (saved panel scores and final events); `PROTOCOL.md` with its hash and `REPORT_v0_1.md` (construction and regression record).

Package scope excludes original images/videos, complete source GT files, detector weights, sports-stadium material, hidden confirmation results and private human-review answers. The source path ledger used to construct this local sample remains outside the package; public-facing provenance uses asset identifiers and hashes.

## Limits and interpretation

All included labels retain **human QC = not_reviewed**. A rule-confirmed crossing can still be temporally or visually uncertain: the source full-body box can include an occluded/amodal extent and its bottom need not be a visible foot. Missing observations remain missing; source-annotator interpolation is unspecified by the GT format and is recorded as unknown.

The original v0 scope was label and score reproduction from a final-output cache. Full end-to-end pixel inference, coverage of all systems and causal attribution stages, independent clean-machine acceptance, a review interface, and evidence that the resource changes a repair decision remained outside that version. Multiple gates and events from the same person are dependent observations and require interpretation with that dependence retained.

Reference-environment parity uses exact comparisons. A different numerical stack may produce small fitting differences and fail the check; report that failure with the original rules preserved. Matching identity remains an algorithmic judgment until the separate human checks are completed.

## Rights and readiness

Derived data and numerical examples: **CC BY-NC-SA 3.0**, see DATA_LICENSE. Original package code: LICENSE_CODE; its scope excludes data and third-party libraries. See ATTRIBUTION.md and CHANGES.md. This directory was prepared as a local sample before external publication. Before public release, complete author/rights review, license-evidence archiving, an independent reproduction, and the planned human label checks. These readiness statements do not add restrictions to the granted licenses.

## Inspect one event or list misses (v0.2 candidate)

`inspect_event.py` adds a read-only evidence view. It calls the package's existing label generator, event chain, identity judge and matching functions unchanged. Its execution scope is local label and scoring evidence on MOT20-01/02; detection, tracking, training, network access and installation remain outside this entry point.

```text
python -B inspect_event.py --gt-root YOUR_GT_TRAIN_ROOT --seqinfo-root YOUR_SEQINFO_TRAIN_ROOT --event-id 01_H_50_r000001 --out NEW_EVIDENCE_DIR
python -B inspect_event.py --gt-root YOUR_GT_TRAIN_ROOT --seqinfo-root YOUR_SEQINFO_TRAIN_ROOT --tracks YOUR_TRACKS_DIR --event-id 01_H_50_r000001 --out NEW_EVIDENCE_DIR
python -B inspect_event.py --gt-root YOUR_GT_TRAIN_ROOT --seqinfo-root YOUR_SEQINFO_TRAIN_ROOT --tracks YOUR_TRACKS_DIR --list-misses --bin low --out NEW_LIST_DIR
```

The first command reports the GT person's gate, direction, observed source/target support, confirmation evidence, consecutive observed region runs, and every available visibility observation within one second (missing frames stay missing). Entry/exit values bound the supporting observations; exact physical crossing times remain unestimated. The 177 unconfirmed transitions are available for inspection and excluded from miss counts.

With `--tracks`, the frozen scorer first evaluates the entire 724-event population, then the inspector presents its canonical assignment. `event.json` contains the matched system event, time/position differences, event identity votes and their individual frame observations. For a miss it lists **all** final events at the same gate within two seconds, irrespective of identity/direction, and identity-valid output observations within 25 frames on either side of the reference entry. Spatial source/target regions are reported separately from temporal before/after. A missing output observation describes a gap in system evidence; visual visibility requires separate assessment. Equally optimal membership possibilities remain visible.

List mode writes `misses.jsonl`, one event per line. Filtering by visibility happens **after full-population matching**, with the original global pairing retained. The saved `tracker/` folder contains the unmodified frozen scorer's evidence and score outputs.

Optional rendering adds `--images YOUR_LOCAL_MOT20-01/img1 --render-out ANOTHER_NEW_DIRECTORY` to an event command. Only the selected development sequence is opened. The five fixed frame offsets are -25,-12,0,12,25, clipped to sequence bounds. GT target boxes are green, system output boxes blue, the virtual gate centre white and region edges orange/purple. The overlay covers geometry and boxes only. Pillow must already be installed. Keep rendered images outside the package and the numerical release distribution.

Run the synthetic-data tests:

```text
python -B -m unittest discover -s tests -p "test_*synthetic.py" -v
```

The new scope is evidence presentation. Human identity/label ambiguity, independent human QC, causal mechanisms, and independent clean-machine reproduction require separate assessment. At preparation of this candidate, all v0.1 scientific modules, labels and numerical examples were preserved byte-for-byte. This section updates the earlier scope to include a local evidence entry point; the other limitations remain.
