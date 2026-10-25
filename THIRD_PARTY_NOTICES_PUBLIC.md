# Public distribution notices

This notice accompanies the complete GateTrace source package as distributed on 2026-10-25. The paths below identify the unchanged scientific files to which these notices apply. Existing notices inside those files and directories remain intact.

## SORT and OC-SORT

Paths:

- `repository/src/track/frozen/sota83d/vendor/oc/ocsort.py`
- `repository/src/track/frozen/sota83d/vendor/oc/association.py`

SORT: Copyright (C) 2016 Alex Bewley. SORT was published under the GNU General Public License, version 3 or any later version. The inherited SORT portions of these files, the combined OC-SORT component, and GateTrace's combined OC execution program are distributed under GPL version 3 or any later version, as described in LICENSE_SCOPE.md. Independently usable MIT modules retain their MIT grants. A full GPLv3 copy accompanies this release at `LICENSES/GPL-3.0.txt`. The software carries the warranty and liability terms of that license.

OC-SORT: the upstream repository's MIT license, including Copyright (c) 2021 Yifu Zhang, remains at `repository/src/track/frozen/sota83d/vendor/oc/LICENSE`. Its full permission and warranty notice remains available for the contributions it covers. OC-SORT's source explicitly credits adaptation from SORT. These upstream notices and the inherited GPL terms accompany the component together.

Sources:

- SORT's first public source and GPLv3-or-later header: https://github.com/abewley/sort/blob/dbffde9f6578b3dee89421fc0a2bb711b31e7cb9/sort.py
- SORT's initial GPLv3 text: https://github.com/abewley/sort/blob/d3761f26e04087e1e040f7818f092de76f769875/LICENSE
- GateTrace's fixed OC-SORT source revision: https://github.com/noahcao/OC_SORT/tree/8462e7e729a93ccd3bd995c0a79a890336cb3a0b

The exact SORT revision used by the OC-SORT authors is not asserted. The historical source above establishes the public license predating OC-SORT. No separate permissive grant is asserted. GateTrace's published source contains project adaptations already present by 2026-10-25; their hashes and source relationships are in the frozen source map. Original scientific files remain unchanged by this licensing addition.

## YOLOX and ByteTrack

Paths: `repository/src/detect/frozen/r15_yolox82e_vendor/` and `repository/src/track/frozen/sota83d/vendor/byte/`.

The detector implementation was vendored from ByteTrack commit `d1bf0191adff59bc8fcfeaa0b33d3d1642552a99`. The copied MIT notice credits Yifu Zhang (2021). YOLOX-origin model, preprocessing, postprocessing and fusion code retain their Megvii copyright headers. YOLOX publishes its implementation under Apache-2.0; the license text is included at `LICENSES/Apache-2.0.txt` in addition to the existing ByteTrack MIT notice.

The detector copy contains explicit private imports, selected helper functions and the documented inference adapter. The project did not change the frozen model mathematics when creating this distribution. Changes and source boundaries are described in `repository/docs/PIPELINE_PATCHDIFF.md` and `repository/src/detect/frozen/r15_yolox82e_vendor/NOTICE.md`.

Sources: https://github.com/FoundationVision/ByteTrack/tree/d1bf0191adff59bc8fcfeaa0b33d3d1642552a99 and https://github.com/Megvii-BaseDetection/YOLOX/tree/0.3.0 . The YOLOX tag identifies the supplied license text; the frozen ByteTrack revision identifies the actual model-source snapshot used by GateTrace.

## BoT-SORT

Path: `repository/src/track/frozen/sota83d/vendor/bot/`.

The fixed source is BoT-SORT commit `251985436d6712aaf682aaaf5f71edb4987224bd`, with the MIT notice Copyright (c) 2022 Nir Aharon preserved in its directory. The project adaptations include private import paths, deprecated NumPy alias replacements, deferred unused appearance imports, and the documented NumPy implementation of bounding-box overlap. They were present in the historical execution copy. See the frozen source map and pipeline modification document. The bundled panel uses ReID disabled.

Source: https://github.com/NirAharon/BoT-SORT/tree/251985436d6712aaf682aaaf5f71edb4987224bd .

## FilterPy-derived Kalman filter

Path: `repository/src/track/frozen/sota83d/vendor/oc/kalmanfilter.py`.

The file credits Copyright 2014-2018 Roger R. Labbe Jr. and states an MIT license. The original credit is retained. A complete FilterPy MIT license accompanies this distribution at `LICENSES/FilterPy-MIT.txt`. Source: https://github.com/rlabbe/filterpy/tree/1.4.5 . The pinned OC-SORT revision identifies the actual adapted Kalman implementation; the FilterPy tag identifies the additional permission text supplied here.

## Ultralytics dependency

Paths: the native v11 tracking wrappers under `repository/src/track/`, including `frozen/r15e17_trackers.py` and `frozen/r15_tracker_idxfix.py`.

These wrappers integrate the externally installed Ultralytics 8.3.192 BYTETracker in the same process. Ultralytics' AGPLv3 license is included at `LICENSES/AGPL-3.0.txt`. Source and applicable terms: https://github.com/ultralytics/ultralytics/tree/v8.3.192 . Project wrapper source remains published here, with its original MIT grant retained and the combined-program scope stated in LICENSE_SCOPE.md. No commercial or enterprise license is claimed.

## Other dependencies and citations

NumPy, Torch, torchvision, SciPy, LAP, OpenCV, Pillow and other separately installed dependencies retain their own licenses and notices. Their versions used for the historical execution appear in the repository's environment records. Model weights retain their upstream terms and are acquired separately. Research citations in the repository identify the methods and datasets used; citations complement the software and data notices.
