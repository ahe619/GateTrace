"""Adopted #47/#48 fix: preserve input indices across ByteTrack slices.

This project-local wrapper does not change the installed package, association
code, thresholds, Kalman state or STrack implementation. The caller supplies
its existing BYTETracker class and arguments. Only STrack.idx is assigned the
full update-input detection index instead of a high/low subset index.
Importing this helper reads no configurations, weights, saved results, media
or annotations. Adoption does not certify real event identity or accuracy.
"""
from __future__ import annotations

import numpy as np

ADOPTION_STATUS = 'adopted_by_instructions_47_48'


class IndexedDetections:
    """Read-only facade retaining row provenance through ordinary Boxes slices."""
    def __init__(self, boxes, original_indices=None):
        self._boxes = boxes
        indices = np.arange(len(boxes), dtype=np.int64) if original_indices is None else np.asarray(original_indices, dtype=np.int64)
        self.original_indices = np.atleast_1d(indices)
        if self.original_indices.ndim != 1 or len(self.original_indices) != len(boxes):
            raise ValueError('One original detection index is required per input row')

    def __len__(self):
        return len(self._boxes)

    def __getitem__(self, key):
        return IndexedDetections(self._boxes[key], self.original_indices[key])

    def __getattr__(self, name):
        # Coordinates, confidences, classes and other attributes are unchanged.
        return getattr(self._boxes, name)


def make_index_preserving_tracker_class(byte_tracker_class):
    """Return an isolated subclass of the supplied, installed BYTETracker.

    Usage::

        IndexFixedTracker = make_index_preserving_tracker_class(BYTETracker)
        tracker = IndexFixedTracker(args, frame_rate=round(fps))
        tracker.reset()
        tracks = tracker.update(boxes, img)

    Constructor/reset/update arguments and returned column order are unchanged.
    Results' last column now refers to the caller's complete boxes array. This
    factory does not monkeypatch either the supplied class or installed modules.
    """
    class IndexPreservingBYTETracker(byte_tracker_class):
        adoption_status = ADOPTION_STATUS

        def update(self, results, img=None, feats=None):
            if isinstance(results, IndexedDetections):
                raise TypeError('Pass original Boxes, not a pre-indexed subset')
            return super().update(IndexedDetections(results), img=img, feats=feats)

        def init_track(self, results, img=None):
            if not isinstance(results, IndexedDetections):
                raise TypeError('Original index provenance absent from tracker input')
            tracks = super().init_track(results, img)
            if len(tracks) != len(results):
                raise RuntimeError('Installed init_track changed its one-track-per-row contract')
            for track, original_index in zip(tracks, results.original_indices):
                track.idx = int(original_index)
            return tracks

    IndexPreservingBYTETracker.__name__ = 'IndexPreservingBYTETracker'
    return IndexPreservingBYTETracker
