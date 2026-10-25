# Results and recomputation status

These tables transcribe the original project's writing tables in `docs/paper_tables_v3/`, preserving each numerical string. The [documentation ledger](metadata/docs_sources.json) records each cell's source text, relative path, line and source SHA256 under `table_transcriptions`. Display precision follows the source table; measurement accuracy and statistical uncertainty require their corresponding evidence.

S identifiers refer to the same ledger. Each formal independent-recomputation finding covers its stated fields. Repository CPU checks, the full pixel workflow and cross-machine acceptance have separate records in [VERIFY](VERIFY.md). See [claims_and_limits](docs/claims_and_limits.md) for interpretation.

## Table 1: MOT20-01/02 development identity crossings

The four bins use mean reference visibility within 1 second before and after the event: low <0.25, mid-low [0.25,0.5), mid-high [0.5,0.75), high ≥0.75. Their denominators are 180, 171, 163 and 210, totaling 724. Matching requires the same identity and direction, |dt|≤1 second and distance≤the person's reference-box height. Precision uses all final system events as its denominator.

| System | Low | Mid-low | Mid-high | High | All | Identity precision | Evidence tag |
| --- | --- | --- | --- | --- | --- | --- | --- |
| P1 | 27/180 (15.0%) | 76/171 (44.4%) | 126/163 (77.3%) | 197/210 (93.8%) | 426/724 (58.8%) | 426/590 (72.2%) | V1_TRANSCRIPTION |
| P2 | 81/180 (45.0%) | 140/171 (81.9%) | 144/163 (88.3%) | 201/210 (95.7%) | 566/724 (78.2%) | 566/697 (81.2%) | V1_TRANSCRIPTION |
| v11 | 86/180 (47.8%) | 136/171 (79.5%) | 144/163 (88.3%) | 203/210 (96.7%) | 569/724 (78.6%) | 569/712 (79.9%) | V1_TRANSCRIPTION |
| YOLOX+ByteTrack | 83/180 (46.1%) | 142/171 (83.0%) | 149/163 (91.4%) | 206/210 (98.1%) | 580/724 (80.1%) | 580/644 (90.1%) | V1_TRANSCRIPTION |
| YOLOX+OC-SORT | 70/180 (38.9%) | 137/171 (80.1%) | 147/163 (90.2%) | 206/210 (98.1%) | 560/724 (77.3%) | 560/593 (94.4%) | V1_TRANSCRIPTION |
| YOLOX+BoT-SORT | 84/180 (46.7%) | 142/171 (83.0%) | 150/163 (92.0%) | 208/210 (99.0%) | 584/724 (80.7%) | 584/634 (92.1%) | V1_TRANSCRIPTION |
| YOLOX+BoT-SORT+ReID | 81/180 (45.0%) | 141/171 (82.5%) | 149/163 (91.4%) | 208/210 (99.0%) | 579/724 (80.0%) | 579/628 (92.2%) | BASELINE_ONLY |
| YOLOX+v11 | 99/180 (55.0%) | 149/171 (87.1%) | 150/163 (92.0%) | 205/210 (97.6%) | 603/724 (83.3%) | 603/665 (90.7%) | V1_TRANSCRIPTION |
| O1 (oracle) | 173/180 (96.1%) | 168/171 (98.2%) | 161/163 (98.8%) | 209/210 (99.5%) | 711/724 (98.2%) | 711/723 (98.3%) | V1_TRANSCRIPTION |

Numerical source: original-project `docs/paper_tables_v3/table1_event_recall.md`, SHA256 `6c668dbd9f80b8039ca526188dc45be211a8d533982c74ce894090b403bef953` (S04).
Earlier rows inherit the recomputation level recorded in table v1; `V1_TRANSCRIPTION` marks the present transcription. Historical score recomputation for YOLOX＋v11 and the three panels appears in S15/S16, respectively. S23 directly covers the ReID row with decision `BASELINE_ONLY`. O1 is a reference under full-body-box information; a pixel-recoverability bound requires separate evidence.

## Table 2: conventional frame-level tracking metrics

HOTA, IDF1 and MOTA retain three decimal places; low-visibility frame-level IDR retains its numerator and denominator. This table uses frame-level visibility, with a different population from the event denominators in Table 1.

| System | Sequence | HOTA | IDF1 | MOTA | Low-visibility frame IDR |
| --- | --- | --- | --- | --- | --- |
| v11 | MOT20-01 | 0.584 | 0.724 | 0.735 | 3205/6925 (0.463) |
| v11 | MOT20-02 | 0.502 | 0.599 | 0.716 | 18705/61635 (0.303) |
| YOLOX+ByteTrack | MOT20-01 | 0.620 | 0.761 | 0.764 | 3278/6925 (0.473) |
| YOLOX+ByteTrack | MOT20-02 | 0.545 | 0.644 | 0.752 | 20689/61635 (0.336) |
| YOLOX+OC-SORT | MOT20-01 | 0.582 | 0.721 | 0.713 | 2618/6925 (0.378) |
| YOLOX+OC-SORT | MOT20-02 | 0.537 | 0.656 | 0.692 | 18394/61635 (0.298) |
| YOLOX+BoT-SORT | MOT20-01 | 0.618 | 0.764 | 0.766 | 3226/6925 (0.466) |
| YOLOX+BoT-SORT | MOT20-02 | 0.560 | 0.664 | 0.755 | 22504/61635 (0.365) |
| YOLOX+v11 | MOT20-01 | 0.638 | 0.786 | 0.787 | 3723/6925 (0.538) |
| YOLOX+v11 | MOT20-02 | 0.565 | 0.671 | 0.783 | 25056/61635 (0.407) |

Numerical source: original-project `docs/paper_tables_v3/table2_standard_metrics.md`, SHA256 `8e047d7386e9b96d71548023ded56e2cda0c4fc5b72597be8d91fe00594ac66f` (S05).
S14 covers the original eight coordinate-corrected P1/P2/v11/O1 units and 272 fields. Expanded YOLOX rows inherit S01's extended checks and S20's status summary; S14 retains its original coverage within this ten-row table. This pass transcribed the existing TrackEval results. Conventional metrics stratified by visibility also reveal degradation.

## Table 3: aggregate stadium development rule pairing

This table contains system-level stratified summaries. Window records remain outside the distribution. Pairing uses time and position rules, with identity truth unavailable; interpret this scale separately from MOT20 IVR. Each cell retains matched/reference counts, system-event count and source precision. Events within the allowed range outside a window can match while staying outside its event count, so precision follows the original calculation.

| System | Clearly visible | Partly obscured | Mostly obscured | All |
| --- | --- | --- | --- | --- |
| P1 | 108/129（events 111，precision 0.92） | 153/201（events 164，precision 0.91） | 9/138（events 17，precision 0.53） | 270/468（events 292，precision 0.89） |
| v10 (CrowdDet) | 104/129（events 114，precision 0.88） | 166/201（events 193，precision 0.84） | 88/138（events 232，precision 0.38） | 358/468（events 539，precision 0.65） |
| v11 (CrowdDet+M3+M4) | 104/129（events 114，precision 0.88） | 171/201（events 196，precision 0.86） | 101/138（events 296，precision 0.34） | 376/468（events 606，precision 0.61） |
| YOLOX+v11 | 103/129（events 107，precision 0.93） | 165/201（events 180，precision 0.90） | 40/138（events 87，precision 0.45） | 308/468（events 374，precision 0.80） |

Numerical source: original-project `docs/paper_tables_v3/table3_stadium.md`, SHA256 `a2e7bba8d5aa2e018b8642223f0132a0b438c1d1e83277a8512d98312c4ef841` (S06).
S17 specifically recomputes YOLOX＋v11 and CrowdDet v11. P1 and v10 retain their historical-row evidence. Original stadium videos, windows, annotations and sealed tests remain outside the distribution.

## E1: automatic attribution of development outputs

| System | Bin | N | ⑤ Recovered | ① No compatible input | ② Unemitted | ③ Missing track connection | ④ Decoding/localization | U |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| P2 | ALL | 724 | 566 | 4 | 1 | 30 | 31 | 92 |
| P2 | low | 180 | 81 | 4 | 1 | 22 | 13 | 59 |
| v11 | ALL | 724 | 569 | 4 | 3 | 28 | 30 | 90 |
| v11 | low | 180 | 86 | 4 | 3 | 23 | 12 | 52 |
| O1 | ALL | 724 | 711 | 0 | 0 | 0 | 7 | 6 |
| O1 | low | 180 | 173 | 0 | 0 | 0 | 2 | 5 |

Numerical source: original-project `docs/paper_tables_v3/table_e1_attribution.md`, SHA256 `75980717a5e6e8655dd1dc27be63c34ab4f2bd1267948103d548aadfcc7a5975` (S08).
S24 independently recomputes P1/P2/v11/O1/O2 × 724, totaling 3,620 rows, with agreement in main classes, subclasses and U subreasons. The table shows overall/low-bin summaries for three of these systems. Classification is algorithmic; human review and causal-effect estimation require separate evidence. Class ① means no compatible input under the fixed thresholds and geometry; image visibility requires separate visual evidence. Identity-reading-sensitive U_IDENTITY rows number P1 5, P2 9 and v11 15, totaling 29 across those named systems. S24 records further ignore-object/IoA sensitivities; P2/v11 counts in ①–⑤ remain unchanged.

## E2: existing controlled-deletion curves

The following ALL/low means, minima and maxima summarize fixed seeds and preserve the original decimal strings. mean/min/max describe seed variation. The present pass transcribes existing curves and aggregate values; confidence intervals require a separate statistical construction.

| sequence | retention_requested | mode | visibility_bin | seed_count | gt_events_each_seed | IVR_mean | IVR_min | IVR_max | identity_matches_mean |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| MOT20-01 | 0.25 | block | ALL | 3 | 74 | 0.06756756756756757 | 0.04054054054054054 | 0.0945945945945946 | 5 |
| MOT20-01 | 0.25 | block | low | 3 | 32 | 0.052083333333333336 | 0.03125 | 0.09375 | 1.6666666666666667 |
| MOT20-01 | 0.25 | iid | ALL | 3 | 74 | 0.47297297297297297 | 0.36486486486486486 | 0.6081081081081081 | 35 |
| MOT20-01 | 0.25 | iid | low | 3 | 32 | 0.4270833333333333 | 0.3125 | 0.5625 | 13.666666666666666 |
| MOT20-01 | 0.5 | block | ALL | 3 | 74 | 0.22522522522522523 | 0.16216216216216217 | 0.25675675675675674 | 16.666666666666668 |
| MOT20-01 | 0.5 | block | low | 3 | 32 | 0.14583333333333334 | 0.09375 | 0.1875 | 4.666666666666667 |
| MOT20-01 | 0.5 | iid | ALL | 3 | 74 | 0.8963963963963965 | 0.8783783783783784 | 0.9324324324324325 | 66.33333333333333 |
| MOT20-01 | 0.5 | iid | low | 3 | 32 | 0.8854166666666666 | 0.875 | 0.90625 | 28.333333333333332 |
| MOT20-01 | 0.75 | block | ALL | 3 | 74 | 0.6306306306306306 | 0.5945945945945946 | 0.6756756756756757 | 46.666666666666664 |
| MOT20-01 | 0.75 | block | low | 3 | 32 | 0.6145833333333334 | 0.59375 | 0.625 | 19.666666666666668 |
| MOT20-01 | 0.75 | iid | ALL | 3 | 74 | 0.972972972972973 | 0.972972972972973 | 0.972972972972973 | 72 |
| MOT20-01 | 0.75 | iid | low | 3 | 32 | 0.96875 | 0.96875 | 0.96875 | 31 |
| MOT20-01 | 0.9 | block | ALL | 3 | 74 | 0.918918918918919 | 0.9054054054054054 | 0.9324324324324325 | 68 |
| MOT20-01 | 0.9 | block | low | 3 | 32 | 0.90625 | 0.875 | 0.9375 | 29 |
| MOT20-01 | 0.9 | iid | ALL | 3 | 74 | 0.981981981981982 | 0.972972972972973 | 0.9864864864864865 | 72.66666666666667 |
| MOT20-01 | 0.9 | iid | low | 3 | 32 | 0.9895833333333334 | 0.96875 | 1.0 | 31.666666666666668 |
| MOT20-01 | 1 | baseline | ALL | 1 | 74 | 0.972972972972973 | 0.972972972972973 | 0.972972972972973 | 72 |
| MOT20-01 | 1 | baseline | low | 1 | 32 | 0.96875 | 0.96875 | 0.96875 | 31 |
| MOT20-02 | 0.25 | block | ALL | 3 | 650 | 0.07641025641025641 | 0.07076923076923076 | 0.08461538461538462 | 49.666666666666664 |
| MOT20-02 | 0.25 | block | low | 3 | 148 | 0.033783783783783786 | 0.02027027027027027 | 0.05405405405405406 | 5 |
| MOT20-02 | 0.25 | iid | ALL | 3 | 650 | 0.5261538461538462 | 0.5015384615384615 | 0.5507692307692308 | 342 |
| MOT20-02 | 0.25 | iid | low | 3 | 148 | 0.30405405405405406 | 0.24324324324324326 | 0.35135135135135137 | 45 |
| MOT20-02 | 0.5 | block | ALL | 3 | 650 | 0.2241025641025641 | 0.21076923076923076 | 0.2353846153846154 | 145.66666666666666 |
| MOT20-02 | 0.5 | block | low | 3 | 148 | 0.0900900900900901 | 0.08108108108108109 | 0.0945945945945946 | 13.333333333333334 |
| MOT20-02 | 0.5 | iid | ALL | 3 | 650 | 0.8964102564102564 | 0.86 | 0.916923076923077 | 582.6666666666666 |
| MOT20-02 | 0.5 | iid | low | 3 | 148 | 0.7702702702702703 | 0.7432432432432432 | 0.7837837837837838 | 114 |
| MOT20-02 | 0.75 | block | ALL | 3 | 650 | 0.5994871794871794 | 0.5892307692307692 | 0.6107692307692307 | 389.6666666666667 |
| MOT20-02 | 0.75 | block | low | 3 | 148 | 0.5045045045045045 | 0.47297297297297297 | 0.5337837837837838 | 74.66666666666667 |
| MOT20-02 | 0.75 | iid | ALL | 3 | 650 | 0.9682051282051282 | 0.96 | 0.9769230769230769 | 629.3333333333334 |
| MOT20-02 | 0.75 | iid | low | 3 | 148 | 0.9099099099099099 | 0.8918918918918919 | 0.9391891891891891 | 134.66666666666666 |
| MOT20-02 | 0.9 | block | ALL | 3 | 650 | 0.8943589743589744 | 0.8923076923076924 | 0.8953846153846153 | 581.3333333333334 |
| MOT20-02 | 0.9 | block | low | 3 | 148 | 0.8288288288288288 | 0.8040540540540541 | 0.8513513513513513 | 122.66666666666667 |
| MOT20-02 | 0.9 | iid | ALL | 3 | 650 | 0.98 | 0.9784615384615385 | 0.9815384615384616 | 637 |
| MOT20-02 | 0.9 | iid | low | 3 | 148 | 0.9481981981981982 | 0.9391891891891891 | 0.9594594594594594 | 140.33333333333334 |
| MOT20-02 | 1 | baseline | ALL | 1 | 650 | 0.9830769230769231 | 0.9830769230769231 | 0.9830769230769231 | 639 |
| MOT20-02 | 1 | baseline | low | 1 | 148 | 0.9594594594594594 | 0.9594594594594594 | 0.9594594594594594 | 142 |

Actual retention rates and other original fields for the same keys:

| sequence | retention_requested | mode | visibility_bin | actual_primary_retention_mean | actual_primary_retention_min | actual_primary_retention_max |
| --- | --- | --- | --- | --- | --- | --- |
| MOT20-01 | 0.25 | block | ALL | 0.26879718168092603 | 0.26879718168092603 | 0.26879718168092603 |
| MOT20-01 | 0.25 | block | low | 0.26137184115523465 | 0.26137184115523465 | 0.26137184115523465 |
| MOT20-01 | 0.25 | iid | ALL | 0.26879718168092603 | 0.26879718168092603 | 0.26879718168092603 |
| MOT20-01 | 0.25 | iid | low | 0.26137184115523465 | 0.26137184115523465 | 0.26137184115523465 |
| MOT20-01 | 0.5 | block | ALL | 0.5128837443381983 | 0.5128837443381983 | 0.5128837443381983 |
| MOT20-01 | 0.5 | block | low | 0.508158844765343 | 0.508158844765343 | 0.508158844765343 |
| MOT20-01 | 0.5 | iid | ALL | 0.5128837443381983 | 0.5128837443381983 | 0.5128837443381983 |
| MOT20-01 | 0.5 | iid | low | 0.508158844765343 | 0.508158844765343 | 0.508158844765343 |
| MOT20-01 | 0.75 | block | ALL | 0.7679416205334675 | 0.7679416205334675 | 0.7679416205334675 |
| MOT20-01 | 0.75 | block | low | 0.7604332129963899 | 0.7604332129963899 | 0.7604332129963899 |
| MOT20-01 | 0.75 | iid | ALL | 0.7679416205334675 | 0.7679416205334675 | 0.7679416205334675 |
| MOT20-01 | 0.75 | iid | low | 0.7604332129963899 | 0.7604332129963899 | 0.7604332129963899 |
| MOT20-01 | 0.9 | block | ALL | 0.9198288877705083 | 0.9198288877705083 | 0.9198288877705083 |
| MOT20-01 | 0.9 | block | low | 0.912057761732852 | 0.912057761732852 | 0.912057761732852 |
| MOT20-01 | 0.9 | iid | ALL | 0.9198288877705083 | 0.9198288877705083 | 0.9198288877705083 |
| MOT20-01 | 0.9 | iid | low | 0.912057761732852 | 0.912057761732852 | 0.912057761732852 |
| MOT20-01 | 1 | baseline | ALL | 1.0 | 1.0 | 1.0 |
| MOT20-01 | 1 | baseline | low | 1.0 | 1.0 | 1.0 |
| MOT20-02 | 0.25 | block | ALL | 0.2646598854868103 | 0.2646598854868103 | 0.2646598854868103 |
| MOT20-02 | 0.25 | block | low | 0.2587166382737081 | 0.2587166382737081 | 0.2587166382737081 |
| MOT20-02 | 0.25 | iid | ALL | 0.2646598854868103 | 0.2646598854868103 | 0.2646598854868103 |
| MOT20-02 | 0.25 | iid | low | 0.2587166382737081 | 0.2587166382737081 | 0.2587166382737081 |
| MOT20-02 | 0.5 | block | ALL | 0.5096935544325393 | 0.5096935544325393 | 0.5096935544325393 |
| MOT20-02 | 0.5 | block | low | 0.5057353776263487 | 0.5057353776263487 | 0.5057353776263487 |
| MOT20-02 | 0.5 | iid | ALL | 0.5096935544325393 | 0.5096935544325393 | 0.5096935544325393 |
| MOT20-02 | 0.5 | iid | low | 0.5057353776263487 | 0.5057353776263487 | 0.5057353776263487 |
| MOT20-02 | 0.75 | block | ALL | 0.7631670781041993 | 0.7631670781041993 | 0.7631670781041993 |
| MOT20-02 | 0.75 | block | low | 0.7575728076579865 | 0.7575728076579865 | 0.7575728076579865 |
| MOT20-02 | 0.75 | iid | ALL | 0.7631670781041993 | 0.7631670781041993 | 0.7631670781041993 |
| MOT20-02 | 0.75 | iid | low | 0.7575728076579865 | 0.7575728076579865 | 0.7575728076579865 |
| MOT20-02 | 0.9 | block | ALL | 0.9152330976722545 | 0.9152330976722545 | 0.9152330976722545 |
| MOT20-02 | 0.9 | block | low | 0.9087531435061248 | 0.9087531435061248 | 0.9087531435061248 |
| MOT20-02 | 0.9 | iid | ALL | 0.9152330976722545 | 0.9152330976722545 | 0.9152330976722545 |
| MOT20-02 | 0.9 | iid | low | 0.9087531435061248 | 0.9087531435061248 | 0.9087531435061248 |
| MOT20-02 | 1 | baseline | ALL | 1.0 | 1.0 | 1.0 |
| MOT20-02 | 1 | baseline | low | 1.0 | 1.0 | 1.0 |

Numerical source: original-project `docs/paper_tables_v3/table_e2_existing_curves.md`, SHA256 `36933afa243c22a7d1a2e2f0cf12d49c7ad4ee85a9684096ff589f69a47b3ba0` (S09).
Interpretation source: original-project `docs/paper_tables_v3/table_e2_notes.md`, SHA256 `b90aed612e2ffcfea12a26945c1f4cde67e5ca1195ab7ef3547ba6c49cabc5d2` (S10).
S25 checks 48/48 deletion manifests, bitwise mask reconstruction, the r=1 O1 regression, and 250 count cells from 50 runs. All differences and optimal-matching range widths are zero. Actual-retention fields inherit the original aggregate document's evidence, with the new receipt covering its explicitly listed checks.

The predictive formula was unspecified before execution. Deleting 13 consecutive frames creates a 0.56-second separation between retained endpoints, exceeding the frozen decoder's 0.5-second gap threshold. Inputs are reference GT boxes. Deletion grouping uses frame-level visibility, whereas IVR uses event-window mean visibility; these define different observation populations.

## Table 4: MOT20-03/05 one-time confirmation

S22 directly covers the four bins and identity precision for 14 system×sequence units, with every cell matching the original report and zero-width optimal-matching ranges. Pooled rows provide descriptions; confirmation decisions use each sequence's results.

| Sequence | System | Low | Mid-low | Mid-high | High | Identity precision |
| --- | --- | --- | --- | --- | --- | --- |
| MOT20-03 | YOLOX+v11 | 67/136 (49.26%) | 271/339 (79.94%) | 367/391 (93.86%) | 554/572 (96.85%) | 1259/1336 (94.24%) |
| MOT20-03 | YOLOX+ByteTrack | 56/136 (41.18%) | 244/339 (71.98%) | 353/391 (90.28%) | 548/572 (95.80%) | 1201/1279 (93.90%) |
| MOT20-03 | YOLOX+OC-SORT | 37/136 (27.21%) | 199/339 (58.70%) | 327/391 (83.63%) | 532/572 (93.01%) | 1095/1130 (96.90%) |
| MOT20-03 | YOLOX+BoT-SORT | 57/136 (41.91%) | 246/339 (72.57%) | 356/391 (91.05%) | 547/572 (95.63%) | 1206/1270 (94.96%) |
| MOT20-03 | P2 (CrowdDet) | 43/136 (31.62%) | 169/339 (49.85%) | 301/391 (76.98%) | 474/572 (82.87%) | 987/1141 (86.50%) |
| MOT20-03 | v11 (CrowdDet, M3+M4) | 43/136 (31.62%) | 165/339 (48.67%) | 302/391 (77.24%) | 480/572 (83.92%) | 990/1169 (84.69%) |
| MOT20-03 | O1 (GT-body input) | 132/136 (97.06%) | 336/339 (99.12%) | 389/391 (99.49%) | 569/572 (99.48%) | 1426/1440 (99.03%) |
| MOT20-05 | YOLOX+v11 | 117/291 (40.21%) | 667/804 (82.96%) | 712/770 (92.47%) | 622/645 (96.43%) | 2118/2275 (93.10%) |
| MOT20-05 | YOLOX+ByteTrack | 84/291 (28.87%) | 574/804 (71.39%) | 667/770 (86.62%) | 610/645 (94.57%) | 1935/2114 (91.53%) |
| MOT20-05 | YOLOX+OC-SORT | 42/291 (14.43%) | 437/804 (54.35%) | 594/770 (77.14%) | 596/645 (92.40%) | 1669/1729 (96.53%) |
| MOT20-05 | YOLOX+BoT-SORT | 79/291 (27.15%) | 581/804 (72.26%) | 678/770 (88.05%) | 611/645 (94.73%) | 1949/2086 (93.43%) |
| MOT20-05 | P2 (CrowdDet) | 39/291 (13.40%) | 339/804 (42.16%) | 522/770 (67.79%) | 528/645 (81.86%) | 1428/1962 (72.78%) |
| MOT20-05 | v11 (CrowdDet, M3+M4) | 36/291 (12.37%) | 335/804 (41.67%) | 520/770 (67.53%) | 521/645 (80.78%) | 1412/2051 (68.84%) |
| MOT20-05 | O1 (GT-body input) | 280/291 (96.22%) | 801/804 (99.63%) | 760/770 (98.70%) | 642/645 (99.53%) | 2483/2508 (99.00%) |
| 03+05（descriptive only） | YOLOX+v11 | 184/427 (43.09%) | 938/1143 (82.06%) | 1079/1161 (92.94%) | 1176/1217 (96.63%) | 3377/3611 (93.52%) |
| 03+05（descriptive only） | YOLOX+ByteTrack | 140/427 (32.79%) | 818/1143 (71.57%) | 1020/1161 (87.86%) | 1158/1217 (95.15%) | 3136/3393 (92.43%) |
| 03+05（descriptive only） | YOLOX+OC-SORT | 79/427 (18.50%) | 636/1143 (55.64%) | 921/1161 (79.33%) | 1128/1217 (92.69%) | 2764/2859 (96.68%) |
| 03+05（descriptive only） | YOLOX+BoT-SORT | 136/427 (31.85%) | 827/1143 (72.35%) | 1034/1161 (89.06%) | 1158/1217 (95.15%) | 3155/3356 (94.01%) |
| 03+05（descriptive only） | P2 (CrowdDet) | 82/427 (19.20%) | 508/1143 (44.44%) | 823/1161 (70.89%) | 1002/1217 (82.33%) | 2415/3103 (77.83%) |
| 03+05（descriptive only） | v11 (CrowdDet, M3+M4) | 79/427 (18.50%) | 500/1143 (43.74%) | 822/1161 (70.80%) | 1001/1217 (82.25%) | 2402/3220 (74.60%) |
| 03+05（descriptive only） | O1 (GT-body input) | 412/427 (96.49%) | 1137/1143 (99.48%) | 1149/1161 (98.97%) | 1211/1217 (99.51%) | 3909/3948 (99.01%) |

### Frozen criteria

H-A: on each sequence, all three panels satisfy `10×low≤7×N_low` and `10×high≥9×N_high`. H-B: YOLOX＋v11's low-bin correct count strictly exceeds the maximum among that sequence's three panels.

| Sequence | Criterion | Integer conditions and outcomes (original) | Outcome |
| --- | --- | --- | --- |
| MOT20-03 | H-A | byte: 10×56≤7×136: True; 10×548≥9×572: True | True |
| MOT20-03 | H-A | oc: 10×37≤7×136: True; 10×532≥9×572: True | True |
| MOT20-03 | H-A | bot: 10×57≤7×136: True; 10×547≥9×572: True | True |
| MOT20-03 | H-B | 67>57: True | True |
| MOT20-05 | H-A | byte: 10×84≤7×291: True; 10×610≥9×645: True | True |
| MOT20-05 | H-A | oc: 10×42≤7×291: True; 10×596≥9×645: True | True |
| MOT20-05 | H-A | bot: 10×79≤7×291: True; 10×611≥9×645: True | True |
| MOT20-05 | H-B | 117>84: True | True |

Numerical values and criteria: original-project `docs/paper_tables_v3/table4_confirmation.md`, SHA256 `1772b79588a71d4d7783b9da2caeab7d93713575d0b77b342d1aa2a250eb8ffb` (S07).
Independent receipt: original-project `codex_supervision/claude_checks/confirm0305_recompute/VERDICT_20261025.md`, SHA256 `f740fe238225ca11c971dde186d5364881a67bbf18251ab7026f83f9d15bf496` (S22).
H-A/H-B hold on both sequences. Pooled low-bin recovery is 184/427（43.1%） for YOLOX＋v11 and 140/427（32.8%） for ByteTrack, an absolute difference of 10.3 percentage points. More than half of low-bin events remain unrecovered. The pooled comparison is descriptive; statistical significance requires a separate analysis.

With CrowdDet fixed, v11 versus P2 has low-bin counts of 43 versus 43 on 03 and 36 versus 39 on 05. These comparisons show equal recovery on the former and lower recovery on the latter. YOLOX＋v11 is a confirmed strong baseline of established components; attribution of its advantage to M4 needs separate intervention evidence. Confirmation is conditional on the sealed cache because YOLOX is numerically nondeterministic. P1/P2 had prior 03/05 exposure, a small desktop GPU workload was present during the historical run, and human work covered 01/02 with two-person review still pending. Retain these disclosures with the findings.

