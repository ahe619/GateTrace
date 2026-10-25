# GateTrace

Identity-qualified crossing evaluation and event evidence for crowded scenes.

Start with the [coauthor guide](../START_HERE.md) or explore the owner-supplied standalone repository guide.

**Historical delivery status:** this directory was a local candidate awaiting Claude review. Native v11 had a local development-equivalence receipt with status `LOCAL_EQUIVALENCE_PASS_PENDING_CLAUDE_RECOMPUTE`; independent acceptance remained pending. The integration covered presentation engineering and documentation, retaining the scientific values and execution permissions. The existing real-data regression receipt was carried forward. See [version status](PRACTICAL_V2_STATUS.md) and [receipt details](docs/NATIVE101A_STATUS_ADDENDUM.md).

This repository lets collaborators examine a specific question: **as crowd occlusion increases, does the system report a person's crossing with the correct identity, direction and time?** It provides derived labels for public MOT20 development data, a frozen scorer, standard-track interfaces, numerical examples and historical findings. YOLOX＋v11 is the project's strong baseline assembled from established components. The recorded comparisons use established tracker components and their specified settings; the claim boundaries are detailed in the linked interpretation guide.

The confirmation result is as follows: among pooled low-visibility events in MOT20-03/05, YOLOX＋v11 recovers 184/427（43.1%） and ByteTrack recovers 140/427（32.8%）, an absolute difference of 10.3 percentage points. More than half remain unrecovered by the former. Confirmation criteria are evaluated separately for each sequence; pooled counts are descriptive. See [RESULTS](RESULTS.md) for all values and recomputation coverage, and [claims_and_limits](docs/claims_and_limits.md) for interpretation. Source: S22; source-relative paths and full SHA256 values appear in the [documentation ledger](metadata/docs_sources.json).

## Core concepts

- **Detection:** a box marks a possible person in one frame. **Tracking:** boxes believed to belong to the same person are linked across frames and assigned a trajectory ID. Identity correctness still requires evidence.
- **Crossing event (region transition):** a reference point moves between fixed regions under the frozen rules. The reference time is the first observed valid point in the target region, and the reference position is that frame's point. C1 confirmation has its own time. The extractor evaluates region transitions; finite yellow-line intersections and physical body crossings require additional geometric interpretation. Gates are evaluation geometries in image coordinates.
- **IVR (identity-qualified crossing recovery):** the denominator is rule-confirmed reference crossings, and the numerator counts matches with the correct person and direction within the allowed time and position errors. Recovering 99 of 180 reference events gives 55.0%. The time tolerance is 1 second and the position tolerance is the person's reference-box height.
- **Identity precision:** the fraction of final system events that correctly match reference events. Its denominator includes every final event, including unknown, mixed and ignored identities.
- **Visibility:** the reference annotation describes how much of a person is visible. Events use the mean within 1 second before and after the first target-region entry and fall into low, mid-low, mid-high and high bins at 0.25, 0.50 and 0.75. Frame-level metrics use individual frame values and a separate denominator.
- **Identity-valid output:** under the frozen identity rules, an output box supports association with the reference person. Missing support on one side can involve detection, association, rules or insufficient evidence; visual visibility remains a separate question.

These definitions and examples come from S04, S20 and S21. A person may cross several gates, so repeated events from the same person or video are statistically dependent. O1 uses reference full-body boxes as a diagnostic under stronger input information; recovery of occluded image evidence requires separate support.

## Run the minimal CPU path

Run from the repository root. The reference core environment is **Python 3.10.18 + NumPy 2.2.6**. CPU execution uses this minimal environment, with GPU dependencies managed separately. Dependency installation was outside this documentation task. With Python 3.10 already available, collaborators can manually create an external environment using the following commands.

Windows PowerShell:

```powershell
py -3.10 -m venv ..\.venv-crowd-flow-cpu
& ..\.venv-crowd-flow-cpu\Scripts\python.exe -m pip install -r requirements-cpu.txt
& ..\.venv-crowd-flow-cpu\Scripts\python.exe -c "import sys,numpy; print(sys.version); print(numpy.__version__)"
& ..\.venv-crowd-flow-cpu\Scripts\python.exe -B scripts/run_resource_synthetic.py
```

Linux / macOS:

```sh
python3.10 -m venv ../.venv-crowd-flow-cpu
../.venv-crowd-flow-cpu/bin/python -m pip install -r requirements-cpu.txt
../.venv-crowd-flow-cpu/bin/python -c "import sys,numpy; print(sys.version); print(numpy.__version__)"
../.venv-crowd-flow-cpu/bin/python -B scripts/run_resource_synthetic.py
```

Check the printed versions first. `requirements-cpu.txt` pins NumPy 2.2.6; the reference Python patch version 3.10.18 must be prepared separately. The synthetic checks use synthetic inputs on CPU. In the commands below, replace `python` with the explicit interpreter path above to select the intended virtual environment.

Prepare lawfully acquired MOT20-01/02 annotations and sequence metadata as described in [DATA](DATA.md). Replace the uppercase path placeholders before execution. `NEW_OUT` must be a **new, nonexistent directory outside the repository**.

```text
python -B scripts/reproduce.py --gt-root GT_TRAIN_ROOT --seqinfo-root SEQINFO_TRAIN_ROOT --out NEW_OUT
python -B scripts/score_tracker.py --self-test --gt-root GT_TRAIN_ROOT --seqinfo-root SEQINFO_TRAIN_ROOT --out ANOTHER_NEW_OUT
```

The first command reconstructs labels from local official GT and checks the existing numerical example. The second checks scoring regression for the three bundled standard-track examples. Recorded same-machine times were approximately 39.5 and 167.1 seconds, respectively; all three panel rows passed. These timings describe that machine. Both paths consume cached outputs. Reconstruction status remains `COMPLETE_PENDING_INDEPENDENT_REPRODUCTION_AND_HUMAN_QC`; full pixel execution and independent acceptance on another machine have separate gates. See [VERIFY](VERIFY.md) for the executed checks.

## Score your own tracks

Place `MOT20-01.txt` and `MOT20-02.txt` in one directory. Each row has 10 columns:

```text
frame,id,x,y,width,height,confidence,-1,-1,-1
```

Frame numbers and left/top coordinates are 1-based. Preserve input row order within each frame. Invalid rows produce an error and require correction by the caller. Follow the full contract in the [frozen-core guide](core/README.md).

```text
python -B scripts/score_tracker.py --gt-root GT_TRAIN_ROOT --seqinfo-root SEQINFO_TRAIN_ROOT --tracks TRACKS_DIR --name tracker --out NEW_SCORE_OUT
python -B scripts/inspect_event.py --gt-root GT_TRAIN_ROOT --seqinfo-root SEQINFO_TRAIN_ROOT --tracks TRACKS_DIR --list-misses --bin low --out NEW_INSPECT_OUT
```

This interface derives events from track-box bottom-centres. Historical v11 uses raw detection footpoints as well; preserving its event semantics requires the dedicated native artifacts and interface.

Native v11 has separate `native_v11.py` and `score_native_v11.py` entry points that connect original-footpoint events with identity scoring from actual output boxes; commands appear in [PIPELINE](PIPELINE.md). The scoring path passed 10 synthetic checks and initially carried **`NOT_REAL_DATA_REGRESSED`**. A subsequent development-equivalence run obtained **`LOCAL_EQUIVALENCE_PASS_PENDING_CLAUDE_RECOMPUTE`**; see the [status addendum](docs/NATIVE101A_STATUS_ADDENDUM.md). The inspector integration carried forward this local receipt; Claude review and full GPU acceptance remained pending in that snapshot. The scorer reconstructs identities from current inputs, while equivalence acceptance has its own evidence. See [native_v11_scoring_status](metadata/native_v11_scoring_status.json) and sources S32–S34 for provenance and historical status.

## Read by purpose

|Purpose|Entry point|
|---|---|
|Understand data, detection, events and scoring|[PIPELINE.md](PIPELINE.md)|
|Read research tables and recomputation status|[RESULTS.md](RESULTS.md)|
|Check data/weight sources and license scope|[DATA.md](DATA.md)|
|Follow successful, unsuccessful and stopped routes|[HISTORY.md](HISTORY.md)|
|Review supported conclusions and pending evidence|[docs/claims_and_limits.md](docs/claims_and_limits.md)|
|Check pixel-workflow input contracts and portability scope|[docs/PIPELINE_PORTABILITY.md](docs/PIPELINE_PORTABILITY.md)|
|Read executed repository checks|[VERIFY.md](VERIFY.md)|
|Organize human review|[protocols/human_qc](protocols/human_qc), [review](review)|

`core/` preserves the frozen resource, `src/` and `scripts/` expose staged entry points, `configs/` contains configuration examples, and `metadata/` records provenance. Read older core README status in its historical context and use the outer documentation, latest recomputation summaries and acceptance records for handoff status.

Original images, videos, complete official GT, stadium windows, human answers and weights remain outside the distribution. In this historical snapshot, Q2/Q3 independent review, reproduction on another machine, final rights/attribution and hosted-access acceptance remained incomplete; existing human work covered MOT20-01/02. [Result limits](docs/claims_and_limits.md) retain YOLOX nondeterminism, P1/P2 exposure to 03/05, and the small desktop GPU workload during historical confirmation. Data, project code and third-party code each follow their own licenses.

