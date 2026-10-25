# Attribution and provenance

This local release candidate contains derived data from **MOT20**, provided by MOTChallenge. Obtain the original data yourself from the official source: https://motchallenge.net/data/MOT20/ . The official data page declares CC BY-NC-SA 3.0; this declaration was checked on 2026-10-23. This package does not redistribute the source images, videos or complete source annotations.

Source paper: Patrick Dendorfer, Hamid Rezatofighi, Anton Milan, Javen Shi, Daniel Cremers, Ian Reid, Stefan Roth, Konrad Schindler, Laura Leal-Taixé, *MOT20: A benchmark for multi object tracking in crowded scenes* (2020), https://arxiv.org/abs/2003.09003 . Cite the original dataset in addition to this resource when using the derived labels. A publication/DOI for this resource is not assigned.

The adaptation uses only **MOT20-01 and MOT20-02**. It fits the frozen development geometry, derives virtual-region crossing transitions from the annotated body-box bottom centre, retains confirmed and unconfirmed transitions, and adds frame lineage and evaluation records. These are new derived annotations; the original dataset authors have not endorsed this adaptation. See CHANGES.md for semantic distinctions.

The numerical example is the project's existing YOLOX-X + v11 development output. It uses the official ByteTrack MOT17 detector weight and project-frozen downstream processing. No detector/tracker implementation or weight is bundled. ByteTrack/YOLOX, the underlying datasets and all upstream software retain their own attribution and licenses. The sample is a representation of previously saved system outputs, not a reproduction of GPU inference.

The package source provenance manifests identify the project-authored functions used for derivation, identity association and matching. NumPy is an external dependency, not vendored code. No upstream Ultralytics, CrowdDet, OC-SORT, BoT-SORT or model implementation is relicensed or redistributed in this package.

Public-release readiness is separate from this technical prototype: contributor names, archival source-license evidence and an independent reproduction/QC receipt should be reviewed before publication. This note does not impose an additional restriction on the CC license.
