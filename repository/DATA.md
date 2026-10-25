# Data, weights and provenance

The core CPU path uses local official MOT20-01/02 GT, sequence metadata and bundled numerical outputs. Images, weights and GPU execution belong to the pixel workflow. Users obtain data and weights from the original sources and prepare their environments explicitly; this handoff performed documentation work with the existing inputs.

## MOT20 and repository contents

The official entry point is [MOTChallenge MOT20](https://motchallenge.net/data/MOT20/). Under the recorded license review and frozen release notes, derived labels, geometry and numerical examples use CC BY-NC-SA 3.0; see [DATA_LICENSE](DATA_LICENSE), [core attribution](core/ATTRIBUTION.md) and [change notes](core/CHANGES.md). This page cites the existing 2026-10-23 review; current online status has a separate verification scope. Sources: S28, S29, S30.

Original-data attribution: Patrick Dendorfer, Hamid Rezatofighi, Anton Milan, Javen Shi, Daniel Cremers, Ian Reid, Stefan Roth, Konrad Schindler and Laura Leal-Taixé, *MOT20: A benchmark for multi object tracking in crowded scenes* (2020), [paper](https://arxiv.org/abs/2003.09003). Retain the data attribution and adaptation notice when using derived labels. The adaptation carries no endorsement from the original authors. Source: S28.

|Material|Included in the repository|Inputs or handling supplied separately|
|---|---|---|
|MOT20-01/02 development resource|Derived transitions/confirmed events, geometry, lineage, frozen generation/scoring code and numerical examples|Lawfully acquired official GT and `seqinfo.ini`; local images for rendering or pixel inference|
|MOT20-03/05 confirmation|Aggregate tables in [RESULTS](RESULTS.md), confirmation-control code and explicit input contracts|Sealed data remain outside the package; command preparation and scientific execution have separate authorization and receipts|
|Historical stadium exploration|Aggregate findings, research history and limitations|Source video, clips, window lists, human labels and sealed tests remain outside the public reproduction inputs|
|Q2/Q3 human review|Protocols and empty interface templates|Materials and answers are managed under separate delivery agreements; human-review completion has its own status|
|Detection/tracking weights|Fixed sources and hashes of locally acquired files below|Weight files and the adapted runtime environment are prepared separately|

Complete official GT files remain outside the package. CPU commands use the following directory layout; `GT_TRAIN_ROOT` and `SEQINFO_TRAIN_ROOT` may be the same directory.

`core/labels/` contains derived labels, `core/examples/` numerical system outputs, and `core/expected/` designated regression references. Human Q2/Q3 answers have their own storage. Added detector/tracker sources retain upstream licenses; the older core README's implementation-scope statement applies to that historical core version.

```text
GT_TRAIN_ROOT/
  MOT20-01/gt/gt.txt
  MOT20-02/gt/gt.txt
SEQINFO_TRAIN_ROOT/
  MOT20-01/seqinfo.ini
  MOT20-02/seqinfo.ini
```

Verify versions using the frozen package's source manifest. This documentation pass retained the existing GT evidence. Matching filenames alone leave version identity unresolved. Pixel manifests explicitly name each sequence's image directory, metadata and required assets; see [PIPELINE_PORTABILITY](docs/PIPELINE_PORTABILITY.md).

## Fixed files from the approved download ledger

The following URLs, sizes and SHA256 values are transcribed from approved ledgers S26/S27. Their public source fields are reproduced here; the full ledgers contain local-machine paths and remain outside the distribution. **These SHA256 values identify the files acquired at that time. Upstream checksums were unavailable for the YOLOX/ReID weights and ByteTrack archive, so upstream authentication remains a separate evidence requirement.** Current link availability was outside this documentation pass.

|Purpose and file|Public source|Bytes|SHA256|
|---|---|---:|---|
|YOLOX-X / ByteTrack MOT17 detector weights `bytetrack_x_mot17.pth.tar`|[Official release link](https://drive.google.com/file/d/1P4mY0Yyd3PPTybgZkjMYhFri88nTmJX5/view?usp=sharing)|792835731|`e3945f3523fde1e107708aacd64dab0670c34e371d136e54587cac7a50d3cfba`|
|ByteTrack fixed-commit source archive `ByteTrack-d1bf0191adff59bc8fcfeaa0b33d3d1642552a99.zip`|[Fixed-commit archive](https://github.com/FoundationVision/ByteTrack/archive/d1bf0191adff59bc8fcfeaa0b33d3d1642552a99.zip)|65562187|`c5a605478e443ce7df1564bfceb4799fcc3b698099a42e6d295f9ca467446090`|
|Historical ReID #93 weights `mot17_sbs_S50.pth`|[Official release link](https://drive.google.com/file/d/1QZFWpoa80rqo7O-HXmlss8J8CnS7IUsN/view)|317604675|`eb2e83afe774c85f20b735a7fabc423659c022387187eba449419c18dd6b4fa9`|

The detector uses MOT17 weights. Recorded training mixtures include MOT17 train, CrowdHuman train/val, ETHZ and CityPersons; MOT17 results therefore describe a training-covered setting. Historical CrowdDet appears in results and research history; download instructions for its older weights require complete verified bindings. ReID weights are listed for historical provenance. Its driver-porting status and 03/05 confirmation membership remain as recorded separately. Sources: S01, S20, S23, S26, S27.

## Dependencies and license scope

The CPU core reference environment is Python 3.10.18 and NumPy 2.2.6. Pillow supports explicitly requested local-image rendering. Prepare additional detection, tracking and analysis dependencies according to [PIPELINE](PIPELINE.md) and the corresponding requirements files. GPU readiness has its own acceptance gate after CPU self-checks.

Project-code terms appear in [LICENSE_CODE](LICENSE_CODE); third-party implementations retain their original licenses. Apply data, model, software and training-data terms to their respective materials, including data attribution and share-alike requirements. Final rights, contribution attribution and public-hosting acceptance remained pending in this snapshot; license-file availability records one part of that review.

Original-project source paths and full SHA256 values appear under S01, S20, S23 and S26–S30 in [metadata/docs_sources.json](metadata/docs_sources.json). This ledger traces documentation sources; each original source has its own distribution status.
