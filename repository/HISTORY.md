# Research routes and stopping decisions

This history traces the shift from private-scene exploration to identity-qualified crossing evaluation on public data. It summarizes the inspected logs, retrospective documents, reports and recomputation receipts. Original conversation text and raw logs remain with their source records. Source IDs resolve through the [documentation ledger](metadata/docs_sources.json), which records original-project paths, full SHA256 values and read scopes; source availability varies by distribution. Later formal receipts take precedence over earlier pending-recomputation wording.

## Early question: can the system identify when people are missed?

The initial idea used temporal pixel transplants and round-trip checks to create inputs with known changes. Lighting, occlusion and valid insertion locations remained unresolved across times, and nearby-time transplant availability was insufficient. That route stopped before becoming part of the public resource. A later geometric blind-zone analysis distinguished occlusion at a footpoint from visibility of the whole person; incorporating body outlines reduced the inferred blind area. Both explorations refined definitions, with a validated new detector still outside their evidence. Sources: S01, S02.

The event implementation then fixed two-sided regions, depth confirmation, same-ID deduplication and direction rules. Speed-based splitting produced apparent gains by fragmenting one person; a strict comparison using the same source led to its rejection. An input-index mapping error between tracker high- and low-score pools was corrected, invalidating the earlier low-threshold anomaly. Memory resets at block boundaries were recorded separately from actual misses. Broader judgments about low-confidence strategies require evidence beyond those superseded anomalous values. Sources: S01, S02.

G1 tried to predict human-window recovery from observable signals. Its event-level combination achieved leave-one-channel-out Spearman −0.11, below the strongest single box-level signal at 0.27, and failed its criterion. The report records independent checks of matching, correlation and ridge-regression point estimates; resampling intervals have their separately documented verification scope. Time-shift chance correction was later found to penalize correct events in steady flows, ending its interpretation as a measure of actual errors. Stadium materials contribute aggregate development experience; windows, labels, source videos and sealed tests remain outside this distribution. Sources: S18, S01, S02.

## Public identity and visibility evaluation

MOT20 supplies reference identities, frame-level positions and visibility, allowing evaluation to ask whether a particular person's crossing was correctly reported. Virtual gates use real-video coordinates, and labels derive from reference trajectories. Human confirmation is a separate step from rule confirmation. The later whole-sequence development table contains 724 rule-confirmed events from 01/02; T3 uses the older 671-event core population, so comparisons require the corresponding population definition. Historical P1/P2 exposure to 03/05 remains disclosed with confirmation results. Sources: S01, S02, S20.

The selected development v11 combines established components: CrowdDet, low-confidence admission and local fragment stitching. O1 uses reference full-body boxes to inspect the event chain under stronger input information. These boxes include occluded extent and share sources with the derived labels, so pixel-level recoverability requires separate evidence. GateNet stopped before training; related prior work and a mismatch in identity objectives led the project to withdraw its proposed original-method positioning. Sources: S01, S02, S30.

## Stopping points of six research routes

|Route|Test and result|Retained conclusion and review scope|
|---|---|---|
|G1|Label-free signals predicting window recovery failed the preset criterion|These signals missed the prediction target. Matching, correlation and ridge point estimates have independent checks; uncertainty statistics retain their individual review scope. S18|
|T3|Conditional v11 residual gap: 01 has 1/59 and 02 has 11/517, both below 0.10; H2 has 0/3 and 1/26|Formal decision: `STOP_CURRENT_CLAIM`. Unknown identities remain unresolved, and these ratios describe conditional gaps. Independent receipt S12|
|HeadGate|Frozen oracle and seven-cell diagnostic on MOT20-01 using matched-source head/body development data; best low-bin result 21/32 against the required 26/32|Route stopped before training. Seven-cell diagnostic recomputation agrees; the conclusion covers this setup. S13|
|D1|The broadest direct-gap candidates are 10 for P2 and 16 for v11, below the entry requirement of 17; the 1.08-second variant remained unexecuted|Stopped at the operational entry gate. Later audits retain single-run status with independent recomputation pending; the counts describe these candidates. S19, S31|
|GateLink|The G50 perfect-reconnection/filling main test failed the requirement of low-bin net gain 27 in at least two systems with high-bin loss at most 2|This frozen intervention stopped. Review coverage is the logged O-link G50 three-system main decision; other ablations, windows and ReID configurations need their own evidence. S01, S20, S31|
|ReID #93|Fixed BoT-SORT appearance configuration: low 81/180 versus 84/180 without ReID, net −3; high 208/210|Formal decision: `BASELINE_ONLY`. Safety passed and the practical low-bin gain gate failed. This baseline remains outside 03/05 confirmation; the conclusion applies to this configuration. Independent receipt S23|

Each stopping decision applies to its specified inputs, rules and intervention, and supports ending investment in that configuration. Image information, other association methods and future approaches retain their own evidence requirements. Unresolved causes remain unknown.

## Output diagnostics and stronger fixed baselines

E1 classifies saved-output evidence into input, output, connection, decoding and unresolved categories. E2 compares dispersed and contiguous deletion of reference boxes. E3 reports count ranges over equally optimal matchings, and E4 examines conventional frame-level tracking metrics. The earlier E4 version and coordinate-origin correction remain traceable. Conventional metrics stratified by visibility also show low-bin degradation. Later E1/E2 receipts confirm agreement for 3,620 attribution rows and 250 count cells; these are algorithmic classifications whose human causal interpretation requires separate review. Sources: S14, S24, S25, S20.

The project then introduced the existing YOLOX-X detector with official ByteTrack MOT17 weights, keeping the MOT20 weights that include confirmation sequences outside the selected setup. Development YOLOX＋v11 met the frozen G2 criterion. The ByteTrack, OC-SORT and BoT-SORT comparison pipelines without ReID also completed independent score recomputation. Their shared detection cache coexists with differences in author admission, output filtering and GMC. The evidence covers these fixed established pipelines; a complete leaderboard SOTA reproduction and original tracker contribution remain separate claims. Sources: S15, S16, S01, S26.

After one-time 03/05 confirmation, independent recomputation agreed on all four bins and identity precision for 14 system×sequence units; H-A and H-B held on both sequences. Pooled low-bin recovery was 184/427（43.1%） for YOLOX＋v11 and 140/427（32.8%） for ByteTrack, an absolute difference of 10.3 percentage points. More than half remained unrecovered. With CrowdDet fixed, v11 versus P2 gave low-bin counts of 43 versus 43 and 36 versus 39, so the low-bin improvement gate remained unmet. Attribution to M4 requires separate intervention evidence. YOLOX is numerically nondeterministic, making confirmation conditional on the sealed cache; prior exposure and the small desktop GPU workload remain disclosed. Source: S22.

## From research scripts to a handoff resource

The resource first added label reconstruction from public GT, then standard-track scoring and event-level evidence inspection. Frozen core functions and outer path adapters organize these entry points; see [PIPELINE](PIPELINE.md) and [VERIFY](VERIFY.md) for interfaces and acceptance. CPU cache regression, inference from original images and independent reproduction on another machine each require their own receipt.

In the historical snapshot, Q2's first reviewer had finished and locked their answers, while the second review remained pending. Q3 independent review also remained incomplete, with human work limited to MOT20-01/02. The package supplies protocols and empty templates; reviewer answers remain outside the distribution. Final rights/attribution, independent reproduction and hosted-access acceptance remained open. Sources: S20, S21.

### Main sources

- S01 `codex_supervision/codex_instruction_log.md`（SHA256 `be8992c0bba4110b2575e1c1f14a366a6fd0a4f8c970d66ca19e37331eaaded5`）
- S02 `docs/r15_project_retrospective_20261023_full.md`（SHA256 `641fd2f632b7fd15ef9c4237a670506c131fe7837302b10b14eed12c74f53dc5`）
- S12 `codex_supervision/claude_checks/c1star_t3_recompute_verdict_20261023.md`（SHA256 `d6d42d095fce7ab9317b4ac5dfc880fcfbdb22ac4c7c4c8fd490e8c8de608497`）
- S13 `codex_supervision/claude_checks/headgate_diagnostic_v2_recompute_verdict_20261023.md`（SHA256 `48b0af115cdd918a86f3b097379a0fa34b15d89332e774f8038888414d54bee8`）
- S14 `codex_supervision/claude_checks/e4_v2_recompute_verdict_20261023.md`（SHA256 `3be2669e9d0b8e83831b4d4fac24a1ededc9fa17ee1deb0518c4a91b122ebdbb`）
- S15 `codex_supervision/claude_checks/offshelf_g1_recompute_verdict_20261023.md`（SHA256 `5c3430a58cf0527788d2d33049c8084e203108465a5e20113568e96aae8ffbd1`）
- S16 `codex_supervision/claude_checks/sota_panel_recompute_verdict_20261023.md`（SHA256 `8477951a5311b669c4a89819af19f5d39f98aa2d6f426bfb9fb11326d24ec777`）
- S18 `docs/g1_results_2026-10-21.md`（SHA256 `4fcf6a15a66b38305724b3de1e5edc17b099ad460e6ce50bbcc749dd4f56e927`）
- S19 `codex_reports/r15e29_gap_chain_describe_81a.md`（SHA256 `3079f33facdc98ec5009632e9b5e37dc25d2f410c7f35638f08ba283a8e9bb2d`）
- S20 `docs/paper_evidence_and_claims_v2.md`（SHA256 `49a4fdc7ca98de7f28fe841d4929b1e5576c1a3314c30dd870301e196a4602f9`）
- S22 `codex_supervision/claude_checks/confirm0305_recompute/VERDICT_20261025.md`（SHA256 `f740fe238225ca11c971dde186d5364881a67bbf18251ab7026f83f9d15bf496`）
- S23 `codex_supervision/claude_checks/reid93_recompute/VERDICT_20261024.md`（SHA256 `341124adfb06193921f8ac77a2544efeecd64db7d9f22ebecd2ac9a8eaa81ec4`）
- S24 `codex_supervision/claude_checks/e1_recompute/VERDICT_20261024.md`（SHA256 `8e1060af50e1202f2384f1078076203508cd7f2043040dcf633924e1c561dfa1`）
- S25 `codex_supervision/claude_checks/e2_recompute/VERDICT_20261024.md`（SHA256 `fac9053428849e1617bea72c4b703f8cd4af90fc5424d87f385e38046ff3ade3`）
- S26 `data/r15/offshelf_detector/download82e/DOWNLOAD_LEDGER.json`（SHA256 `bead41eb28af1141732b1115fc67cbcc08fbfa963829a31a0a748a35cd98e46d`）
- S30 `docs/resource_spec_v2.md`（SHA256 `1c99ef4a33f654c1babcba468c1661fe18fa4dec251cfe5578389b88b076e841`）
- S31 `docs/resource_spec_v2_status_addendum_90.md`（SHA256 `02444456951947aa4b884efed2797480ca453ddba18215f8b62af3e375e849c9`）

