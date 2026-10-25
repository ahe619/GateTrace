"""Saved-inspection CLI tests with synthetic files and mocked read-only Inspector.

No real scoring, raw GT, trajectories, images, labels or human answers are opened.
Scientific worker imports and accidental seal creation are made fatal in tests.
"""
import builtins
import contextlib
import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from scratch_support import scratch_parent

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import inspect_saved_event as cli


SHA = 'a' * 64
PACKAGE_SHA = 'b' * 64


class FakeInspector:
    def __init__(self, package, gt, tracks, score_dir, read_ledger, evidence_manifest_sha256):
        if evidence_manifest_sha256 != SHA:
            raise ValueError('synthetic external seal mismatch')
        self.frame_integrity = {'synthetic': {'frame_count': 3, 'observation_count': 1, 'empty_frames': 2}}
        read_ledger.append({'alias': 'synthetic_bound_evidence', 'sha256': SHA})

    def detail(self, event_id):
        return dict(event_id=event_id, confirmation_status=True,
                    system_evidence=dict(found=False), human_qc='not_reviewed')

    def list_events(self, bin_name):
        return [dict(event_id='synthetic_event', bin=bin_name, found=False)]


class SavedInspectionCLITests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic_saved_cli_',dir=scratch_parent())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.score = self.root / 'existing_score'
        self.score.mkdir()
        # This is deliberately not an executable or valid scientific score.
        # It provides immutable sentinels to show that the CLI never replaces it.
        (self.score / 'complete.json').write_text('{"sentinel":"existing_complete"}', encoding='utf-8')
        (self.score / 'read_ledger.json').write_text('[{"sentinel":"existing_reads"}]', encoding='utf-8')
        (self.score / 'inspection_evidence_manifest.json').write_text('{"sha256":"untrusted"}', encoding='utf-8')
        self.original = {p.name: p.read_bytes() for p in self.score.iterdir()}
        self.gt, self.tracks = self.root / 'synthetic_gt', self.root / 'synthetic_tracks'
        self.out = self.root / 'new_inspection'
        self.args = ['--gt-root', str(self.gt), '--tracks', str(self.tracks),
                     '--score-dir', str(self.score), '--evidence-sha256', SHA, '--out', str(self.out)]
        self.gt_map = {'MOT20-01': 'synthetic_gt_01', 'MOT20-02': 'synthetic_gt_02'}
        self.track_map = {'MOT20-01': 'synthetic_track_01', 'MOT20-02': 'synthetic_track_02'}

    @contextlib.contextmanager
    def safe_runtime(self, inspector=FakeInspector):
        original_import = builtins.__import__
        forbidden_names = {'src.labels', 'src.tracker_score', 'src.lineage'}
        def guarded_import(name, globals=None, locals=None, fromlist=(), level=0):
            if name in forbidden_names or any(n in ('build_labels', 'score_tracks', 'enrich_labels') for n in fromlist or ()):
                raise AssertionError('Scientific worker import is forbidden in saved-inspection CLI: ' + name)
            return original_import(name, globals, locals, fromlist, level)
        with contextlib.ExitStack() as stack:
            verify = stack.enter_context(patch.object(cli, 'verify_package', return_value=({}, PACKAGE_SHA)))
            inputs = stack.enter_context(patch.object(cli, 'input_paths', return_value=self.gt_map))
            tracks = stack.enter_context(patch.object(cli, 'track_paths', return_value=self.track_map))
            factory = stack.enter_context(patch.object(cli, 'Inspector', side_effect=inspector))
            render = stack.enter_context(patch.object(cli, 'render_event', return_value=[]))
            # seal_score_evidence is imported by the fresh CLI solely to obtain
            # preserve_failure. It must never be called by this saved-only path.
            seal = stack.enter_context(patch('inspect_event.seal_score_evidence', side_effect=AssertionError('resealing forbidden')))
            stack.enter_context(patch('builtins.__import__', side_effect=guarded_import))
            stack.enter_context(contextlib.redirect_stdout(io.StringIO()))
            yield dict(verify=verify, inputs=inputs, tracks=tracks, factory=factory, render=render, seal=seal)

    def assert_score_untouched(self):
        self.assertEqual({p.name: p.read_bytes() for p in self.score.iterdir()}, self.original)

    def test_event_mode_passes_only_explicit_external_digest_and_does_not_rescore(self):
        with self.safe_runtime() as mocks:
            self.assertEqual(cli.main(self.args + ['--event-id', 'synthetic_event']), 0)
            kwargs = mocks['factory'].call_args.kwargs
            self.assertEqual(kwargs['evidence_manifest_sha256'], SHA)
            self.assertEqual(mocks['factory'].call_args.args[1:4], (self.gt_map, self.track_map, self.score.resolve()))
            mocks['seal'].assert_not_called()
        receipt = json.loads((self.out / 'inspection_receipt.json').read_text())
        self.assertTrue(receipt['no_rescoring'])
        self.assertFalse(receipt['scientific_result_created'])
        self.assertEqual(receipt['status'], 'INSPECTION_COMPLETE_PENDING_QC')
        self.assertFalse((self.out / 'complete.json').exists())
        self.assertFalse((self.out / 'labels').exists())
        self.assertFalse((self.out / 'tracker').exists())
        self.assertEqual(json.loads((self.out / 'read_ledger.json').read_text())[0]['sha256'], SHA)
        self.assert_score_untouched()

    def test_list_mode_passes_bin_and_writes_no_new_score(self):
        with self.safe_runtime() as mocks:
            cli.main(self.args + ['--list-misses', '--bin', 'low'])
            mocks['seal'].assert_not_called()
        rows = [json.loads(line) for line in (self.out / 'misses.jsonl').read_text().splitlines()]
        self.assertEqual(rows, [{'event_id': 'synthetic_event', 'bin': 'low', 'found': False}])
        receipt = json.loads((self.out / 'inspection_receipt.json').read_text())
        self.assertEqual(receipt['selection']['inspected_event_count'], 1)
        self.assert_score_untouched()

    def test_wrong_retained_digest_preserves_failure_without_touching_score(self):
        args = [str('c' * 64) if item == SHA else item for item in self.args]
        with self.safe_runtime():
            with self.assertRaisesRegex(ValueError, 'external seal mismatch'):
                cli.main(args + ['--event-id', 'synthetic_event'])
        self.assertTrue((self.out / 'FAILED.json').is_file())
        self.assertFalse((self.out / 'inspection_receipt.json').exists())
        self.assert_score_untouched()

    def test_missing_digest_is_not_taken_from_local_manifest(self):
        args = copy.copy(self.args)
        position = args.index('--evidence-sha256')
        del args[position:position + 2]
        with self.safe_runtime() as mocks, contextlib.redirect_stderr(io.StringIO()):
            with self.assertRaises(SystemExit):
                cli.main(args + ['--event-id', 'synthetic_event'])
            mocks['factory'].assert_not_called()
        self.assertFalse(self.out.exists())
        self.assert_score_untouched()

    def test_malformed_digest_rejected_before_reads(self):
        for value in ('a' * 63, 'G' * 64, 'A' * 64, '../manifest.json'):
            args = [value if item == SHA else item for item in self.args]
            with self.subTest(value=value), self.safe_runtime() as mocks, contextlib.redirect_stderr(io.StringIO()):
                with self.assertRaises(SystemExit):
                    cli.main(args + ['--event-id', 'synthetic_event'])
                mocks['verify'].assert_not_called()
        self.assertFalse(self.out.exists())

    def test_old_score_directory_cannot_be_used_as_output(self):
        for target in (self.score, self.score / 'new_output', self.score.parent):
            args = [str(target) if item == str(self.out) else item for item in self.args]
            with self.subTest(target=target), self.safe_runtime():
                with self.assertRaises(ValueError):
                    cli.main(args + ['--event-id', 'synthetic_event'])
        self.assert_score_untouched()

    def test_existing_inspection_directory_refused(self):
        self.out.mkdir()
        marker = self.out / 'keep.txt'
        marker.write_text('do not overwrite')
        with self.safe_runtime(), self.assertRaises(ValueError):
            cli.main(self.args + ['--event-id', 'synthetic_event'])
        self.assertEqual(marker.read_text(), 'do not overwrite')

    def test_optional_render_calls_readonly_renderer_once(self):
        render_out = self.root / 'new_renders'
        with self.safe_runtime() as mocks:
            cli.main(self.args + ['--event-id', 'synthetic_event', '--images', 'synthetic_images',
                                 '--render-out', str(render_out)])
            mocks['render'].assert_called_once()
            self.assertEqual(mocks['render'].call_args.args[2:], ('synthetic_images', render_out.resolve()))
        self.assert_score_untouched()

    def test_render_cannot_write_into_original_score(self):
        with self.safe_runtime(), self.assertRaises(ValueError):
            cli.main(self.args + ['--event-id', 'synthetic_event', '--images', 'synthetic_images',
                                 '--render-out', str(self.score / 'renders')])
        self.assert_score_untouched()

    def test_render_without_event_and_complete_arguments_rejected(self):
        variants = [ ['--event-id', 'synthetic_event', '--images', 'synthetic_images'],
                     ['--event-id', 'synthetic_event', '--render-out', str(self.root / 'renders')],
                     ['--list-misses', '--images', 'synthetic_images', '--render-out', str(self.root / 'renders')] ]
        for variant in variants:
            with self.subTest(variant=variant), self.safe_runtime(), self.assertRaises(ValueError):
                cli.main(self.args + variant)

    def test_partial_inspector_failure_keeps_reads_without_new_result(self):
        def broken(*args, **kwargs):
            kwargs['read_ledger'].append({'alias': 'synthetic_read_before_error'})
            raise RuntimeError('synthetic integrity failure')
        with self.safe_runtime(broken), self.assertRaisesRegex(RuntimeError, 'integrity failure'):
            cli.main(self.args + ['--event-id', 'synthetic_event'])
        self.assertEqual(json.loads((self.out / 'read_ledger.json').read_text()), [{'alias': 'synthetic_read_before_error'}])
        self.assertTrue((self.out / 'FAILED.json').exists())
        self.assertFalse((self.out / 'inspection_receipt.json').exists())
        self.assert_score_untouched()

    def test_entry_point_contains_no_scientific_worker_import_or_call(self):
        import ast
        tree = ast.parse(Path(cli.__file__).read_text(encoding='utf-8'))
        forbidden = {'build_labels', 'score_tracks', 'enrich_labels', 'seal_score_evidence'}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                self.assertTrue(forbidden.isdisjoint(alias.name for alias in node.names))
            if isinstance(node, ast.Call):
                name = node.func.id if isinstance(node.func, ast.Name) else getattr(node.func, 'attr', None)
                self.assertNotIn(name, forbidden)


if __name__ == '__main__':
    unittest.main()
