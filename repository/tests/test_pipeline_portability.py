"""Synthetic-only wrapper and frozen-primitive tests. No model or dataset access."""
from pathlib import Path
import copy
import hashlib
import json
import math
import sys
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.detect.io import (activate_frozen, explicit_asset, new_output, relative,
                           fragment_namespace, verify_frozen)
from src.detect.cli import validate_manifest, WEIGHT_SHA
from src.analysis.cli import analyze, module
from src.track.cli import mot_line
from src.track.native_v11 import native_events
from src.confirm.cli import deployment_path, generate_workspace


class PortabilityTests(unittest.TestCase):
    def pixel_fixture(self):
        return dict(schema="crowd_flow_pixel_inputs_v1", sequence="MOT20-01", fps=25,
                    native_size=[100, 80], weight=dict(path="checkpoint.pt", bytes=1, sha256=WEIGHT_SHA),
                    images=[dict(source_frame=1, binding=dict(path="images/one.png", bytes=1, sha256="0"*64))])

    def test_development_manifest_and_path_scope(self):
        doc = self.pixel_fixture()
        self.assertIs(validate_manifest(doc), doc)
        for sequence in ("MOT20-03", "MOT20-05", "unknown"):
            changed = copy.deepcopy(doc)
            changed["sequence"] = sequence
            with self.assertRaises(ValueError):
                validate_manifest(changed)
        for path in ("../escape", "/root/file", "bad\\separator", ""):
            with self.assertRaises(ValueError):
                relative(path)
        changed = copy.deepcopy(doc)
        changed["images"][0]["source_frame"] = 2
        with self.assertRaises(ValueError):
            validate_manifest(changed)

    def test_binding_checks_real_bytes_only_synthetic_asset(self):
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "fake.bin"
            path.write_bytes(b"synthetic")
            ref = dict(path=path.name, bytes=9, sha256=hashlib.sha256(b"synthetic").hexdigest())
            self.assertEqual(explicit_asset(temporary, ref), path)
            ref["sha256"] = "0"*64
            with self.assertRaises(ValueError):
                explicit_asset(temporary, ref)
        with self.assertRaises(ValueError):
            new_output(ROOT / "must_not_write")

    def test_all_complete_frozen_files_match(self):
        self.assertGreaterEqual(len(verify_frozen("src/")), 48)

    def test_optimized_python_is_rejected(self):
        code = "import sys;sys.path.insert(0," + repr(str(ROOT)) + ");from src.detect.io import verify_frozen;verify_frozen('src/')"
        result = subprocess.run([sys.executable, "-I", "-S", "-B", "-O", "-c", code],
                                capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Do not use Python -O", result.stderr)

    def test_e2_grid_partition_and_reproducibility(self):
        doc = dict(sequence="MOT20-01", fps=25, retention="0.5", seed=20261023, mode="block",
                   observations=[dict(sequence_id="MOT20-01", identity_id="1", frame=i,
                                      visibility_bin="low") for i in range(1, 31)])
        result = analyze("e2-mask", doc)
        self.assertEqual(len(result["kept"]), 15)
        self.assertEqual(len(result["deleted"]), 15)
        self.assertEqual(result, analyze("e2-mask", doc))
        self.assertEqual(result["segments"][0]["block_frames"], 13)
        doc["retention"] = "1"
        baseline = analyze("e2-mask", doc)
        self.assertEqual(len(baseline["kept"]), 30)
        self.assertEqual(baseline["deleted"], ())

    def test_d1_original_selftest_and_adapter(self):
        self.assertTrue(module("d1").selftest()["passed"])
        result = analyze("d1-gaps", dict(sequence="MOT20-01", fps=25,
            timelines={"7": [dict(source_frame=1, point=[1, 1]), dict(source_frame=14, point=[1, 20])]}))
        self.assertEqual(result["gaps"][0]["missing_frames"], 12)
        self.assertEqual(result["gaps"][0]["duration_bin"], "gt_0p5_le_1")

    def test_headgate_projection_and_boundary(self):
        result = analyze("headgate-project", dict(sequence="MOT20-01", native_size=[100, 100],
            calibration={"coefficients_a_b": [2, 0]},
            detections=[{"box": [10, 10, 20, 20]}, {"box": [0, 10, 20, 20]}]))
        self.assertEqual(result["points"][0]["point"], [15, 40])
        self.assertIsNone(result["points"][1]["point"])

    def test_gatelink_interpolation_uses_frozen_primitive(self):
        rows = [[1, 7, 10, 10, 20, 40, .9], [4, 7, 13, 13, 20, 40, .9]]
        result = analyze("gatelink", dict(sequence="MOT20-01", mode="bridge", max_gap_frames=50, rows=rows))
        self.assertEqual(result["added"], 2)
        self.assertEqual(next(r for r in result["rows"] if r[0] == 2)[2:4], [11, 11])
        self.assertEqual(rows[0], [1, 7, 10, 10, 20, 40, .9])

    def test_e1_recovered_precedence(self):
        args = dict(g={}, evidence={}, matched="synthetic_prediction", tie=None, anonymous_unknown=[],
                    support={}, gtframes={}, polygons={}, width=100, height=100,
                    fragment_lookup=[], outputobs={}, saved={}, identities={})
        result = analyze("e1-attribute", dict(sequence="MOT20-01", arguments=args))
        self.assertEqual(result["category"], "RECOVERED")
        self.assertFalse(result["causal_claim"])

    def test_m4_rejects_missing_policy_before_frames(self):
        with self.assertRaises(RuntimeError):
            analyze("m4-stitch", dict(sequence="MOT20-01", namespace={"sequence": "MOT20-01", "block": "all"},
                fps=25, frames=None, gates=None, g1=None, policy=None))

    def test_standard_output_geometry_without_rounding(self):
        line = mot_line(3, dict(box=[1.25, 2.5, 11.25, 22.5], track_id=9, score=None))
        self.assertEqual(line, "3,9,2.25,3.5,10.0,20.0,-1,-1,-1,-1\n")

    def test_confirmation_generation_never_opens_approval_or_assets(self):
        activate_frozen("src/confirm")
        from production_v1 import command, manifest
        ref = lambda path: dict(path=path, bytes=0, sha256="0"*64)
        doc = dict(schema=manifest.SCHEMA, manifest_id="synthetic", producer="synthetic test",
            scope="development", sequences=["MOT20-01", "MOT20-02"], systems=list(manifest.SYSTEMS),
            assets=[], freeze=ref("freeze.json"), reference_modes={"p2": "import_existing", "o1": "import_existing"},
            run_root="data/r15/confirmation85/synthetic_run", resources=dict(
                stages={s: dict(cpu_seconds=1, wall_seconds=1) for s in manifest.STAGES},
                max_output_bytes=1024, min_free_bytes=0, max_workers=1, cpu_threads=1),
            interpreters={"detector": ref("python"), "cpu": ref("python")}, runtime_roots=["runtime"])
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "docs").mkdir()
            source = root / "docs/manifest.json"
            source.write_text(json.dumps(doc), encoding="utf-8")
            payload_sha = hashlib.sha256(source.read_bytes()).hexdigest()
            result, _ = generate_workspace(root, "docs/manifest.json", payload_sha,
                "docs/approval_does_not_exist.json", "0"*64, "data/r15/confirmation85/commands")
            self.assertFalse(result["stages_executed"])
            self.assertFalse(result["referenced_asset_paths_opened"])
            self.assertEqual(len(result["scientific_stages"]), 18)
            self.assertFalse((root / "docs/approval_does_not_exist.json").exists())
            self.assertFalse((root / doc["run_root"]).exists())
        self.assertNotIn("torch", sys.modules)

    def test_confirmation_deployment_containment(self):
        with tempfile.TemporaryDirectory() as temporary:
            workspace = Path(temporary)
            target = workspace / "scripts/confirmation85/production_v1"
            self.assertEqual(deployment_path(workspace, target), target)
            with self.assertRaisesRegex(ValueError, "external workspace"):
                deployment_path(workspace, workspace / ".." / "unexpected_confirmation_destination")
            self.assertFalse(target.exists())

    def test_fragment_fresh_raw_discards_old_identity_without_changing_box(self):
        def require(value, message):
            if not value:
                raise ValueError(message)
        ns = fragment_namespace("r15e26_run_v2.py", dict(copy=copy, math=math, require=require, FROZEN={}))
        old = dict(raw_detection_index=0, box=[1, 2, 3, 4], confidence=.2, class_id=0,
                   track_id=99, point=[2, 4], original_track_id=42)
        new = ns["fresh_raw"]([old])[0]
        self.assertIsNone(new["track_id"])
        self.assertEqual(new["box"], old["box"])
        self.assertNotIn("point", new)
        self.assertNotIn("original_track_id", new)
        self.assertEqual(old["track_id"], 99)

    def test_native_events_use_raw_detection_feet(self):
        frames = []
        for frame in range(75):
            y = 30 if frame < 35 else 70
            frames.append(dict(frame=frame, source_frame=frame+1,
                detections=[dict(frame=frame, source_frame=frame+1, track_id=1, box=[40, y-20, 60, y],
                    confidence=.9, raw_detection_index=0, point=[50, y], point_source="box_bottom_center")],
                tracker_rows=[[40, y-20, 60, y+10, 1, .9, 0, 0]]))
        geometry = {"lines": [{"line_id": "H_50", "polygons": {
            "tunnel": [[0, 40], [100, 40], [100, 0], [0, 0]],
            "plaza": [[0, 60], [100, 60], [100, 100], [0, 100]]}}]}
        g1 = dict(coefficients=[10, 0, 0], fitting_coordinate_range={"x_normalized": [0, 1], "y_top_normalized": [0, 1]})
        result = native_events(frames, dict(sequence="MOT20-01", native_size=[100, 100], frames=75), geometry, g1)
        final = result["H_50"]["final_events"]
        self.assertEqual(len(final), 1)
        self.assertEqual(final[0]["crossing_position_native_px"], [50, 70])

    def test_reid_decision_exact_original_thresholds(self):
        def unit(low, high, correct, final):
            return dict(bins={"low": {"numerator": low}, "high": {"numerator": high}}, correct=correct, final_events=final)
        report = {"main": {"aggregate": unit(84, 208, 584, 634), "by_sequence": {
            "MOT20-01": unit(16, 13, 55, 55), "MOT20-02": unit(68, 195, 529, 579)}}}
        result = analyze("reid-decision", dict(sequence="MOT20-01", report=report))
        self.assertEqual(result["decision"], "BASELINE_ONLY")
        self.assertEqual(result["delta_low_correct"], 0)
        self.assertEqual(result["state"], "PENDING_CLAUDE_RECOMPUTE")


if __name__ == "__main__":
    unittest.main()
