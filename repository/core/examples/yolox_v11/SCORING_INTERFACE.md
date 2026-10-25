# What this example reproduces

The input is the already completed YOLOX-X + v11 development run. This sample recomputes the identity referee and final-event matching from actual emitted tracker boxes and the public GT supplied by the user. Its scope begins with saved outputs after model inference, detection, tracking, stitching, C1 confirmation and R1+R2 decoding.

`cache_manifest.json` explicitly lists both sequences, metadata, every sanitized frame/event file and its SHA256. `source_manifest.json` records the corresponding saved source files by project-relative name, byte count and SHA256, together with the field whitelist. These names identify provenance; reproduction reads the bundled files.

|Layer|Retained|Omitted and resulting limitation|
|---|---|---|
|Emitted boxes|Native zero-based xyxy, post-M4 track ID, original detection index, pre-M4 ID, zero/one-based frame indices and time|Unemitted raw detections, confidence, pose and region points; cannot rerun detection, M4 or explain why a raw detection was discarded|
|Final events|Direction, first target-entry frame/time, crossing point, final/fragment/group IDs and stable member event IDs with original member timing|Prior identity results, detector diagnostics and internal C1/R1/R2 evidence; cannot reproduce the event-decoding chain from this reduced sample|
|Official reference GT|Read from the two explicit caller-supplied gt.txt paths, with original file hash verification|Never copied into the release; no images or video are included|
|Rebuilt labels|All confirmed and unconfirmed transitions from the label builder; main scoring uses only rule-confirmed transitions|Human QC remains `not_reviewed`; numerical reconstruction does not certify label truth|
|Expected results|The existing whole-sequence aggregate, per-sequence summaries and 12 gate units, copied as numerical expectations only|No old per-frame or per-event identity answers; scoring must reconstruct those from GT and output boxes|

The main population has 724 confirmed GT events. The historical T3 core population of 671 is a separate subset outside the evaluation scope of this v0 sample. Identity precision uses every final system event as its denominator, including unknown, ambiguous, mixed and ignored identities.

The scorer preserves the frozen rules: ordinary native-coordinate box IoU at least 0.5, one-to-one maximum cardinality then maximum exact IoU sum, row margin at least 0.10, conservative identity voting in the event's ±25-frame window, and same-identity/same-direction event matching within 25 frames and one GT height. Stable numeric keys resolve remaining exact ties. Function source and AST hashes are in `src/frozen_score/provenance.json`.

The additional range table reports each visibility bin's minimum and maximum matched count across **all** globally maximum-cardinality/minimum-exact-time pairings. Matching is done before binning. These achievable ranges describe ambiguity among equivalent optima; statistical confidence is outside their scope. Separate sequence/gate graphs are independent, so aggregate bounds are sums of their attainable bounds.

The anonymous range uses all final events and the same time/direction/position gates, with identity excluded from eligibility. All final events remain eligible under those gates, including events removed by historical T3 clean/neutral filtering. These ranges are recomputed diagnostics; the exact saved-main parity check covers the numerical references retained in this sample.

Scope: existing development results. A successful software reproduction provides evidence for that execution; independent recomputation by a separate AI-assisted implementation and human label validation require separate records.
