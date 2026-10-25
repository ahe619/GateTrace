# #101a status addendum: existing equivalence-regression receipt

This addendum summarizes a saved receipt. Tracking, scoring and raw-data access remained outside its preparation. The original `release/github_repo/VERIFY.md`, `codex_reports/r15_github_repo101.md` and #107 report preserve their historical pending-regression wording in their original files.

This branch had already completed development-equivalence regression for the new repository's v11 adapter:

- Receipt: `data/r15/github_repo101_build/v11_regression_20261025T050709Z/REGRESSION_RECEIPT.json`.
- SHA256: `a23ca615e0ce945f2f64380347516333b1d0c816e59bc9e5b3330e4b902ebdb0`.
- Status: `LOCAL_EQUIVALENCE_PASS_PENDING_CLAUDE_RECOMPUTE`; Claude approval remained pending.
- One native run for each of MOT20-01/02, followed by one scoring run; scientific CPU wall time totaled 133.322 seconds, with zero GPU use.
- Scientific fields across 3,211 frames, final events at 12 gates, the M4 stitch object, complete event-matching objects and 161,840 identity observations agreed individually.
- Low 86/180, high 203/210 and identity precision 569/712; the receipt contains all four bins and aggregate values.

The comparison targets scientific fields. Whole JSON rows and compressed files retain byte differences: old detector timing/path metadata was omitted, top-level event identity attachments were recomputed, and the new identity audit contains additional output-association information. The receipt lists these differences explicitly.

Earlier input-scope incidents and preflight failures remain recorded. Continuing with clean 01/02 inputs relied on an autonomous correction within the user's authorized scope; Claude approval remained a separate step. See `prior_incident_retained`, `continuation_authority` and `preflight_failure_retained` in the receipt.

The next step recorded here was review of the existing receipt, read ledger and comparator. Acceptance should be recorded in a new version's status file. Any remaining concern should identify the specific comparison field or input binding and request the corresponding evidence; the existing experiment remains available for that review.
