# v0.2.1 engineering candidate

|Item|Practical change|Does not establish|
|---|---|---|
|I1|Reject redirected frame and directory paths before rendering|Correct pixels, visible anatomy, or correct GT identity|
|I2|Seal fresh output content; require complete identity-audit frames and exact correspondence to tracker rows|A correct scoring algorithm or a causal explanation of misses|
|I3|Keep actual/expected hashes on failed reads and preserve the original exception|A complete OS-level I/O trace; preflight failures can precede output creation|
|Reuse|`inspect_saved_event.py` checks and views a sealed run without invoking scoring|Permission to repeat experiments or to retrospectively bless unsealed results|
|Portable checks|`check_inspector.py --out NEW_DIR` produces a synthetic test receipt|A real-data regression, clean-machine reproduction, or Claude approval|

At preparation of this engineering candidate, the original source package
remained unchanged. Scientific modules, data, reference tables, protocols, and
licenses were copied byte-for-byte. Changes covered the inspector/CLI integrity
layer, documentation, and synthetic tests.

The scoring seal includes six files: `complete.json`, `read_ledger.json`, and
the two sequences' event-matching and frame-identity audits. This Inspector
consumes and authenticates those files. The separate original release/scoring
manifests retain their own roles.

Direct Python users must call `verify_package` first, retain the seal digest from
the trusted producer, and pass `read_ledger=[]` and `evidence_manifest_sha256` to
`Inspector`. An unsealed stored folder fails closed. The public CLI does these
checks and requires a new output directory. The helper preserves missing observations, observed positions, recorded
identities, and fixed thresholds.

At preparation of this candidate, mainline review was required for adoption.
A separately authorized real-data regression could establish output parity for
the new wrappers. Synthetic checks and unchanged scientific source hashes
provide engineering evidence; output parity requires the real-data regression.
The immutable v0.1 release and the execution status of held-out confirmation
remain fixed during adoption.
