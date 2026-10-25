# Human review: protocols and empty templates

This directory supplies protocols and empty interfaces. Formal item manifests, original videos, system outputs, group mappings and reviewer answers remain outside this distribution. The research lead manages the user's separately supplied answers under the original protocol.

## Review questions

- **Q2: visual evidence for remaining misses.** Reviewers assess whether any identifiable part of the target is visible before and after the crossing, and whether the original images support an actual crossing. A visible head may suffice; movement of the reference box alone leaves visual support unresolved. Model-failure explanations require further evidence. Group comparisons follow the frozen rules after two independent submissions are locked and unblinding is authorized.
- **Q3: support for derived labels.** Reviewers assess crossing, direction, identity continuity and temporal identifiability, recording visual uncertainty, technical failure, an unlocated target and an unreviewed item separately. Reference GT remains subject to review; matching uncertain judgments retain uncertain status.

The historical Q3 batch described in this snapshot had 77 items: 72 confirmed, 4 unconfirmed and 1 search window. This records completed material preparation; independent two-person review has a separate completion gate. The media and answers for these 77 items remain outside this repository.

## Templates and protocols

- `q2/r15e30_blind_review_template.html`: English-localized empty template with original behavior and schema preserved. Its default item list is empty, so validation refuses to start. Organizers may replace only the public JSON element `id="dataset"`.
- `q3/review_template.html`: English-localized template preserving original behavior and schema, retaining `__PUBLIC_ITEMS_JSON__`. Organizers must populate the original schema before collecting formal answers.
- `../protocols/human_qc/`: original protocol copies, read in precedence order v1→v2→86 amendment→87 amendment. Other datasets in early protocols describe historical plans. The material and human-review scope recorded here is MOT20-01/02.
- File hashes and original relative paths appear in `../metadata/human_materials_map.json`.

Both templates save locally in the browser and support exported backups. Reviewer codes distinguish records; authentication is a separate concern. Reviewers should use separate devices or browser profiles, preserve independent answers and import only their own backups. Browser storage may be lost, so export after every session. Keep exported answers in the separately managed answer location.

## Synthetic checks

Run from the repository root. Node is an optional development-check tool; CPU scoring has its own dependencies.

```text
node review/q2/r15e30_blind_review_template_check.js
node review/q3/synthetic_ui_test.js ../qc_synthetic_new
```

The second output path must contain `synthetic` and should be a new external directory. Checks use synthetic manifests/answers and a simulated DOM. Browser storage, real media playback and human review require their own validation. Packaging preserved the existing review rules and Q2 blinding state.
