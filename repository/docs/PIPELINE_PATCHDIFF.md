# Source preservation and portability differences

The authoritative inventory is [metadata/pipeline_frozen_map.json](../metadata/pipeline_frozen_map.json). Each complete copy records its original project-relative path, repository-relative path, exact SHA256 and byte count. Each approved fragment records the original complete-file SHA256/bytes, physical line interval, node name, exact fragment SHA256/bytes and repository path. Direct byte slicing preserves original line endings, whitespace and function bodies.

At packaging, the pipeline inventory contains 54 complete source/license files and 16 unchanged physical source-node slices. Complete copies include the existing YOLOX adapter/vendor, approved author panel/vendor code and licenses, idxfix, M4, six event-adapter/source files, E1/E2/HeadGate/D1/GateLink kernels, and five production control/worker modules. Vendor compatibility edits were already present in the approved project sources. These copies preserve that project version; upstream originals have their own provenance. Copyright and license notices remain beside the vendor code.

## Explicitly permitted node slices

The user explicitly permitted unchanged source slices with full provenance and differences because some application files contain machine-specific paths. The map distinguishes these from complete files:

- `r15e26_run_v2.py`: `MethodTracker`, `fresh_raw`.
- `r15e24_inference.py`: `SEED`, `TRACKER_ADAPTER_SHA`, `IDXFIX_SHA`, `_require`, `_bound_bytes`, `_load_adapter`, `_register_packages`, `_seed`, `ByteTrackTracker`.
- `r15e24_run55.py`: `point_for`.
- `r15_reid93_analysis.py`: `RULES_SHA`, `fraction_value`, `decision`, `sidecat`.

Only the named nodes are loaded. Surrounding driver globals, readers, schedulers, top-level work, output directories and unrelated detector branches remain outside the extracted files. Public records describe structural differences and hashes; private path literals stay in the excluded source files.

## New wrapper behavior

| Area | Old application dependency | New declared I/O/import adaptation | Scientific body change |
|---|---|---|---|
| YOLOX | Application-selected local images/weight | Explicit ordered byte/hash-bound image manifest and output-local caches | None |
| Author panels | Project run directory and shared cache | Explicit cache binding; unchanged GMC bytes staged with the author-required filename | None |
| Standard export | Native 0-based tracker xyxy | MOTChallenge serialization adds 1 to left/top, keeps width/height; matches the frozen standard parser's inverse | None |
| Native v11 source loader | `_root()/scripts` and old application import | Runtime source root with the two unchanged tracker helpers; explicit namespace injection for `_root`, copy/math/require and frozen idxfix hash | None in selected nodes |
| Native v11 events | Old application read/dispatch loops | Explicit cache/geometry/G1/policy bindings; same raw detection point function, original M4 and original event API | None |
| Native identity scoring | Actual post-M4 tracker output boxes plus native final events | Explicit 01/02 native output roots and GT/seqinfo roots; original core label/E1/identity/matching/aggregate functions, with saved native final events consumed directly | No frozen function changes |
| ReID analysis | Old fixed result locations and shared global rule hash | Explicit original-format summary/support JSON; original rule constant and functions | None in selected nodes |
| Confirmation | Root-relative original control directories | Five byte-identical files deployed under the original directory depth in an explicit external workspace | No schema/path guard/worker change |
| Safety/preflight | Implicit environment/runtime assumptions | Reject optimized Python, offline runtime, no dependency installation, external new outputs, explicit execute flags | No parameter changes |

## Excluded complete files

The historical YOLOX `SOURCE_MANIFEST.json` contains private build roots and remains outside this package. The new relative inventory replaces its publication metadata, while selected scientific/vendor files and original license notices retain their existing bytes.

The complete `r15e26_run_v2.py`, `r15e24_inference.py` and `r15_reid93_analysis.py` applications contain machine-specific data or weight locations. The map records their full hashes and exclusion reasons. Publication covers the approved nodes above, with full drivers retained separately. Real data, weights, private annotation answers and original confirmation products remain outside these adapters.

The first wrapper test found a Windows root-relative path acceptance case; the new I/O layer now rejects leading `/` explicitly. Independent interface review also corrected the MOT writer to use standard 1-based left/top coordinates. Both fixes apply to new wrappers; frozen scientific files retain their original bytes. The final synthetic suite passed with these adapters.

The native scorer reuses the scientific sources in [core_frozen_map.json](../metadata/core_frozen_map.json), with exact called functions listed in [native_v11_scoring_status.json](../metadata/native_v11_scoring_status.json). New orchestration replaces the historical application's fixed input/result paths with explicit inputs and hash-bound native artifacts. It uses the original whole-sequence labels and frozen assignment, identity, event-matching, range and aggregation functions. The example-specific `score()` parity driver and standard tracker-box event decoder have separate contracts. Input events retain their stored bytes; new `native_manifest.json` fields bind those bytes and actual tracker frames separately. Historical status was **NOT_REAL_DATA_REGRESSED**. A later local development-equivalence receipt records **LOCAL_EQUIVALENCE_PASS_PENDING_CLAUDE_RECOMPUTE**; see the [status addendum](NATIVE101A_STATUS_ADDENDUM.md). Inspector integration carried forward that receipt, with Claude acceptance pending.