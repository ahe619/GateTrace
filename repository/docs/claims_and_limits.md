# Claims, verification scope and open work

The evidence supports **a resource and empirical diagnostics under stated conditions**. On MOT20-01/02 development data and frozen one-time 03/05 confirmation, the tested established pipelines consistently recover a limited share of low-visibility identity-qualified crossings. The public development resource lets others rebuild labels, score standard tracks and trace event-level evidence. YOLOX＋v11 is a strong baseline with preregistered confirmation. The contribution is a reproducible resource and a comparison of fixed established pipelines under the recorded settings.

S identifiers resolve through the [source ledger](../metadata/docs_sources.json), which records original-project paths, full SHA256 values and read scopes. Original conversations, complete reports and underlying data have separate distribution scopes. See [RESULTS](../RESULTS.md) for values and [HISTORY](../HISTORY.md) for stopping decisions. Main sources: S20–S25.

## Metrics and information conditions

IVR uses rule-confirmed reference events as its denominator. Correct matches require the same person and direction, a time difference of at most 1 second and distance at most the corresponding reference-box height. Identity precision includes every final event, retaining unknown, mixed and ignored identities. Event visibility averages the reference observations within 1 second before and after the first target-region entry; frame-level metrics use individual-frame visibility and a separate denominator. The development population contains 724 rule-confirmed events among 901 transitions across 12 gates. The same person may appear at multiple gates, so the 724 events include dependencies within people and videos. Sources: S20, S21.

Rule confirmation and human confirmation are separate evidence stages. O1 reference full-body boxes include occluded extent and share sources with label derivation; they define a diagnostic information condition. Standard-track scoring uses track-box bottom-centres, while historical v11 uses original detection footpoints and its dedicated interface. Missing identity-valid output leaves image visibility unresolved, and output-level unknowns retain their status. Sources: S20, S21, S30.

## Supported findings and interpretation scope

|Evidence|Supported statement|Interpretation|
|---|---|---|
|03/05 one-time confirmation|Independent recomputation agrees on four bins and precision for 14 system×sequence units; H-A/H-B hold separately on both sequences|Descriptive confirmation of these fixed systems on the sealed cache, with prior baseline exposure disclosed. S22|
|Pooled low-bin comparison|YOLOX＋v11 184/427（43.1%） versus ByteTrack 140/427（32.8%）, an absolute 10.3-point difference; more than half remain unrecovered|Pooled counts are descriptive. Decisions remain per sequence; report absolute percentage-point differences and established-component scope. S22|
|CrowdDet v11 versus P2|Low counts are 43 versus 43 on 03 and 36 versus 39 on 05, with the low-bin improvement gate unmet|The two comparisons show equal and lower recovery, respectively. The YOLOX＋v11 comparison measures the full pipeline, leaving M4 attribution unresolved. S22|
|E1 output attribution|3,620 main/subclass rows agree; v11 low-bin counts are 86 recovered, 4 with no compatible input, 3 unemitted, 23 missing connection, 12 decoding/localization and 52 unresolved|The 52 unknowns remain unresolved. Classes describe algorithmic evidence under fixed input thresholds and geometry; human confirmation and causal effects remain unestablished. S24|
|E2 controlled deletion|48/48 mask contracts and bitwise reconstruction pass; 50 runs and 250 count cells agree; temporal-loss responses are descriptive|Inputs are reference boxes. A 13-frame block creates a 0.56-second endpoint gap beyond the fixed 0.5-second decoder reset. The response applies to this GT-input intervention and its fixed decoder. S25|
|ReID #93|The fixed configuration has 3 fewer low-bin recoveries than the baseline without ReID and receives `BASELINE_ONLY`|The finding covers this fixed appearance configuration; broader appearance-association behavior and image observability remain unresolved. S23|
|E3 optimal-matching ranges|Equivalent-optimum count ranges provide a scoring safeguard; recorded zero-width identity ranges are retained|These are assignment-ambiguity bounds using established optimization. Sampling uncertainty is a different quantity, and the stopped T3 claim retains its decision. S20, S31|
|E4 conventional metrics|Visibility stratification also reveals degradation; coordinate-corrected results have specified recomputation coverage|Event metrics and conventional metrics both expose occlusion difficulty. Label the expanded YOLOX table and original eight-unit receipt separately. S05, S14, S20|
|Stadium summary|Aggregate development illustration using time-and-position rule pairing|Identity truth is unavailable; this scale and its window-data distribution scope are separate from MOT20 IVR. S06, S17|

The independent E1 implementation uses the same identity interpretation. Sensitive U_IDENTITY rows number P1 5, P2 9 and v11 15, totaling 29; ignore-object and IoA interpretations also affect a small number of P1 rows. The receipt records unchanged P2/v11 counts in ①–⑤, while definition sensitivity remains. E2 fixed-seed mean/min/max describe variation across deletion seeds. Actual frame-retention rates and event-mean-visibility evaluation use different observation populations; confidence intervals require separate statistical construction. Sources: S24, S25, S09, S10.

## Verification layers

|Verification|Established scope|Separate acceptance requirements|
|---|---|---|
|Historical independent score recomputation|Another implementation reproduces identity, matching and aggregation values for each receipt's stated inputs and fields|Pixel-inference bitwise agreement, human label accuracy and comprehensive code-branch correctness|
|Repository CPU checks|Passed checks are listed in [VERIFY](../VERIFY.md); synthetic tests and cache regression on lawfully acquired public inputs check interfaces and frozen results|Complete GPU pixel execution and full historical-experiment reproduction|
|Independent-machine acceptance|Pending in this snapshot|A separate machine must execute and document the reconstruction workflow|

The native v11 scoring path consumes saved `final_events` and actual post-M4 `tracker_rows`, reusing frozen label, E1-v2 identity-pool, matching and aggregation functions. Standard-track bottom-centre decoding retains its separate interface. The entry point passed 10 synthetic checks and initially carried `NOT_REAL_DATA_REGRESSED`. A later development-equivalence receipt recorded `LOCAL_EQUIVALENCE_PASS_PENDING_CLAUDE_RECOMPUTE`; see the [status addendum](NATIVE101A_STATUS_ADDENDUM.md). Inspector integration carried forward that receipt; Claude acceptance and cross-machine reproduction remained separate gates. Historical tables and recomputation conclusions retain their existing evidence. Sources: S32–S34; historical status appears in [native_v11_scoring_status.json](../metadata/native_v11_scoring_status.json).

HeadGate covers only the matched-source 01 development setup. D1 retains a single-run record with independent recomputation pending. GateLink inherits the O-link G50 three-system main-decision receipt; other ablations need their own checks. T3 remains `STOP_CURRENT_CLAIM` under its frozen thresholds and population; later confirmation has its own claims and criteria. Sources: S12, S13, S19, S20, S31.

## Execution disclosures accompanying confirmation

YOLOX's FP16 and lower-level implementation are numerically nondeterministic, so confirmation is conditional on the sealed detection cache. P1/P2 baseline event results on 03/05 had been seen previously. A small desktop GPU workload was present during the historical run; startup checks describe their observation time, while hardware exclusivity throughout execution would require continuous evidence. Sources: S22, S07.

Shared detection caches coexist with differences in author input admission, output filtering, GMC and post-processing. The frozen confirmation membership excludes ReID #93. Additional confirmation runs, cache selection or altered criteria require their own explicit design and authorization. Sources: S16, S20, S23.

## Work pending in the historical snapshot

- Q2's first reviewer was locked and the second remained pending, with status `PENDING_SECOND_HUMAN / NO_GROUP_UNBLINDING`. Answers, answer distributions and private group mappings remained outside the repository.
- Q3 material preparation had its own completion status; independent two-person review remained a separate gate. Human materials and work covered MOT20-01/02, with 03/05 outside that scope.
- Reconstruction from public inputs on another machine, final rights/attribution, hosting and logged-out access acceptance remained incomplete.
- Technical capability supports reproducibility. Third-party value, scientific necessity and priority claims require further evidence. Identity-event evaluation, visibility analysis, oracles and auditing each build on existing foundations.

These status records come from S20, S21 and S31. Later S22/S24/S25 receipts update S31's earlier pending E1/E2 and confirmation records. Human review, independent-machine acceptance and rights review retain their own status histories.
