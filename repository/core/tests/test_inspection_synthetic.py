"""Synthetic evidence tests. No real GT, tracking output, image or human label."""
import copy
from pathlib import Path
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from src.inspection import canonical_rows, valid_support, visibility_bin, Inspector, region_of
from src.frozen_score import e1, matching


def truth(eid='synthetic_1', confirmed=True, frame=50):
    return dict(event_id=eid,confirmed=confirmed,sequence='MOT20-01',line_id='synthetic_gate',
        track_id=7,gt_frame_1based=frame,direction='IN',
        attributes=dict(mean_visibility=.1,visibility_bin='low'),
        frozen_transition=dict(source_zone='tunnel',target_zone='plaza'))


def gate_audit():
    truths=[dict(id='synthetic_1',frame=50,gid=7,direction='IN',position=[40,60],h=20,bin='low'),
            dict(id='synthetic_2',frame=52,gid=8,direction='IN',position=[42,60],h=20,bin='high')]
    pred=dict(source_frame=50,track_id=100,prediction_id='r000001',fragment_index=0,
        direction='IN',crossing_position_native_px=[40,60],_identity=dict(status='known',gid=7))
    _,_,_,audit=e1.event_matching([pred],truths,matching.solve,matching.can_match_right_optimally)
    return dict(gate='synthetic_gate',**audit)


class EvidenceTests(unittest.TestCase):
    def fixture(self):
        a=truth();b=truth('synthetic_2',frame=52);b['track_id']=8
        b['attributes']=dict(mean_visibility=.9,visibility_bin='high')
        return [a,b], {'MOT20-01':[gate_audit()]}

    def test_frozen_identity_matching_not_anonymous_nearness(self):
        labels,audits=self.fixture();rows=canonical_rows(labels,audits)
        self.assertEqual([r['found'] for r in rows],[True,False])
        self.assertEqual(rows[0]['system_event']['track_id'],100)

    def test_unconfirmed_not_a_miss(self):
        labels,audits=self.fixture();labels.append(truth('synthetic_u',False))
        self.assertEqual(len(canonical_rows(labels,audits)),2)

    def test_incomplete_membership_rejected(self):
        labels,audits=self.fixture();audits['MOT20-01'][0]['gt_membership_checks'].pop()
        with self.assertRaises(ValueError):canonical_rows(labels,audits)

    def test_pair_membership_disagreement_rejected(self):
        labels,audits=self.fixture();audits['MOT20-01'][0]['gt_membership_checks'][0]['canonical_matched']=False
        with self.assertRaises(ValueError):canonical_rows(labels,audits)

    def test_wrong_gt_key_rejected(self):
        labels,audits=self.fixture();labels[0]['gt_frame_1based']=51
        with self.assertRaises(ValueError):canonical_rows(labels,audits)

    def test_prediction_cannot_be_used_twice(self):
        labels,audits=self.fixture();a=audits['MOT20-01'][0]
        pk=a['solution']['pairs'][0][0]
        a['solution']['pairs'].append([pk,a['gt_membership_checks'][1]['gt_key']])
        a['solution']['cardinality']=2
        with self.assertRaises(ValueError):canonical_rows(labels,audits)

    def test_empty_predictions_preserve_all_misses(self):
        labels,audits=self.fixture();a=audits['MOT20-01'][0]
        a['predictions']=[];a['solution'].update(pairs=[],cardinality=0)
        for m in a['gt_membership_checks']:m.update(canonical_matched=False,can_be_matched=False,can_be_unmatched=True)
        self.assertFalse(any(r['found'] for r in canonical_rows(labels,audits)))

    def test_list_visibility_filter_after_global_match(self):
        labels,audits=self.fixture();i=Inspector.__new__(Inspector)
        i.statuses={r['event_id']:r for r in canonical_rows(labels,audits)}
        self.assertEqual(i.list_events('low'),[])
        self.assertEqual(i.list_events('high')[0]['event_id'],'synthetic_2')
        self.assertEqual(len(i.list_events('all',False)),2)

    def test_visibility_boundaries_and_missing(self):
        self.assertEqual([visibility_bin(v) for v in (0,.249,.25,.5,.75,1,None)],
                         ['low','low','mid_low','mid_high','high','high',None])
        for v in (-1,float('nan'),1.1):
            with self.assertRaises(ValueError):visibility_bin(v)

    def test_identity_valid_spatial_vs_temporal_sides(self):
        polys={'tunnel':[[10,10],[90,10],[90,40],[10,40]],
               'plaza':[[10,60],[90,60],[90,90],[10,90]]}
        def o(f,box,status='valid',gid=7):
            return dict(source_frame=f,track_id=100,box=box,status=status,gt_id=gid)
        obs=[o(25,[20,20,30,30]),o(75,[20,60,30,70]), # inclusive temporal endpoints
             o(24,[20,60,30,70]),o(76,[20,20,30,30]), # excluded
             o(50,[20,20,30,30],'ambiguous'),o(50,[20,60,30,70],gid=9),
             o(49,[20,40,30,50]),o(51,[0,20,30,30])]
        r=valid_support(obs,truth(),polys,100,100)
        self.assertEqual(r['spatial_regions']['tunnel']['source_frames_1based'],[25])
        self.assertEqual(r['spatial_regions']['plaza']['source_frames_1based'],[75])
        self.assertEqual(r['spatial_regions']['gap']['source_frames_1based'],[49])
        self.assertEqual(r['spatial_regions']['invalid_point']['source_frames_1based'],[51])
        self.assertEqual(r['missing_spatial_sides'],[])
        self.assertEqual(r['temporal_before']['source_frames_1based'],[25,49])

    def test_no_identity_valid_output_reports_both_sides(self):
        polys={'tunnel':[[10,10],[90,10],[90,40],[10,40]],'plaza':[[10,60],[90,60],[90,90],[10,90]]}
        r=valid_support([],truth(),polys,100,100)
        self.assertEqual(r['missing_spatial_sides'],['source','target'])

    def test_invalid_point_not_a_gap_observation(self):
        self.assertEqual(region_of(None,{}),'invalid_point')

    def test_duplicate_label_rejected(self):
        labels,audits=self.fixture();labels.append(copy.deepcopy(labels[0]))
        with self.assertRaises(ValueError):canonical_rows(labels,audits)


if __name__=='__main__':unittest.main(verbosity=2)
