"""Synthetic-only integrity checks: no GT, real output, images or answers."""
import copy
import json
import math
from pathlib import Path
import sys
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.audit_integrity import FrameIdentityIntegrityError, validate_frame_identity


def row(tid, x=0):
    return dict(track_id=tid, box=[x, 0.0, x + 10.0, 20.0], conf=0.8, line=1)


def observation(sf, index, source, status='valid', gid=7):
    result = dict(source_frame=sf, output_row_index=index, track_id=source['track_id'],
                  box=list(source['box']), status=status, gt_id=gid, gt_class=1,
                  gt_line=sf, assigned_iou=0.8, margin=0.2)
    if status == 'ambiguous':
        result.update(gt_id=None, margin=0.05)
    elif status == 'unmatched':
        result.update(gt_id=None, gt_class=None, gt_line=None, assigned_iou=None, margin=None)
    return result


def record(sf, observations):
    pairs = [[o['output_row_index'], o['gt_id'] if o['gt_id'] is not None else 99]
             for o in observations if o['status'] != 'unmatched']
    return dict(source_frame=sf, observations=observations,
                output_assignment=dict(pairs=pairs, cardinality=len(pairs), exact_cost='-4/5' if pairs else '0',
                                       iou_edges=[], containment_edges=[], residual_containment=[]))


def fixture():
    frames = {1: [row(10), row(11, 20)], 3: [row(10)], 4: [row(10)]}
    records = [record(1, [observation(1, 0, frames[1][0]), observation(1, 1, frames[1][1], 'ambiguous')]),
               record(2, []), record(3, [observation(3, 0, frames[3][0], 'unmatched')]),
               record(4, [observation(4, 0, frames[4][0], gid=8)])]
    records[3]['observations'][0]['gt_class'] = 6
    return records, frames, 4


class FrameIdentityIntegrityTests(unittest.TestCase):
    def check_rejected(self, change):
        records, frames, length = fixture()
        change(records, frames)
        with self.assertRaises(FrameIdentityIntegrityError):
            validate_frame_identity(records, frames, length)

    def test_sparse_input_and_genuine_empty_frame_accepted(self):
        records, frames, length = fixture()
        summary = validate_frame_identity(records, frames, length)
        self.assertEqual(summary, dict(schema='frame_identity_integrity_v1', status='VALIDATED', seq_length=4,
                                      frame_count=4, observation_count=4, input_row_count=4, empty_frames=1,
                                      frames_with_observations=3, unique_track_ids=2,
                                      status_counts={'valid': 2, 'ambiguous': 1, 'unmatched': 1}))
        json.dumps(summary, allow_nan=False)

    def test_all_empty_sequence_accepted(self):
        summary = validate_frame_identity([record(1, []), record(2, [])], {}, 2)
        self.assertEqual((summary['empty_frames'], summary['observation_count']), (2, 0))

    def test_explicit_empty_input_frame_accepted(self):
        records, frames, length = fixture()
        frames[2] = []
        self.assertEqual(validate_frame_identity(records, frames, length)['empty_frames'], 1)

    def test_single_pass_record_generator_accepted(self):
        records, frames, length = fixture()
        self.assertEqual(validate_frame_identity(iter(records), frames, length)['frame_count'], length)

    def test_inputs_are_not_mutated(self):
        records, frames, length = fixture()
        before = copy.deepcopy((records, frames))
        validate_frame_identity(records, frames, length)
        self.assertEqual((records, frames), before)

    def test_ambiguous_assigned_row_retains_class_and_line_but_not_gid(self):
        records, frames, length = fixture()
        obs = records[0]['observations'][1]
        self.assertIsNone(obs['gt_id'])
        self.assertEqual((obs['gt_class'], obs['gt_line']), (1, 1))
        self.assertEqual(validate_frame_identity(records, frames, length)['status_counts']['ambiguous'], 1)

    def test_frame_omission_at_any_position_is_not_an_empty_frame(self):
        for position in range(4):
            with self.subTest(position=position):
                self.check_rejected(lambda r, f, p=position: r.pop(p))

    def test_duplicate_frame_rejected(self):
        self.check_rejected(lambda r, f: r.insert(1, copy.deepcopy(r[0])))

    def test_frame_reordering_rejected(self):
        self.check_rejected(lambda r, f: r.__setitem__(slice(1, 3), [r[2], r[1]]))

    def test_extra_frame_rejected(self):
        self.check_rejected(lambda r, f: r.append(record(5, [])))

    def test_frame_number_types_and_ranges_rejected(self):
        for value in (0, -1, 5, 1.0, True, '1', None):
            with self.subTest(value=value):
                self.check_rejected(lambda r, f, v=value: r[0].__setitem__('source_frame', v))

    def test_missing_observation_rejected(self):
        self.check_rejected(lambda r, f: r[0]['observations'].pop())

    def test_extra_observation_on_genuine_empty_frame_rejected(self):
        self.check_rejected(lambda r, f: r[1]['observations'].append(copy.deepcopy(r[0]['observations'][0])))

    def test_duplicate_index_rejected(self):
        self.check_rejected(lambda r, f: r[0]['observations'][1].__setitem__('output_row_index', 0))

    def test_reordered_observations_rejected(self):
        self.check_rejected(lambda r, f: r[0]['observations'].reverse())

    def test_observation_index_type_and_range_rejected(self):
        for value in (-1, 2, True, 0.0, '0', None):
            with self.subTest(value=value):
                self.check_rejected(lambda r, f, v=value: r[0]['observations'][0].__setitem__('output_row_index', v))

    def test_cross_frame_observation_rejected(self):
        self.check_rejected(lambda r, f: r[0]['observations'][0].__setitem__('source_frame', 2))

    def test_track_id_mismatch_rejected(self):
        self.check_rejected(lambda r, f: r[0]['observations'][0].__setitem__('track_id', 123))

    def test_finite_box_mismatch_has_no_tolerance(self):
        self.check_rejected(lambda r, f: r[0]['observations'][0]['box'].__setitem__(0, 1e-12))

    def test_nonfinite_boxes_rejected_in_record_and_source(self):
        for value in (float('nan'), float('inf'), float('-inf')):
            for target in ('record', 'source'):
                with self.subTest(value=value, target=target):
                    def change(r, f):
                        (r[0]['observations'][0] if target == 'record' else f[1][0])['box'][0] = value
                    self.check_rejected(change)

    def test_nonfinite_auxiliary_audit_rejected(self):
        self.check_rejected(lambda r, f: r[0]['output_assignment']['iou_edges'].append({'iou': float('nan')}))

    def test_nonfinite_saved_scores_rejected(self):
        for field in ('assigned_iou', 'margin'):
            with self.subTest(field=field):
                self.check_rejected(lambda r, f, name=field: r[0]['observations'][0].__setitem__(name, float('inf')))

    def test_missing_observation_fields_rejected(self):
        for field in tuple(fixture()[0][0]['observations'][0]):
            with self.subTest(field=field):
                self.check_rejected(lambda r, f, name=field: r[0]['observations'][0].pop(name))

    def test_missing_frame_fields_rejected(self):
        for field in ('source_frame', 'observations', 'output_assignment'):
            with self.subTest(field=field):
                self.check_rejected(lambda r, f, name=field: r[0].pop(name))

    def test_unknown_status_rejected(self):
        for status in ('known', 'unknown', 'ignore', '', None, [], True):
            with self.subTest(status=status):
                self.check_rejected(lambda r, f, s=status: r[0]['observations'][0].__setitem__('status', s))

    def test_valid_status_requires_gid(self):
        self.check_rejected(lambda r, f: r[0]['observations'][0].__setitem__('gt_id', None))

    def test_ambiguous_status_requires_null_gid(self):
        self.check_rejected(lambda r, f: r[0]['observations'][1].__setitem__('gt_id', 99))

    def test_unmatched_status_requires_all_null_assignment_fields(self):
        for field, value in (('gt_id', 7), ('gt_class', 1), ('gt_line', 3), ('assigned_iou', 0.0), ('margin', 0.0)):
            with self.subTest(field=field):
                self.check_rejected(lambda r, f, k=field, v=value: r[2]['observations'][0].__setitem__(k, v))

    def test_status_margin_contradiction_rejected(self):
        self.check_rejected(lambda r, f: r[0]['observations'][0].__setitem__('margin', 0.09))
        self.check_rejected(lambda r, f: r[0]['observations'][1].__setitem__('margin', 0.10))

    def test_assigned_score_range_rejected(self):
        for value in (0.49, True, '0.8'):
            with self.subTest(value=value):
                self.check_rejected(lambda r, f, v=value: r[0]['observations'][0].__setitem__('assigned_iou', v))

    def test_no_extra_iou_or_margin_upper_bound_is_imposed(self):
        records, frames, length = fixture()
        slightly_above_one = math.nextafter(1.0, math.inf)
        records[0]['observations'][0].update(assigned_iou=slightly_above_one, margin=slightly_above_one)
        self.assertEqual(validate_frame_identity(records, frames, length)['status'], 'VALIDATED')

    def test_invalid_gt_class_and_line_rejected(self):
        self.check_rejected(lambda r, f: r[0]['observations'][0].__setitem__('gt_class', 2))
        self.check_rejected(lambda r, f: r[0]['observations'][0].__setitem__('gt_line', 0))

    def test_input_duplicate_track_id_rejected(self):
        self.check_rejected(lambda r, f: f[1][1].__setitem__('track_id', 10))

    def test_input_cross_frame_metadata_rejected(self):
        self.check_rejected(lambda r, f: f[1][0].__setitem__('source_frame', 2))

    def test_input_frame_outside_sequence_rejected(self):
        self.check_rejected(lambda r, f: f.__setitem__(5, []))

    def test_input_invalid_box_rejected(self):
        self.check_rejected(lambda r, f: f[1][0].__setitem__('box', [0, 0, 0, 20]))

    def test_invalid_length_rejected(self):
        for length in (0, -1, True, 4.0, '4', None):
            with self.subTest(length=length):
                with self.assertRaises(FrameIdentityIntegrityError):
                    validate_frame_identity([], {}, length)

    def test_invalid_container_rejected(self):
        for records, frames in ((None, {}), ([], [])):
            with self.subTest(records=records, frames=frames):
                with self.assertRaises(FrameIdentityIntegrityError):
                    validate_frame_identity(records, frames, 1)

    def test_invalid_assignment_envelope_rejected(self):
        self.check_rejected(lambda r, f: r[0].__setitem__('output_assignment', {}))
        self.check_rejected(lambda r, f: r[0]['output_assignment'].__setitem__('cardinality', 1))
        self.check_rejected(lambda r, f: r[0]['output_assignment'].__setitem__('exact_cost', 'NaN'))

    def test_assignment_duplicate_or_out_of_range_index_rejected(self):
        for pair in ([0, 99], [2, 99], [1, 7]):
            with self.subTest(pair=pair):
                self.check_rejected(lambda r, f, p=pair: r[0]['output_assignment']['pairs'].__setitem__(1, p))

    def test_assignment_valid_identity_mismatch_rejected(self):
        self.check_rejected(lambda r, f: r[0]['output_assignment']['pairs'][0].__setitem__(1, 8))

    def test_assignment_pair_missing_for_ambiguous_row_rejected(self):
        def change(r, f):
            r[0]['output_assignment']['pairs'].pop()
            r[0]['output_assignment']['cardinality'] = 1
        self.check_rejected(change)


if __name__ == '__main__':
    unittest.main()
