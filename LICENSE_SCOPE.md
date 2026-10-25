# GateTrace software and data licenses

Date of this distribution notice: 2026-10-25.

GateTrace brings together project-authored evaluation software and adapted open-source inference components. The source files, numerical examples and frozen scientific records retain their recorded bytes. The license terms below apply to their respective components and to combinations that use them.

## Project-authored software

The existing MIT grant in [repository/LICENSE_CODE](repository/LICENSE_CODE) applies to project-authored code within its stated scope. The independent evaluation core retains [its MIT grant](repository/core/LICENSE_CODE). Those grants remain available when the modules are used independently. They do not replace upstream grants on incorporated or linked software.

## Inference components and combined programs

| Component | Distribution terms and notices |
|---|---|
| SORT-derived OC-SORT implementation | The SORT-derived portions, the combined OC-SORT component, and GateTrace's combined OC execution program are distributed under GPL version 3 or any later version. Existing MIT grants remain available for independently usable MIT modules and contributions. See [the path-bound notice](THIRD_PARTY_NOTICES_PUBLIC.md#sort-and-oc-sort), [GPLv3 text](LICENSES/GPL-3.0.txt) and [source-license map](SOURCE_LICENSE_MAP.json). |
| Native v11 / Ultralytics integration | The integration imports and subclasses Ultralytics 8.3.192 in one process. The combined program is subject to the applicable AGPLv3 terms. Project modules retain their separate MIT grants. The pinned dependency's source and license are identified below. |
| ByteTrack and BoT-SORT adaptations | The existing upstream MIT notices remain in their source directories. |
| YOLOX-derived model code vendored through ByteTrack | Preserve both ByteTrack's MIT contribution notice and the Apache-2.0 terms applicable to the YOLOX-origin material. Megvii copyright headers remain intact. |
| FilterPy-derived OC-SORT Kalman filter | Retain Roger R. Labbe Jr.'s notice and the MIT grant supplied in [LICENSES/FilterPy-MIT.txt](LICENSES/FilterPy-MIT.txt). |
| Bounding-box overlap translation | The original Microsoft and WANG Chenxi MIT notices and full permission text remain embedded in the source. |

GPLv3 and AGPLv3 section 13 provide for their specified combinations. Each covered portion retains its respective license; the AGPL network-source provision applies to the combination when applicable. A distributor of a combined application must comply with its source, notice and other applicable obligations. These conditions also apply when a dependency is obtained separately and integrated into the application.

This repository supplies the source form of GateTrace's adapters and modifications. External runtime packages remain separately obtained dependencies. Ultralytics is pinned to [v8.3.192 source](https://github.com/ultralytics/ultralytics/tree/v8.3.192), with its verbatim license included in [LICENSES/AGPL-3.0.txt](LICENSES/AGPL-3.0.txt). Anyone distributing a packaged executable/environment or operating a modified network service must provide the corresponding source required for that distribution or service. An upstream link alone is insufficient if it fails to make the required corresponding version available.

## Data and numerical outputs

Derived labels and numerical examples retain their existing [data license](repository/DATA_LICENSE) and [MOT attribution](repository/core/ATTRIBUTION.md). Code licenses and data licenses have separate scopes. Original MOT images, complete official GT, model weights, private stadium data and human-review answers are outside this package. Model licenses must be checked at their official sources when acquiring weights.

## Provenance and historical changes

The frozen source map and modification documentation remain in [repository/FROZEN_CODE_MAP.json](repository/FROZEN_CODE_MAP.json) and [repository/docs/PIPELINE_PATCHDIFF.md](repository/docs/PIPELINE_PATCHDIFF.md). The public source includes the project's pre-existing compatibility and I/O adaptations. This notice adds licensing material without changing their implementations or experimental results.

The SORT author publicly offered a separate permissive-license route. GateTrace has no record of a grant covering this OC-SORT derivation, and this release does not rely on one. It follows the public GPL grant for the inherited SORT material. This treatment leaves the existing upstream notices visible and makes no claim about private agreements or third-party misconduct.

License texts are reproduced verbatim. Their retrieval sources and hashes are recorded in [LICENSES/SOURCES.json](LICENSES/SOURCES.json). This scope statement accompanies the licenses; the complete applicable license texts control the rights they grant.
