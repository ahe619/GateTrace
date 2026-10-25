# Status and acceptance boundaries

This file records the status of the local development-only release candidate, v0, before external publication. The user supplies the official source GT separately from this directory.

Technical component checks completed during construction:

- Complete transition reconstruction: 901 transitions / 724 rule-confirmed, scientific fields equal to the approved filtered development reference. Original global JSONL line numbers differ because the sample is filtered; the explicit mapping preserves that difference.
- Score reconstruction from the numerical example and supplied GT: all saved main aggregate, per-sequence and twelve per-gate values match. Identity correctness: 603/724; precision: 603/665. Identity judgments are reconstructed from the numerical example and supplied GT.
- Matching ranges are computed from the reproduced legal graphs. They are new sample outputs that describe ambiguity among optimal pairings; historical numerical parity covers fields present in the prior score file, and statistical confidence has a separate meaning.
- Synthetic checks exercise unsafe paths, input absence, changed assets and manifest omissions. Internal code review covers implementation; scientific and independent human validation provide separate evidence.

The final one-command integration receipt is written outside this package and binds MANIFEST.json. Its PASS status must be checked before treating the assembled package as reproduced. Acceptance of the assembled package requires that receipt in addition to component PASS results.

Publication requirements outstanding when this status was recorded: independent clean-machine reproduction, human reference-label/identity review, named author and rights audit, archival license evidence, and the research-value gate. Human QC was recorded as not_reviewed. Rejected hypotheses retain their status, and confirmation-sequence execution requires separate authorization.
