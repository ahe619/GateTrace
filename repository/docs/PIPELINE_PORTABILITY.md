# Portable pipeline interfaces and verification scope

These wrappers call the bundled frozen functions and retain their thresholds, geometry and association logic. The source inventory is [pipeline_frozen_map.json](../metadata/pipeline_frozen_map.json). Complete-file copies and approved physical source-node slices have separate records. Python 3.10 or newer is required; `-O` and `-OO` are rejected because the frozen implementations use assertions.

## Explicit inputs and runtime outputs

Development execution accepts only `MOT20-01` and `MOT20-02`. Put private manifests beside their assets. Every asset binding has `path`, `bytes` and full lowercase `sha256`; POSIX relative paths must stay below that manifest directory. Callers explicitly prepare inputs and dependencies and supply the complete ordered frame sequence. Asset discovery, downloads and installation remain outside the wrappers.

The executable schema is [pipeline_inputs.schema.json](../configs/pipeline_inputs.schema.json); the CLI additionally checks ordered frame numbers, unique image paths, frozen checkpoint identity, path containment and numerical constraints. Runtime output directories must be new and outside the repository. Partial outputs are retained if execution fails; a completion manifest is written only after the stage succeeds. Library caches are placed inside the selected output's `runtime/` directory.

## Pixels to shared YOLOX cache

```console
python -B scripts/detect.py --manifest ../private_inputs/pixel_manifest.json
python -B scripts/detect.py --manifest ../private_inputs/pixel_manifest.json --out ../runs/yolox01 --device cuda:0 --execute
```

The first command validates only the named manifest. Image/weight access and detector initialization begin with the second command, which runs the unchanged `r15_yolox82e_detector.py`: YOLOX-X, 800×1440, confidence 0.01, NMS 0.7, FP32 construction and fusion, FP16 inference, and the original FP32 postprocessing conversion. The permitted checkpoint SHA is `e3945f3523fde1e107708aacd64dab0670c34e371d136e54587cac7a50d3cfba`; obtain that checkpoint separately.

Pixel manifests contain `schema: crowd_flow_pixel_inputs_v1`, `sequence`, `fps`, `native_size: [width,height]`, a `weight` binding, and `images: [{source_frame, binding}, ...]` consecutively from frame 1. The output is `detections.jsonl.gz` plus `cache_manifest.json`. Raw xyxy coordinates remain native 0-based coordinates; scores remain objectness × class confidence exactly once. The frozen model metadata's weight path is represented by the manifest-relative binding in the new metadata wrapper.

## Shared cache to the three author panels

```console
python -B scripts/track.py --cache ../runs/yolox01 --method byte
python -B scripts/track.py --cache ../runs/yolox01 --method byte --out ../runs/byte01 --execute
python -B scripts/track.py --cache ../runs/yolox01 --method oc --out ../runs/oc01 --execute
python -B scripts/track.py --cache ../runs/yolox01 --method bot --gmc-manifest ../private_inputs/gmc01.json --out ../runs/bot01 --execute
```

Before `--execute`, the entry point reads cache metadata only. Adapters preserve approved author parameters, FP16 admission comparison, empty-frame update behavior, output area/aspect filters and BoT-SORT file-GMC consumption. This BoT-SORT panel has ReID disabled. Its GMC manifest is `{sequence, gmc: {path, bytes, sha256}}`; the named file is copied unchanged into an output-local directory under the author's required filename.

Each output contains `MOT20-01.txt` or `MOT20-02.txt`, an observation audit and `track_manifest.json`. The MOT writer adds +1 to native left/top for standard 1-based MOTChallenge coordinates, preserving width, height and numerical precision. Collect the two explicitly generated sequence files into the input directory for `scripts/score_tracker.py`, which derives events from output-box bottom-centres. See [PIPELINE.md](../PIPELINE.md) for label, event, scoring and inspection commands.

## Native v11 cache, raw points, M4 and events

```console
python -B scripts/native_v11.py --manifest ../private_inputs/native_v11_01.json
python -B scripts/native_v11.py --manifest ../private_inputs/native_v11_01.json --out ../runs/native_v11_01 --execute
```

The manifest has `schema: crowd_flow_native_v11_inputs_v1`, `sequence`, `fps: 25`, `native_size`, `frames`, `source_kind: crowddet` or `yolox`, and explicit `cache`, `geometry`, `g1`, `m4_policy` and `detector_lineage` bindings. Geometry is the original `{sequence, lines:[six gates]}` in H_30/H_50/H_70/V_25/V_50/V_75 order. G1 retains original coefficients, native size and fitting coordinates. The M4 policy must match its original complete bytes and canonical contents; policy and geometry are supplied explicitly in their frozen versions.

The cache is a complete native-frame JSONL gzip containing `frame`, `source_frame`, `time_s` and `detections`. Each detection retains its raw index, box, confidence and class. Unchanged `fresh_raw` removes prior identity/point fields; unchanged `MethodTracker` applies M3 admission 0.10 around the pinned idxfix ByteTrack implementation. Original `point_for` uses the raw detection box. M4 remaps identities while retaining observed points, then the unchanged event adapter performs extraction, C1 and R1+R2. Native tracking disables CUDA and uses historical CPU thread settings.

Outputs are `frames.jsonl.gz`, `stitch.json`, six `gates/GATE/events.json` files and `native_manifest.json`. Events use raw detection footpoints; actual post-M4 `tracker_rows` remain available for the E1-v2 identity pool. Use the dedicated native scorer for these events. `score_tracker.py` derives a separate event stream from tracker boxes. The native generation manifest records `identity_scoring_executed: false`, frame/size/source metadata and byte/SHA bindings for all seven scoring artifacts.

Full historical drivers remain outside the package because they embed machine-specific data paths. Permitted slices preserve their source bytes and load through a new namespace/path adapter. The provenance map explicitly distinguishes these slices from complete files; see [PIPELINE_PATCHDIFF.md](PIPELINE_PATCHDIFF.md).

## Native final events to E1-v2 identity scores

```console
python -B scripts/score_native_v11.py --native-01 ../runs/native_v11_01 --native-02 ../runs/native_v11_02 --gt-root ../private_assets/train --seqinfo-root ../private_assets/train
python -B scripts/score_native_v11.py --native-01 ../runs/native_v11_01 --native-02 ../runs/native_v11_02 --gt-root ../private_assets/train --seqinfo-root ../private_assets/train --out ../runs/native_v11_scores --execute
```

The first command validates only the two `native_manifest.json` files. Reading native frames, gates, GT and seqinfo begins during execution, which requires both exact development sequences, one shared detector source kind and NumPy 2.2.6. GT paths are restricted to `GT_ROOT/MOT20-01/gt/gt.txt` and `GT_ROOT/MOT20-02/gt/gt.txt`; seqinfo paths are `SEQINFO_ROOT/MOT20-01/seqinfo.ini` and `SEQINFO_ROOT/MOT20-02/seqinfo.ini`. The unchanged `input_paths` guard rejects forbidden roots and redirected paths before opening contents. The frozen builder verifies four official input hashes and reconstructs 724 whole-sequence confirmed events. Existing labels and historical score answers remain outside this explicit-input computation.

The adapter verifies core source bytes against `core_frozen_map.json`, loads them in a private namespace, and calls original label, E1-v2 pool/assignment, identity, event-matching, exact-optimum-range and aggregation functions. `e1.pools(frame, 'v11')` validates actual post-M4 output rows, admitted raw indices and M4 lineage. Saved `final_events` retain their coordinates and event semantics. Identities are recomputed; saved `_identity` or `identity_association` answers are rejected. Unknown, ambiguous, mixed and ignored events remain in the ALL-final precision denominator.

Outputs include rebuilt `labels/`, frame-level identity evidence, per-gate matching evidence, `units.json`, `matching_ranges.json`, `scores.json` and a read ledger. Reports contain low/mid-low/mid-high/high, overall and precision numerator/denominator pairs and per-sequence aggregates. The core's example-specific `score()` driver has a separate parity contract tied to a different bundled example. This adapter scores the supplied artifacts; historical equivalence requires its own comparison receipt.

The original interface snapshot was **NOT_REAL_DATA_REGRESSED**, retained in [native_v11_scoring_status.json](../metadata/native_v11_scoring_status.json) and historical manifests/reports. Ten synthetic tests validate interface behavior and frozen-kernel composition. Real-input equivalence has a later local receipt with status **LOCAL_EQUIVALENCE_PASS_PENDING_CLAUDE_RECOMPUTE**; see the [status addendum](NATIVE101A_STATUS_ADDENDUM.md). Inspector integration carried forward that receipt. Claude acceptance and clean-machine validation remained separate pending gates.

## Frozen confirmation command generation

```console
python -B scripts/confirm.py --workspace ../private_confirmation_workspace --manifest docs/manifest.json --manifest-sha256 MANIFEST_SHA256 --approval docs/approval.json --approval-sha256 APPROVAL_SHA256 --out data/r15/confirmation85/commands
```

Supply the actual two control-document hashes and an explicit workspace outside the repository. The wrapper deploys five complete frozen files under `workspace/scripts/confirmation85/production_v1/`, checking containment and symlink/junction/reparse redirection before writing. The original `ROOT` expression resolves to that workspace, preserving frozen path guards. Existing deployed code must match byte-for-byte. Control/output arguments are workspace-relative under the original guard: controls belong under `docs/` or `data/r15/confirmation85/`, and generated commands under the latter.

Original `command.py generate` runs in an isolated standard-library Python child process and applies the complete production schema in [manifest.py](../src/confirm/production_v1/manifest.py). Fields are `schema`, `manifest_id`, `producer`, `scope`, `sequences`, `systems`, `assets`, `freeze`, `reference_modes`, `run_root`, `resources`, `interpreters` and `runtime_roots`; asset and interpreter entries bind bytes, hashes and paths. P2/O1 require explicit `import_existing`, with rebuilding outside this contract.

The generator writes 18 scientific-stage commands plus receipt collection: two exports, seven systems per sequence, seal and score. The generated future script calculates dynamic handoff/seal hashes. Generation reads the control manifest and local control-source bytes, renders the approval path as text, and statically checks worker presence. Scientific-asset reads and execution of `run.py`, the generated shell script, detector, tracker and scorer belong to the separately authorized stage. That stage requires complete bound runtime/source/asset closure. Command generation documents preparation; actual confirmation and seven-system deployment have separate execution receipts.

## Analysis primitives

```console
python -B scripts/analysis.py e2-mask --input ../private_inputs/e2.json --out ../runs/e2_mask.json
python -B scripts/analysis.py d1-gaps --input ../private_inputs/d1.json --out ../runs/d1_gaps.json
python -B scripts/analysis.py headgate-project --input ../private_inputs/heads.json --out ../runs/projected_heads.json
python -B scripts/analysis.py gatelink --input ../private_inputs/gatelink.json --out ../runs/gatelink.json
python -B scripts/analysis.py reid-decision --input ../private_inputs/reid_summary.json --out ../runs/reid_decision.json
```

All analysis inputs have an explicit development `sequence`. The actions call the existing kernels:

| Action | Additional input fields | Scope |
|---|---|---|
| `e2-mask` | `observations` with sequence_id/identity_id/frame/visibility_bin; `fps`, frozen `retention`, `seed`, `mode` | Original mask generation; no detector/tracker degradation run |
| `d1-gaps` | `timelines` keyed by track ID, ordered source_frame/point observations; `fps` | Original gap description |
| `headgate-project` | `native_size`, frozen `calibration.coefficients_a_b`, head `detections` | Original MOT projection; no head detector, calibration fit or oracle evaluation |
| `gatelink` | MOT rows, `mode: bridge/link`, `max_gap_frames: 50/125`; `valid_identities` for link | Original oracle transformation; no new identity assignment or scoring |
| `e1-pools` | original frame record and `system` | Original admitted/output-box pool validation |
| `e1-attribute` | original `attribute` keyword arguments; fragment_lookup represented as source_frame/track_id/fragment records | Original attribution precedence on explicitly supplied evidence; no reconstructed evidence pipeline |
| `m4-stitch` | frames, namespace, fps, gates, g1 and exact policy | Original M4 on already tracked frames |
| `reid-decision` | original scoring `report` with main.aggregate and main.by_sequence | Exact original frozen decision; its historical pending-recompute field is retained |
| `reid-support` | original `supports` dictionaries | Exact original side-support categories |

Each primitive covers its stated operation within a historical analysis. E1 remains an output-level description and E2 a specified intervention; oracle and negative-result interpretations retain their established scope. ReID appearance inference, new tracker configurations and causal interventions require their own implementation and evidence.

## Environment and validation

Standard-library tests and control generation require Python 3.10+. GPU detection additionally needs compatible NumPy, Torch, torchvision, OpenCV and loguru. Panel tracking needs NumPy, Torch, SciPy, LAP, OpenCV, FilterPy and matplotlib. Native idxfix tracking also requires pinned Ultralytics 8.3.192 and its frozen tracker YAML/source SHA. Missing dependencies produce a failure; prepare them explicitly before execution.

Historical metadata records NumPy 2.2.6, Torch 2.10.0+cu128, torchvision 0.25.0+cu128, SciPy 1.15.3, FilterPy 1.4.5, OpenCV 4.12.0.88, Ultralytics 8.3.192 and LAP 0.5.13. These versions describe the observed environment. A universal installable dependency lock and cross-hardware bitwise inference each require separate validation.

```console
python -I -S -B tests/test_pipeline_portability.py
python -B tests/test_native_v11_scoring.py
```

Sixteen synthetic tests cover complete-source hashes, input/path rejection, native frame ordering, external outputs, E2 masks, D1, head projection, GateLink, E1 precedence, raw-point native events, original-node cleanup, ReID thresholds, optimized-Python rejection, deployment containment and real-guard generation of the full 18-command plan in an external workspace. Scientific execution and the GPU pixel wrapper remained outside packaging checks. Separately authorized 01/02 CPU equivalence regression needs its own result and receipt.

The ten native-scoring tests cover the bound seven-artifact contract, output-box identity coordinates, M4 lineage rejection, original assignment on synthetic GT text, preserved native event positions, fresh identity matching, ALL-final unknown denominators, rejection of old identity answers, manifest-only preflight, optimized-Python rejection and development path checks before content reads. All ten passed with Python 3.10.18 and NumPy 2.2.6. The assignment test uses existing NumPy and explicitly skips when unavailable; production scoring requires the reference version. Both suites use synthetic inputs. The complete production scorer has a separate execution scope.