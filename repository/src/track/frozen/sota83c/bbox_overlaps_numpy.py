"""NumPy translation of cython_bbox 0.1.5's inclusive-endpoint overlap formula.

Scope: finite float64 arrays of shape (N, 4), including inverted/degenerate boxes.
No epsilon, coordinate clipping, width clamping, or alternate IoU convention.
This is an explicitly approved implementation substitution, not the compiled
upstream extension. Its proof is source review plus a scalar Python comparison.

Upstream: cython_bbox-0.1.5/src/cython_bbox.pyx
SHA256: 6b820fda8bd75e06335ad047ea0277af0da86cbbf0a99ab4a0597ab57d2df709
Written upstream by Sergey Karayev; Fast R-CNN.
Copyright (c) 2015 Microsoft Corporation
Copyright (c) 2018 WANG Chenxi

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

Complete upstream license/notices are preserved in
data/r15/sota_panel83c/bbox_proof/UPSTREAM_LICENSE.
"""

import numpy as np


def _check_input(value, name):
    if not isinstance(value, np.ndarray) or value.dtype != np.dtype(np.float64):
        raise TypeError(name + " must be a float64 numpy.ndarray")
    if value.ndim != 2 or value.shape[1] != 4:
        raise ValueError(name + " must have shape (N, 4)")
    if not np.isfinite(value).all():
        raise ValueError(name + " contains NaN or infinity; unsupported input")


def bbox_overlaps(boxes, query_boxes):
    """Return (N,K) float64 overlaps using the upstream +1 pixel convention.

Input guards deliberately reject values outside the finite Nx4 contract.
Arithmetic overflow/non-finite results stop the caller, rather than being
replaced with zeros or clipped. No input array is modified.
"""
    _check_input(boxes, "boxes")
    _check_input(query_boxes, "query_boxes")
    overlaps = np.zeros((boxes.shape[0], query_boxes.shape[0]), dtype=np.float64)
    if boxes.shape[0] == 0 or query_boxes.shape[0] == 0:
        return overlaps
    with np.errstate(over="raise", divide="raise", invalid="raise"):
        # The subtraction/addition/multiplication order is the pyx order.
        query_area = ((query_boxes[:, 2] - query_boxes[:, 0] + 1.0)
                      * (query_boxes[:, 3] - query_boxes[:, 1] + 1.0))
        iw = (np.minimum(boxes[:, None, 2], query_boxes[None, :, 2])
              - np.maximum(boxes[:, None, 0], query_boxes[None, :, 0]) + 1.0)
        n, k = np.nonzero(iw > 0.0)
        if n.size == 0:
            return overlaps
        # Like the pyx, compute height only for a strictly positive width.
        ih = (np.minimum(boxes[n, 3], query_boxes[k, 3])
              - np.maximum(boxes[n, 1], query_boxes[k, 1]) + 1.0)
        positive_height = ih > 0.0
        n, k, ih = n[positive_height], k[positive_height], ih[positive_height]
        if n.size == 0:
            return overlaps
        iw = iw[n, k]
        box_area = ((boxes[n, 2] - boxes[n, 0] + 1.0)
                    * (boxes[n, 3] - boxes[n, 1] + 1.0))
        intersection = iw * ih
        # Do not reassociate this expression or fuse its operations.
        union = box_area + query_area[k] - intersection
        values = intersection / union
        if not np.isfinite(values).all():
            raise FloatingPointError("Non-finite overlap; unsupported arithmetic")
        overlaps[n, k] = values
    return overlaps
