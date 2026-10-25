"""Pure, synthetic-validated E2 deletion-mask candidate. No module-level I/O."""

from __future__ import annotations

from dataclasses import dataclass
from fractions import Fraction
import hashlib
import json
import random
from typing import Iterable, Mapping


RETENTIONS = ("1", "0.9", "0.75", "0.5", "0.25")
SEEDS = (20261023, 20261024, 20261025)
MODES = ("iid", "block")
STREAM_VERSION = "e2-mask-candidate-v1"


@dataclass(frozen=True)
class Observation:
    sequence_id: str
    identity_id: str
    frame: int
    visibility_bin: str

    @property
    def key(self) -> tuple[str, str, int]:
        return (self.sequence_id, self.identity_id, self.frame)


@dataclass(frozen=True)
class Segment:
    segment_id: str
    observations: tuple[Observation, ...]


@dataclass(frozen=True)
class SegmentMask:
    segment_id: str
    sequence_id: str
    identity_id: str
    visibility_bin: str
    first_frame: int
    last_frame: int
    input_count: int
    kept_count: int
    deleted_count: int
    block_frames: int
    deleted_ids: tuple[tuple[str, str, int], ...]
    missing_run_lengths: tuple[int, ...]


@dataclass(frozen=True)
class MaskResult:
    retention: str
    seed: int | None
    mode: str
    kept: tuple[Observation, ...]
    deleted: tuple[Observation, ...]
    segments: tuple[SegmentMask, ...]

    @property
    def kept_ids(self) -> tuple[tuple[str, str, int], ...]:
        return tuple(item.key for item in self.kept)

    @property
    def deleted_ids(self) -> tuple[tuple[str, str, int], ...]:
        return tuple(item.key for item in self.deleted)


def _json(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


def _canonical(observations: Iterable[Observation]) -> tuple[Observation, ...]:
    records = tuple(observations)
    seen: set[tuple[str, str, int]] = set()
    for record in records:
        if not isinstance(record, Observation):
            raise TypeError("Each record must be an Observation")
        if any(not isinstance(value, str) or not value for value in
               (record.sequence_id, record.identity_id, record.visibility_bin)):
            raise ValueError("Sequence, identity, and visibility labels must be nonempty strings")
        if type(record.frame) is not int or record.frame < 0:
            raise ValueError("Frame must be a nonnegative integer")
        if record.key in seen:
            raise ValueError("Duplicate sequence/identity/frame key: " + repr(record.key))
        seen.add(record.key)
    return tuple(sorted(records, key=lambda item: item.key))


def _segment(records: tuple[Observation, ...]) -> Segment:
    first, last = records[0], records[-1]
    descriptor = [first.sequence_id, first.identity_id, first.visibility_bin,
                  first.frame, last.frame]
    segment_id = hashlib.sha256(_json(descriptor).encode("utf-8")).hexdigest()
    return Segment(segment_id=segment_id, observations=records)


def _segments(records: tuple[Observation, ...]) -> tuple[Segment, ...]:
    segments: list[Segment] = []
    current: list[Observation] = []
    for record in records:
        if current:
            previous = current[-1]
            if (record.sequence_id != previous.sequence_id or
                    record.identity_id != previous.identity_id or
                    record.visibility_bin != previous.visibility_bin or
                    record.frame != previous.frame + 1):
                segments.append(_segment(tuple(current)))
                current = []
        current.append(record)
    if current:
        segments.append(_segment(tuple(current)))
    return tuple(segments)


def build_segments(observations: Iterable[Observation]) -> tuple[Segment, ...]:
    """Validate keys, canonicalize order, and split at gaps/visibility changes."""
    return _segments(_canonical(observations))


def deletion_count(retention: str, segment_length: int) -> int:
    """Return the exact rational floor((1-r)N) for the fixed protocol grid."""
    if not isinstance(retention, str) or retention not in RETENTIONS:
        raise ValueError("Retention must be one of the exact protocol strings")
    if type(segment_length) is not int or segment_length < 0:
        raise ValueError("Segment length must be a nonnegative integer")
    ratio = (1 - Fraction(retention)) * segment_length
    return ratio.numerator // ratio.denominator


def block_frames(native_fps: int | str | Fraction) -> int:
    """Candidate positive half-up rounding of 0.5 native-fps seconds."""
    if isinstance(native_fps, bool) or not isinstance(native_fps, (int, str, Fraction)):
        raise TypeError("Native fps must be explicit exact int, decimal string, or Fraction")
    try:
        fps = Fraction(native_fps)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("Native fps must be a positive exact number") from error
    if fps <= 0:
        raise ValueError("Native fps must be positive")
    rounded = fps / 2 + Fraction(1, 2)
    return max(1, rounded.numerator // rounded.denominator)


def segment_rng(seed: int, retention: str, mode: str, segment_id: str) -> random.Random:
    """Local stream construction exposed so the exact candidate can be audited."""
    payload = [STREAM_VERSION, seed, retention, mode, segment_id]
    digest = hashlib.sha256(_json(payload).encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest, "big"))


def missing_run_lengths(frames: Iterable[int]) -> tuple[int, ...]:
    """Lengths of actual consecutive runs; input must contain distinct frames."""
    ordered = sorted(frames)
    if len(set(ordered)) != len(ordered):
        raise ValueError("Duplicate frames in missing-run input")
    lengths: list[int] = []
    previous: int | None = None
    for frame in ordered:
        if previous is not None and frame == previous + 1:
            lengths[-1] += 1
        else:
            lengths.append(1)
        previous = frame
    return tuple(lengths)


def make_mask(
    observations: Iterable[Observation],
    *,
    retention: str,
    seed: int,
    mode: str,
    fps_by_sequence: Mapping[str, int | str | Fraction],
) -> MaskResult:
    """Return unchanged immutable records partitioned into kept/deleted tuples.

    No GT validity, visibility classification, box conversion, tracking, or I/O
    occurs here. A separately reviewed adapter must provide frozen valid records.
    """
    deletion_count(retention, 0)
    if type(seed) is not int or seed not in SEEDS:
        raise ValueError("Seed must be one of the three protocol seeds")
    if mode not in MODES:
        raise ValueError("Mode must be iid or block")
    records = _canonical(observations)
    segments = _segments(records)
    block_sizes: dict[str, int] = {}
    for sequence_id in sorted({record.sequence_id for record in records}):
        if sequence_id not in fps_by_sequence:
            raise ValueError("Missing native fps for sequence: " + sequence_id)
        block_sizes[sequence_id] = block_frames(fps_by_sequence[sequence_id])
    deleted_keys: set[tuple[str, str, int]] = set()
    stats: list[SegmentMask] = []
    for segment in segments:
        items = segment.observations
        first, last = items[0], items[-1]
        count = deletion_count(retention, len(items))
        block_size = block_sizes[first.sequence_id]
        chosen: set[int] = set()
        if count:
            rng = segment_rng(seed, retention, mode, segment.segment_id)
            if mode == "iid":
                chosen.update(rng.sample(range(len(items)), count))
            else:
                starts = list(range(0, len(items), block_size))
                rng.shuffle(starts)
                remaining = count
                for start in starts:
                    take = min(remaining, block_size, len(items) - start)
                    chosen.update(range(start, start + take))
                    remaining -= take
                    if not remaining:
                        break
        deleted = tuple(items[index] for index in sorted(chosen))
        ids = tuple(record.key for record in deleted)
        deleted_keys.update(ids)
        stats.append(SegmentMask(
            segment.segment_id, first.sequence_id, first.identity_id,
            first.visibility_bin, first.frame, last.frame, len(items),
            len(items) - count, count, block_size, ids,
            missing_run_lengths(record.frame for record in deleted),
        ))
    return MaskResult(
        retention=retention,
        seed=None if retention == "1" else seed,
        mode="baseline" if retention == "1" else mode,
        kept=tuple(record for record in records if record.key not in deleted_keys),
        deleted=tuple(record for record in records if record.key in deleted_keys),
        segments=tuple(stats),
    )


def make_grid(
    observations: Iterable[Observation],
    *,
    fps_by_sequence: Mapping[str, int | str | Fraction],
) -> tuple[MaskResult, ...]:
    """Construct one common baseline and the 24 protocol degradation masks."""
    records = tuple(observations)
    results = [make_mask(records, retention="1", seed=SEEDS[0], mode=MODES[0],
                         fps_by_sequence=fps_by_sequence)]
    for retention in RETENTIONS[1:]:
        for seed in SEEDS:
            for mode in MODES:
                results.append(make_mask(records, retention=retention, seed=seed,
                                         mode=mode, fps_by_sequence=fps_by_sequence))
    return tuple(results)
