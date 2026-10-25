"""Independent #109 I2/I3 integration fixtures; entirely invented inputs.

No project labels, real GT, tracks, images, answers, scientific workers, GPU,
network or dependency installer are used. The source package imports have no
I/O. All temporary files are under a checked new project scratch directory.
"""
from __future__ import annotations

from contextlib import ExitStack, redirect_stderr, redirect_stdout
import copy
import gzip
import hashlib
import io
import json
from pathlib import Path
import shutil
import sys
import tempfile
import time
from types import ModuleType
import unittest
from unittest.mock import Mock, patch
from scratch_support import scratch_parent

PACKAGE = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(PACKAGE))

import inspect_event as cli
import inspect_saved_event as saved_cli
from src import inspection
from src import evidence_seal
from src.audit_integrity import FrameIdentityIntegrityError
from src.evidence_seal import MANIFEST_NAME, seal_score_evidence


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def dump_json(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, sort_keys=True, allow_nan=False) + '\n',
                    encoding='utf-8')


def dump_gz(path, rows):
    raw = b''.join((json.dumps(row, sort_keys=True, allow_nan=False) + '\n').encode('utf-8')
                   for row in rows)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(raw, mtime=0))


class InventedFixture:
    """Three-frame sequences with a found event and a missed event.

    The frozen score itself is not invoked: the fixture supplies its serialized
    audit contract. MOT20-02 genuinely has an empty tracker frame 2, represented
    explicitly in the per-frame audit. Mutating that audit is distinguishable
    from mutating the tracks or changing the seal.
    """
    SEQS = ('MOT20-01', 'MOT20-02')

    def __init__(self, root):
        self.root = root
        self.package = root / 'invented_package'
        self.score = root / 'invented_score'
        self.gt_files, self.track_files, self.gt_rows, self.gt_raw = {}, {}, {}, {}
        self.identity_rows, self.audits = {}, {}
        self.summary = dict(sequences={})
        self.transitions, geometry = [], []
        polygons = {
            'tunnel': [[10, 10], [90, 10], [90, 40], [10, 40]],
            'plaza': [[10, 60], [90, 60], [90, 90], [10, 90]],
        }
        for i, seq in enumerate(self.SEQS):
            gid, tid = 7 + i, 100 + i
            eid = 'synthetic_' + seq
            meta = dict(seqLength=3, width=100, height=100, fps=25)
            self.summary['sequences'][seq] = dict(metadata=meta)
            label = dict(event_id=eid, confirmed=True, sequence=seq,
                line_id='synthetic_gate', track_id=gid, gt_frame_1based=3,
                direction='IN', position_native_px=[25, 70],
                attributes=dict(mean_visibility=0.1, visibility_bin='low'),
                confirmation=dict(synthetic=True),
                audit=dict(source_gt_asset='synthetic:' + seq,
                           event_time_semantics='synthetic_target_entry', human_qc='not_reviewed'),
                frozen_transition=dict(source_zone='tunnel', target_zone='plaza',
                    endpoints=[dict(gt_frame_1based=1, point=[25, 30]),
                               dict(gt_frame_1based=3, point=[25, 70])]))
            self.transitions.append(label)
            geometry.append(dict(sequence=seq, line_id='synthetic_gate', polygons=copy.deepcopy(polygons),
                                 orientation='H', line_coordinate_px=50, line_extent_px=[10, 90]))
            rows, gt_lines, track_lines, frame_audit = [], [], [], []
            for frame in (1, 2, 3):
                top = 20 * frame
                box = [20.0, float(top), 30.0, float(top + 10)]
                rows.append(inspection.census.Row(frame, gid, *box, 10, 10, 1, 1, 0.1, frame))
                gt_lines.append(f'{frame},{gid},21,{top + 1},10,10,1,1,0.1\n')
                has_output = not (seq == 'MOT20-02' and frame == 2)
                observations = []
                if has_output:
                    track_lines.append(f'{frame},{tid},21,{top + 1},10,10,0.9,-1,-1,-1\n')
                    observations.append(dict(source_frame=frame, track_id=tid, output_row_index=0,
                        gt_id=gid, gt_class=1, gt_line=frame, status='valid', box=box,
                        assigned_iou=1.0, margin=1.0))
                assignment = dict(pairs=[[0, gid]] if has_output else [],
                    cardinality=int(has_output), exact_cost='-1' if has_output else '0',
                    iou_edges=[], containment_edges=[], residual_containment=[])
                frame_audit.append(dict(source_frame=frame, observations=observations,
                                        output_assignment=assignment))
            self.gt_rows[seq] = rows
            self.gt_raw[seq] = ''.join(gt_lines).encode('utf-8')
            self.gt_files[seq] = root / 'invented_inputs' / seq / 'gt.txt'
            self.gt_files[seq].parent.mkdir(parents=True, exist_ok=True)
            self.gt_files[seq].write_bytes(self.gt_raw[seq])
            self.track_files[seq] = root / 'invented_tracks' / (seq + '.txt')
            self.track_files[seq].parent.mkdir(parents=True, exist_ok=True)
            self.track_files[seq].write_text(''.join(track_lines), encoding='utf-8')
            self.identity_rows[seq] = frame_audit
            found = seq == 'MOT20-01'
            pk, gk = [3, tid, 'IN', 0], [3, gid, 'IN', eid]
            prediction = dict(matching_key=pk, prediction_id='synthetic_prediction_' + seq,
                source_frame=3, track_id=tid, position_native_px=[25, 70], direction='IN',
                identity_status='known' if found else 'unknown')
            self.audits[seq] = [dict(gate='synthetic_gate', predictions=[prediction],
                solution=dict(pairs=[[pk, gk]] if found else [], cardinality=int(found)),
                gt_membership_checks=[dict(gt_event_id=eid, gt_key=gk,
                    canonical_matched=found, membership_tie=False,
                    can_be_matched=found, can_be_unmatched=not found)],
                anonymous_legal_edges=[dict(gt_event_id=eid, prediction_id=prediction['prediction_id'])])]
        dump_json(self.package / 'labels/summary.json', self.summary)
        dump_json(self.package / 'labels/geometry.json', dict(lines=geometry))
        dump_gz(self.package / 'labels/transitions.jsonl.gz', self.transitions)
        dump_json(self.package / 'MANIFEST.json', dict(synthetic=True, version='fixture-v1'))
        self.package_manifest_sha256 = sha((self.package / 'MANIFEST.json').read_bytes())
        self.code_path = self.package / 'src/synthetic_bound.py'
        self.code_path.parent.mkdir(parents=True, exist_ok=True)
        self.code_path.write_bytes(b'fixture_only = True\n')
        self.bindings = [self.binding('code:synthetic_bound.py', self.code_path)]
        for seq in self.SEQS:
            self.bindings += [self.binding('gt:' + seq, self.gt_files[seq]),
                              self.binding('tracks:' + seq, self.track_files[seq])]
        self.write_score(self.score)
        self.seal = seal_score_evidence(self.score, self.package_manifest_sha256)

    @staticmethod
    def binding(alias, path):
        raw = path.read_bytes()
        return dict(path=alias, bytes=len(raw), sha256=sha(raw))

    def write_score(self, out):
        out.mkdir(parents=True, exist_ok=False)
        dump_json(out / 'complete.json', dict(status='COMPLETE', fixture='no_scientific_worker'))
        dump_json(out / 'read_ledger.json', self.bindings)
        for seq in self.SEQS:
            dump_json(out / (seq + '_event_matching.json'), self.audits[seq])
            dump_gz(out / (seq + '_frame_identity.jsonl.gz'), self.identity_rows[seq])

    def reseal_modified_frame_audit(self, seq):
        # Only this fixture's initially-created seal is removed. This operation
        # intentionally makes malformed content honestly hash-bound, so the
        # integrity validator (not just a digest mismatch) has to reject it.
        dump_gz(self.score / (seq + '_frame_identity.jsonl.gz'), self.identity_rows[seq])
        (self.score / MANIFEST_NAME).unlink()
        self.seal = seal_score_evidence(self.score, self.package_manifest_sha256)

    def patches(self, stack):
        expected = {seq: dict(gt=sha(raw)) for seq, raw in self.gt_raw.items()}
        stack.enter_context(patch.object(inspection.census, 'EXPECTED_INPUTS', expected))

        def fake_parse_gt(raw, metadata):
            self.assert_synthetic_raw(raw)
            seq = next(s for s in self.SEQS if raw == self.gt_raw[s])
            return copy.deepcopy(self.gt_rows[seq]), [], {}

        stack.enter_context(patch.object(inspection.census, 'parse_gt', side_effect=fake_parse_gt))

    def assert_synthetic_raw(self, raw):
        if raw not in self.gt_raw.values():
            raise AssertionError('Fixture parser received anything other than invented GT bytes')

    def inspector(self, ledger):
        return inspection.Inspector(self.package, self.gt_files, self.track_files, self.score,
            read_ledger=ledger, evidence_manifest_sha256=self.seal['sha256'])


class InspectorIntegrationRound2(unittest.TestCase):
    def setUp(self):
        self.assertEqual(Path(inspection.__file__).resolve().parents[1], PACKAGE)
        scratch = scratch_parent()
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic_', dir=scratch)
        self.root = Path(self.temp.name).resolve()
        self.assertEqual(self.root.parent, scratch)
        self.addCleanup(self.temp.cleanup)
        self.fx = InventedFixture(self.root)
        self.stack = ExitStack()
        self.addCleanup(self.stack.close)
        self.fx.patches(self.stack)

    def test_full_constructor_list_and_detail_from_synthetic_files(self):
        reads = []
        inspector = self.fx.inspector(reads)
        self.assertIs(inspector.reads, reads)
        self.assertEqual(len(inspector.list_events('all', False)), 2)
        self.assertEqual([r['event_id'] for r in inspector.list_events('low')],
                         ['synthetic_MOT20-02'])
        detail = inspector.detail('synthetic_MOT20-01')
        self.assertTrue(detail['system_evidence']['found'])
        self.assertEqual(detail['system_evidence']['absolute_time_difference_s'], 0)
        self.assertEqual(detail['system_evidence']['position_distance_px'], 0)
        self.assertEqual(detail['system_evidence']['identity_valid_output_support']['missing_spatial_sides'], [])
        self.assertEqual(len(detail['visibility_window']), 3)
        self.assertEqual(inspector.frame_integrity['MOT20-01']['frame_count'], 3)
        self.assertEqual(inspector.frame_integrity['MOT20-02']['empty_frames'], 1)
        self.assertTrue(all(r.get('read_status') == 'READ' for r in reads))
        self.assertTrue(any(r['asset'] == 'score:evidence_seal' for r in reads))

    def test_honestly_sealed_missing_frame_is_not_interpreted_as_zero_support(self):
        self.fx.identity_rows['MOT20-01'].pop(1)
        self.fx.reseal_modified_frame_audit('MOT20-01')
        reads = []
        with self.assertRaises(FrameIdentityIntegrityError):
            self.fx.inspector(reads)
        row = next(r for r in reads if r['asset'] == 'score:MOT20-01:frame_identity')
        self.assertEqual(row['binding_status'], 'MATCH')

    def test_honestly_sealed_observation_box_disagreement_is_rejected(self):
        self.fx.identity_rows['MOT20-01'][1]['observations'][0]['box'][0] += 0.5
        self.fx.reseal_modified_frame_audit('MOT20-01')
        reads = []
        with self.assertRaises(FrameIdentityIntegrityError):
            self.fx.inspector(reads)
        row = next(r for r in reads if r['asset'] == 'score:MOT20-01:frame_identity')
        self.assertEqual(row['binding_status'], 'MATCH')

    def test_post_seal_audit_change_records_actual_digest_before_constructor_fails(self):
        path = self.fx.score / 'MOT20-01_frame_identity.jsonl.gz'
        old = path.read_bytes()
        self.fx.identity_rows['MOT20-01'].pop()
        dump_gz(path, self.fx.identity_rows['MOT20-01'])
        actual = path.read_bytes()
        reads = []
        with self.assertRaisesRegex(ValueError, 'Bound input changed'):
            self.fx.inspector(reads)
        row = next(r for r in reads if r['asset'] == 'score:MOT20-01:frame_identity')
        self.assertEqual(row['binding_status'], 'MISMATCH')
        self.assertEqual(row['sha256'], sha(actual))
        self.assertEqual(row['bytes'], len(actual))
        self.assertEqual(row['expected_sha256'], sha(old))

    def test_different_package_manifest_cannot_consume_prior_seal(self):
        path = self.fx.package / 'MANIFEST.json'
        dump_json(path, dict(synthetic=True, version='a_different_package'))
        reads = []
        with self.assertRaises(ValueError):
            self.fx.inspector(reads)
        self.assertTrue(any(row.get('sha256') == sha(path.read_bytes()) for row in reads),
                        'The rejected package manifest must itself remain auditable')

    def test_changed_tracker_input_preserves_shared_constructor_ledger(self):
        path = self.fx.track_files['MOT20-01']
        old = path.read_bytes()
        path.write_bytes(old.replace(b'0.9', b'0.8', 1))
        reads = []
        with self.assertRaisesRegex(ValueError, 'Bound input changed'):
            self.fx.inspector(reads)
        row = next(r for r in reads if r['asset'] == 'tracks:MOT20-01')
        self.assertEqual(row['binding_status'], 'MISMATCH')
        self.assertEqual(row['sha256'], sha(path.read_bytes()))
        self.assertEqual(row['expected_sha256'], sha(old))
        self.assertGreater(len(reads), 3)

    def test_fixed_gt_source_hash_failure_is_marked_as_binding_failure(self):
        path = self.fx.gt_files['MOT20-01']
        old = path.read_bytes()
        path.write_bytes(old + b'\n')
        reads = []
        with self.assertRaises(ValueError):
            self.fx.inspector(reads)
        rows = [r for r in reads if r['asset'] == 'gt:MOT20-01']
        self.assertTrue(rows)
        self.assertEqual(rows[-1]['binding_status'], 'MISMATCH')
        self.assertEqual(rows[-1]['sha256'], sha(path.read_bytes()))
        self.assertEqual(rows[-1]['expected_sha256'], sha(old))

    def test_missing_gt_file_records_read_error(self):
        self.fx.gt_files['MOT20-01'].unlink()
        reads = []
        with self.assertRaises(FileNotFoundError):
            self.fx.inspector(reads)
        row = next(r for r in reads if r['asset'] == 'gt:MOT20-01')
        self.assertEqual(row['read_status'], 'READ_ERROR')
        self.assertIn('error', row)

    def cli_patches(self, stack, render_callback):
        # Fabricated worker modules make it impossible for these tests to enter
        # the real label derivation or scientific scoring workers.
        fake_labels, fake_lineage, fake_score = (ModuleType(n) for n in
            ('src.labels', 'src.lineage', 'src.tracker_score'))
        fake_labels.build_labels = Mock(side_effect=lambda gt, seq, out:
            shutil.copytree(self.fx.package / 'labels', out))
        fake_lineage.enrich_labels = Mock(return_value={'synthetic': True})
        fake_score.score_tracks = Mock(side_effect=lambda gt, labels, tracks, out, package, name:
            self.fx.write_score(out))
        stack.enter_context(patch.dict(sys.modules, {
            'src.labels': fake_labels, 'src.lineage': fake_lineage, 'src.tracker_score': fake_score}))
        stack.enter_context(patch.object(cli, '__file__', str(self.fx.package / 'inspect_event.py')))
        stack.enter_context(patch.object(cli, 'verify_package',
            return_value=({}, self.fx.package_manifest_sha256)))
        stack.enter_context(patch.object(cli, 'input_paths', side_effect=lambda root, kind:
            self.fx.gt_files if kind == 'gt' else {seq: self.root / (seq + '.ini') for seq in self.fx.SEQS}))
        stack.enter_context(patch.object(cli, 'track_paths', return_value=self.fx.track_files))
        stack.enter_context(patch.object(cli, 'verify_rebuilt_labels', return_value={'status': 'SYNTHETIC'}))
        stack.enter_context(patch.object(cli, 'render_event', side_effect=render_callback))
        stack.enter_context(redirect_stdout(io.StringIO()))
        stack.enter_context(redirect_stderr(io.StringIO()))
        return fake_labels, fake_lineage, fake_score

    def cli_args(self, out):
        return ['--gt-root', str(self.root / 'unused_gt_root'), '--tracks', str(self.root / 'unused_tracks'),
                '--event-id', 'synthetic_MOT20-01', '--out', str(out),
                '--images', str(self.root / 'invented_images/MOT20-01/img1'),
                '--render-out', str(self.root / 'invented_render_out')]

    def test_cli_render_exception_preserves_ledger_and_failed_without_complete(self):
        out = self.root / 'cli_render_failure'
        marker = self.root / 'invented_render_bytes.bin'
        marker.write_bytes(b'not_a_real_image:fixture_only')
        error = RuntimeError('synthetic renderer failure after a recorded read')

        def render(inspector, detail, images, target):
            inspector.read(marker, 'image:synthetic:3')
            raise error

        with ExitStack() as stack:
            workers = self.cli_patches(stack, render)
            with self.assertRaises(RuntimeError) as caught:
                cli.main(self.cli_args(out))
        self.assertIs(caught.exception, error)
        self.assertTrue((out / 'read_ledger.json').is_file())
        self.assertTrue((out / 'FAILED.json').is_file())
        self.assertFalse((out / 'complete.json').exists())
        ledger = json.loads((out / 'read_ledger.json').read_text(encoding='utf-8'))
        row = next(r for r in ledger if r['asset'] == 'image:synthetic:3')
        self.assertEqual(row['sha256'], sha(marker.read_bytes()))
        failed = json.loads((out / 'FAILED.json').read_text(encoding='utf-8'))
        self.assertEqual(failed['error'], repr(error))
        self.assertEqual(failed['reads'], ledger)
        self.assertEqual(workers[0].build_labels.call_count, 1)
        self.assertEqual(workers[1].enrich_labels.call_count, 1)
        self.assertEqual(workers[2].score_tracks.call_count, 1)

    def test_cli_constructor_binding_failure_keeps_evidence_without_success_marker(self):
        self.fx.code_path.write_bytes(b'fixture_only = False\n')
        out = self.root / 'cli_constructor_failure'
        with ExitStack() as stack:
            self.cli_patches(stack, Mock(side_effect=AssertionError('renderer must not run')))
            with self.assertRaisesRegex(ValueError, 'Bound input changed'):
                cli.main(self.cli_args(out))
        ledger = json.loads((out / 'read_ledger.json').read_text(encoding='utf-8'))
        row = next(r for r in ledger if r['asset'] == 'code:synthetic_bound.py')
        self.assertEqual(row['binding_status'], 'MISMATCH')
        self.assertEqual(row['sha256'], sha(self.fx.code_path.read_bytes()))
        self.assertTrue((out / 'FAILED.json').is_file())
        self.assertFalse((out / 'complete.json').exists())

    def test_cli_secondary_logging_failure_does_not_replace_render_error(self):
        out = self.root / 'cli_secondary_logging_failure'
        error = RuntimeError('primary synthetic render error')
        original_save = cli.save

        def failing_log(path, payload):
            if Path(path).name in ('read_ledger.json', 'FAILED.json'):
                raise OSError('synthetic disk-full logging failure')
            return original_save(path, payload)

        with ExitStack() as stack:
            self.cli_patches(stack, Mock(side_effect=error))
            stack.enter_context(patch.object(cli, 'save', side_effect=failing_log))
            with self.assertRaises(RuntimeError) as caught:
                cli.main(self.cli_args(out))
        self.assertIs(caught.exception, error)
        self.assertFalse((out / 'complete.json').exists())

    def cached_cli_patches(self, stack):
        # These are tripwires, not replacements that return a successful score.
        # The cached command must use the real Inspector and existing seal only.
        guards = []
        modules = {}
        for module_name, function_name in (
                ('src.labels', 'build_labels'), ('src.lineage', 'enrich_labels'),
                ('src.tracker_score', 'score_tracks')):
            module = ModuleType(module_name)
            guard = Mock(side_effect=AssertionError('Cached inspection entered ' + function_name))
            setattr(module, function_name, guard)
            modules[module_name] = module
            guards.append(guard)
        stack.enter_context(patch.dict(sys.modules, modules))
        seal_guard = Mock(side_effect=AssertionError('Cached inspection tried to create a new seal'))
        stack.enter_context(patch.object(evidence_seal, 'seal_score_evidence', seal_guard))
        stack.enter_context(patch.object(cli, 'seal_score_evidence', seal_guard))
        guards.append(seal_guard)
        stack.enter_context(patch.object(saved_cli, '__file__',
                                        str(self.fx.package / 'inspect_saved_event.py')))
        stack.enter_context(patch.object(saved_cli, 'verify_package',
                                        return_value=({}, self.fx.package_manifest_sha256)))
        stack.enter_context(patch.object(saved_cli, 'input_paths', return_value=self.fx.gt_files))
        stack.enter_context(patch.object(saved_cli, 'track_paths', return_value=self.fx.track_files))
        inspector = stack.enter_context(patch.object(saved_cli, 'Inspector',
                                                     wraps=inspection.Inspector))
        stack.enter_context(redirect_stdout(io.StringIO()))
        stack.enter_context(redirect_stderr(io.StringIO()))
        return guards, inspector

    def cached_cli_args(self, out, mode, digest=None):
        return ['--gt-root', str(self.root / 'unused_gt_root'),
                '--tracks', str(self.root / 'unused_tracks'),
                '--score-dir', str(self.fx.score),
                '--evidence-sha256', digest or self.fx.seal['sha256'],
                '--out', str(out)] + mode

    def score_bytes(self):
        return {p.relative_to(self.fx.score).as_posix(): p.read_bytes()
                for p in self.fx.score.rglob('*') if p.is_file()}

    def assert_cached_guards(self, guards, inspector, before):
        for guard in guards:
            guard.assert_not_called()
        inspector.assert_called_once()
        self.assertEqual(self.score_bytes(), before,
                         'Cached inspection must not add, remove, or change any original score member')

    def test_cached_cli_list_uses_real_inspector_without_scoring_or_resealing(self):
        before = self.score_bytes()
        out = self.root / 'cached_list'
        with ExitStack() as stack:
            guards, inspector = self.cached_cli_patches(stack)
            self.assertEqual(saved_cli.main(self.cached_cli_args(out,
                ['--list-misses', '--bin', 'low'])), 0)
            self.assert_cached_guards(guards, inspector, before)
        rows = [json.loads(line) for line in (out / 'misses.jsonl').read_text(encoding='utf-8').splitlines()]
        self.assertEqual([row['event_id'] for row in rows], ['synthetic_MOT20-02'])
        receipt = json.loads((out / 'inspection_receipt.json').read_text(encoding='utf-8'))
        self.assertTrue(receipt['no_rescoring'])
        self.assertFalse(receipt['scientific_result_created'])
        self.assertEqual(receipt['frame_integrity']['MOT20-02']['empty_frames'], 1)
        self.assertFalse((out / 'complete.json').exists())
        self.assertFalse((out / 'FAILED.json').exists())

    def test_cached_cli_event_uses_real_inspector_without_scoring_or_resealing(self):
        before = self.score_bytes()
        out = self.root / 'cached_event'
        with ExitStack() as stack:
            guards, inspector = self.cached_cli_patches(stack)
            self.assertEqual(saved_cli.main(self.cached_cli_args(out,
                ['--event-id', 'synthetic_MOT20-01'])), 0)
            self.assert_cached_guards(guards, inspector, before)
        detail = json.loads((out / 'event.json').read_text(encoding='utf-8'))
        self.assertTrue(detail['system_evidence']['found'])
        self.assertEqual(detail['system_evidence']['absolute_time_difference_s'], 0)
        self.assertEqual(detail['system_evidence']['identity_valid_output_support']['missing_spatial_sides'], [])
        ledger = json.loads((out / 'read_ledger.json').read_text(encoding='utf-8'))
        self.assertTrue(any(row['asset'] == 'score:evidence_seal' and
                            row['binding_status'] == 'MATCH' for row in ledger))
        self.assertTrue((out / 'inspection_receipt.json').exists())
        self.assertFalse((out / 'complete.json').exists())

    def test_cached_cli_wrong_external_sha_rejects_and_preserves_source_bytes(self):
        before = self.score_bytes()
        out = self.root / 'cached_bad_external_sha'
        with ExitStack() as stack:
            guards, inspector = self.cached_cli_patches(stack)
            with self.assertRaisesRegex(ValueError, 'Bound input changed'):
                saved_cli.main(self.cached_cli_args(out, ['--list-misses'], '0' * 64))
            self.assert_cached_guards(guards, inspector, before)
        ledger = json.loads((out / 'read_ledger.json').read_text(encoding='utf-8'))
        row = next(row for row in ledger if row['asset'] == 'score:evidence_seal')
        self.assertEqual(row['sha256'], self.fx.seal['sha256'])
        self.assertEqual(row['expected_sha256'], '0' * 64)
        self.assertEqual(row['binding_status'], 'MISMATCH')
        self.assertTrue((out / 'FAILED.json').exists())
        self.assertFalse((out / 'inspection_receipt.json').exists())
        self.assertFalse((out / 'complete.json').exists())


if __name__ == '__main__':
    unittest.main(verbosity=2)
