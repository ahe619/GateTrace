# Inspector integration candidate

Historical native-v11 regression status is summarized in [NATIVE101A_STATUS_ADDENDUM](docs/NATIVE101A_STATUS_ADDENDUM.md), copied from the project docs/research_pressure_test_round2_20261025/NATIVE101A_STATUS_ADDENDUM.md. The existing receipt SHA is a23ca615e0ce945f2f64380347516333b1d0c816e59bc9e5b3330e4b902ebdb0, with status LOCAL_EQUIVALENCE_PASS_PENDING_CLAUDE_RECOMPUTE. The integration carried forward this receipt; Claude approval remained pending.

This repository copy added inspector integrity adapters reviewed in code, the saved-score inspection entry point and synthetic engineering tests. The original repository and source packages retained their existing contents. At this snapshot, Claude approval was pending, and the integration work used existing real-data regression and scientific-scoring evidence.

At the inspector integration, two display-layer files received explicit presentation_layer_revision records in FROZEN_CODE_MAP.json, with their complete former entries retained as previous_provenance. Those records distinguished the revisions from complete unchanged copies. Other map entries and frozen scientific code retained their original bytes/values. Historical status fields preserve the acceptance record at each stage. The later editorial localization of the review templates and synthetic UI test is recorded as presentation revisions with prior provenance and before/after hashes.

The repository verifier has one additional exception bound to an exact file SHA and line number for an intentionally invalid synthetic path. The original numeric GT-line exception and scientific hash checks remain intact. See metadata/inspector_verifier_compatibility.patch.

Run the engineering check from the repository root:

```text
python -B core/check_inspector.py --out NEW_EXTERNAL_CHECK_DIRECTORY
```

Prepare Pillow separately for synthetic rendering. The optional standard-library-only check is:

```text
python -S -B core/check_inspector.py --stdlib-only --out NEW_EXTERNAL_STDLIB_DIRECTORY
```

The saved-score entry point is core/inspect_saved_event.py. Use --help for explicit input paths and the separately retained evidence SHA. Existing unsealed scores keep their status. Original data/model/annotation restrictions continue to apply, and public release requires separate authorization.

The practical v2 copy clarified existing semantics and status; see [PRACTICAL_V2_STATUS](PRACTICAL_V2_STATUS.md). Its engineering acceptance was inherited from the prior candidate.
