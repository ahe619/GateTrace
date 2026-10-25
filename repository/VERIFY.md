# Local verification record

This document records a local candidate before upload. Resource reconstruction and scoring passed same-machine CPU acceptance. The native v11 status below preserves the packaging history; a later development-equivalence receipt recorded **LOCAL_EQUIVALENCE_PASS_PENDING_CLAUDE_RECOMPUTE**, detailed in the [status addendum](docs/NATIVE101A_STATUS_ADDENDUM.md). Inspector integration carried forward that receipt, with Claude review pending. Synthetic interface checks, real-data equivalence and independent reproduction on another machine each have their own evidence scope.

## Executed resource checks

Run from the repository root with reference Python 3.10.18 and NumPy 2.2.6. Users supply their own public MOT20 directories and new output directories outside the repository.

```bash
python -B scripts/score_tracker.py --self-test --gt-root "$GT_ROOT" --seqinfo-root "$SEQUENCE_ROOT" --out "$NEW_SELFTEST_DIR"
python -B scripts/reproduce.py --gt-root "$GT_ROOT" --seqinfo-root "$SEQUENCE_ROOT" --out "$NEW_REPRO_DIR"
```

The first check took 167.094 seconds and returned SELF_TEST_PASS. Using MOT20-01/02 only, it reconstructed 724 confirmed crossings from public GT. All three example trackers matched frozen references for per-sequence and per-gate values, final-event lists and main metrics.

|Example output|Low|Mid-low|Mid-high|High|All|Identity precision|
|---|---:|---:|---:|---:|---:|---:|
|ByteTrack|83/180|142/171|149/163|206/210|580/724|580/644|
|OC-SORT|70/180|137/171|147/163|206/210|560/724|560/593|
|BoT-SORT without ReID|84/180|142/171|150/163|208/210|584/724|584/634|

The second check took 39.516 seconds. Derived-label contents matched exactly, and the existing YOLOX+v11 example scores matched the resource reference. This check consumed saved events and observations; CrowdDet v11 cache retracking belongs to a separate regression.

## Synthetic and structural checks

The following checks were executed on synthetic/structural inputs. Downloads, training, GPU inference and human answers remained outside their scope:

```bash
python -B scripts/run_resource_synthetic.py
python -I -S -B tests/test_pipeline_portability.py
python -B tests/test_native_v11_scoring.py
node review/q2/r15e30_blind_review_template_check.js
node review/q3/synthetic_ui_test.js "$NEW_SYNTHETIC_TEST_DIR"
```

- Resource adapters passed 9 checks, and the original evidence entry point passed 13.
- Pipeline portability passed 16 checks, including x/y +1 for MOTChallenge export, frozen confirmation-control validation and rejection of redirected workspaces.
- Native-event identity scoring passed 10 synthetic tests. It consumes saved native final_events and calls frozen identity and matching functions. Standard-track box decoding is a separate path. Frozen development-sequence guards run before GT content is read.
- The Q2 template passed 19 checks and Q3's simulated DOM passed 29. Human review and real-video playback require separate acceptance; actual review materials are delivered separately.

## Frozen sources and new adapters

The historical `FROZEN_CODE_MAP.json` record distinguishes 84 complete copies and 16 user-approved verbatim source-node slices. Slice records include the original file SHA256, physical line numbers, node name and slice SHA256. New entry points, path handling and input guards are separate adapters bound by `MANIFEST.json`. See [porting differences](docs/PIPELINE_PATCHDIFF.md) for compatibility changes and scope.

The original core MANIFEST SHA256 is `b022a6debd0dced5ace6c8b4a00e4bdd2e7663d20128ddc5bf8e560149c530e9`. The original-project v0.1 MANIFEST remains `3ffd2f904936a0a1d6d960c85d1afafc2a88f8395694772ffcd796b98987517a`; that earlier release retains its original bytes.

## Historical open gates

The earlier pause record preserves an input-scope incident: native v11 real-cache regression was pending when preparation mistakenly read a mixed-sequence geometry/height metadata container. The issue was recorded and regression paused for an input-scope decision before tracking or scoring. The proposed correction used existing clean development-only resources. Acceptance required exact MOT20-01/02 per-gate events and reproduction of 86/180, 203/210 and 569/712. This gate has its own real-input comparison. A later local equivalence receipt passed; see the [status addendum](docs/NATIVE101A_STATUS_ADDENDUM.md) for comparison scope and review status. Claude acceptance and independent-machine acceptance remained separate pending steps.

GPU export, author-tracker panels and the complete confirmation workflow retained their historical execution evidence during this packaging round. Analysis directories provide traceable scientific functions and explicit adapters, each with its stated coverage. Environment versions describe the observed reference setup; clean-machine installation and cross-machine bitwise agreement remained unverified.

## Repository audit

```bash
python -I -S -B scripts/verify_repository.py --report "$NEW_EXTERNAL_AUDIT_JSON"
```

The auditor checks the manifest, frozen source hashes, Python syntax, compressed text and path patterns for each file. Model execution is outside its scope. Maintainers may add local identity tokens through `--forbid-token`, keeping the tokens themselves outside the repository. A numeric match to a username was verified as a GT source-line number and preserved; its narrow exception is bound in `metadata/privacy_reviewed_exceptions.json`. Upstream author names and contact details remain as required attribution. Pattern scans cover their defined rules; public release also requires human rights and attribution review.

The distribution contains permitted development-derived labels, numerical outputs, code and provenance. Original GT, images, videos, weights, stadium data, human answers and conversation logs remain outside it. Two-person review, final rights/attribution review and independent reproduction remained incomplete in this historical snapshot.
