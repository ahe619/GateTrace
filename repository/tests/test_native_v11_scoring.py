"""Synthetic-only native scoring contract tests. No dataset, cache or GT-file reads."""
import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.score.native_v11 import (GATES, REGRESSION_STATUS, core_api, frame_identity,
    gate_score, output_pool, run, scoped_inputs, validate_native_manifest)
from src.track.native_v11 import output_bindings


class NativeScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = core_api()

    def manifest(self, sequence="MOT20-01"):
        names = {"frames": "frames.jsonl.gz", **{g: "gates/" + g + "/events.json" for g in GATES}}
        return dict(schema="crowd_flow_native_v11_output_v1", sequence=sequence, fps=25,
            frames=5, native_size=[100, 100], source_kind="crowddet", identity_scoring_executed=False,
            event_box_source="raw_detection_box", identity_box_source="post_M4_tracker_rows",
            files={k: dict(path=v, bytes=1, sha256="0" * 64) for k, v in names.items()})

    def frame(self):
        return dict(frame=0, source_frame=1, time_s=0.0,
            detections=[dict(raw_detection_index=7, confidence=.9, track_id=4, original_track_id=4,
                            box=[0., 0., 10., 70.], tracking_eligible=True)],
            tracker_rows=[[0., 0., 10., 80., 4, .9, 0, 7]],
            tracker_frame_metadata=dict(tracker_input_raw_indices=[7]))

    def gate_fixture(self):
        event = dict(prediction_id="p1", sequence="MOT20-01", gate_id="H_30", source_frame=4,
            target_frame=3, time_s=.12, track_id=4, fragment_index=0, direction="tunnel_to_city",
            crossing_position_native_px=[5., 70.])
        doc = dict(sequence="MOT20-01", gate_id="H_30", metadata=dict(nb_frames=5, fps=25), final_events=[event])
        observations = {4: [dict(source_frame=f, gt_id=11, status="valid") for f in range(1, 6)]}
        truth = dict(sequence="MOT20-01", line_id="H_30", gt_frame_1based=4, track_id=11,
            time_s=.12, event_id="01_H_30_p1", direction="tunnel_to_city", position_native_px=[5., 70.],
            confirmed=True, frozen_transition={}, confirmation={},
            attributes=dict(h_g=5., mean_visibility=.9, visibility_bin="high", rho=0., static_occ=0.))
        view = self.api.view.gt_row(truth, "synthetic", 1)
        return doc, observations, [truth], [view]

    def score_fixture(self, doc=None, observations=None):
        original, outputobs, transitions, views = self.gate_fixture()
        return gate_score(doc or original, "MOT20-01", "H_30", 5,
                          outputobs if observations is None else observations, {11: 1}, transitions, views, self.api)

    def test_manifest_scope_paths_and_source_contract(self):
        self.assertEqual(validate_native_manifest(self.manifest(), "MOT20-01")["frames"], 5)
        changes = [("sequence", "MOT20-03"), ("fps", 30), ("frames", True),
                   ("source_kind", "unknown"), ("identity_scoring_executed", True),
                   ("event_box_source", "tracker_box"), ("identity_box_source", "detections")]
        for key, value in changes:
            doc = self.manifest()
            doc[key] = value
            with self.assertRaises(ValueError, msg=key):
                validate_native_manifest(doc, "MOT20-01")
        doc = self.manifest()
        doc["files"]["H_30"]["path"] = "../outside.json"
        with self.assertRaises(ValueError):
            validate_native_manifest(doc, "MOT20-01")
        doc = self.manifest()
        del doc["files"]["V_75"]
        with self.assertRaises(ValueError):
            validate_native_manifest(doc, "MOT20-01")

    def test_emitted_box_pool_uses_tracker_coordinates_and_m4_lineage(self):
        row = self.frame()
        self.assertEqual(output_pool(row, 0, self.api)[0]["box"], [0., 0., 10., 80.])
        self.assertEqual(row["detections"][0]["box"], [0., 0., 10., 70.])
        del row["detections"][0]["original_track_id"]
        with self.assertRaisesRegex(ValueError, "M4 lineage"):
            output_pool(row, 0, self.api)
        row = self.frame()
        row["tracker_rows"][0][4] = 99
        with self.assertRaises(ValueError):
            output_pool(row, 0, self.api)
        with self.assertRaises(ValueError):
            output_pool(self.frame(), 1, self.api)

    def test_original_assignment_on_synthetic_gt(self):
        try:
            import numpy
        except ImportError:
            self.skipTest("NumPy unavailable; run with an existing NumPy environment for this one test")
        gt, classes = self.api.identity.parse_gt("1,11,1,1,10,80,1,1,1\n", 5)
        observations, audit = frame_identity(self.frame(), 0, gt[1], self.api, numpy)
        self.assertEqual(classes, {11: 1})
        self.assertEqual(observations[0]["gt_id"], 11)
        self.assertEqual(observations[0]["assigned_iou"], 1.0)
        self.assertEqual(observations[0]["box"], [0., 0., 10., 80.])
        self.assertEqual(audit["cardinality"], 1)

    def test_native_final_position_is_preserved_and_input_is_immutable(self):
        doc, _, _, _ = self.gate_fixture()
        before = copy.deepcopy(doc)
        unit, ranges, audit = self.score_fixture(doc)
        self.assertEqual(doc, before)
        self.assertEqual(unit["correct"], 1)
        self.assertEqual(unit["bins"]["high"], {"correct": 1, "GT": 1})
        self.assertEqual(audit["predictions"][0]["position_native_px"], [5., 70.])
        self.assertEqual(ranges["ranges"]["identity"]["cardinality"], 1)
        # A tracker-box bottom center would be y=80 and would fail this h=5 gate.
        doc["final_events"][0]["crossing_position_native_px"] = [5., 80.]
        self.assertEqual(self.score_fixture(doc)[0]["correct"], 0)

    def test_unknowns_keep_all_final_precision_denominator(self):
        unit, _, _ = self.score_fixture(observations={4: [dict(source_frame=4, gt_id=None, status="unmatched")]})
        aggregate = self.api.aggregate.aggregate([unit])
        self.assertEqual(aggregate["identity_precision"]["numerator"], 0)
        self.assertEqual(aggregate["identity_precision"]["denominator"], 1)
        self.assertEqual(aggregate["unknown_or_ambiguous"], 1)

    def test_cached_identity_and_event_contract_rejected(self):
        for key in ("_identity", "identity_association"):
            doc, _, _, _ = self.gate_fixture()
            doc["final_events"][0][key] = {"gid": 11}
            with self.assertRaisesRegex(ValueError, "Cached identity"):
                self.score_fixture(doc)
        for key, value in (("time_s", .13), ("target_frame", 4), ("track_id", 99), ("source_frame", True)):
            doc, _, _, _ = self.gate_fixture()
            doc["final_events"][0][key] = value
            with self.assertRaises(ValueError, msg=key):
                self.score_fixture(doc)
        doc, _, _, _ = self.gate_fixture()
        doc["final_events"].append(copy.deepcopy(doc["final_events"][0]))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            self.score_fixture(doc)

    def test_default_cli_does_not_open_named_scientific_assets(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            for seq in ("MOT20-01", "MOT20-02"):
                (root / seq).mkdir()
                (root / seq / "native_manifest.json").write_text(json.dumps(self.manifest(seq)), encoding="utf-8")
            result = subprocess.run([sys.executable, "-I", "-S", "-B", str(ROOT / "scripts/score_native_v11.py"),
                "--native-01", str(root / "MOT20-01"), "--native-02", str(root / "MOT20-02"),
                "--gt-root", str(root / "absent_gt"), "--seqinfo-root", str(root / "absent_seqinfo")],
                capture_output=True, text=True)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout)
            self.assertFalse(report["scientific_assets_opened"])
            self.assertEqual(report["regression_status"], REGRESSION_STATUS)
            self.assertFalse((root / "absent_gt").exists())

    def test_output_bytes_bound_and_scope_rejected_before_any_input_read(self):
        with self.assertRaisesRegex(ValueError, "Exactly"):
            run({"MOT20-03": "does-not-exist"}, {}, {}, "does-not-exist")
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "frames.jsonl.gz").write_bytes(b"synthetic frames, never decompressed")
            for gate in GATES:
                (root / "gates" / gate).mkdir(parents=True)
                (root / "gates" / gate / "events.json").write_bytes(b"{}")
            refs = output_bindings(root)
            self.assertEqual(len(refs), 7)
            self.assertEqual(refs["H_30"]["bytes"], 2)
            self.assertEqual(refs["H_30"]["sha256"], "44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a")

    def test_optimized_python_rejected(self):
        result = subprocess.run([sys.executable, "-I", "-S", "-B", "-O", str(ROOT / "scripts/score_native_v11.py"),
            "--native-01", "absent", "--native-02", "absent", "--gt-root", "absent", "--seqinfo-root", "absent"],
            capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Do not use Python -O", result.stderr)

    def test_development_path_guard_precedes_content_reads(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            files = {}
            for sequence in ("MOT20-01", "MOT20-02"):
                target = root / sequence / "gt/gt.txt"
                target.parent.mkdir(parents=True)
                target.write_bytes(b"synthetic; must not be opened by the guard")
                files[sequence] = target
            with patch.object(Path, "read_bytes", side_effect=AssertionError("Guard opened contents")):
                self.assertEqual(scoped_inputs(files, "gt", self.api), files)
                redirected = dict(files)
                redirected["MOT20-01"] = files["MOT20-02"]
                with self.assertRaises(ValueError):
                    scoped_inputs(redirected, "gt", self.api)
                banned = {s: root / "sealed" / s / "gt/gt.txt" for s in files}
                with self.assertRaisesRegex(ValueError, "outside the development"):
                    scoped_inputs(banned, "gt", self.api)


if __name__ == "__main__":
    unittest.main()
