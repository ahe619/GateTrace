"""Pure MOT20 adapter around exact, hash-checked frozen event functions.

Importing this module does not read project files or import old main modules.
The caller explicitly supplies read_bytes(path, purpose=...) to load_frozen;
the caller also owns all metadata, observations, G1 models, polygons and I/O.
No detector, tracker, identity association, matching, scoring or data fitting is
implemented here. All frame ordinals are sequence-local, zero based internally;
source_frame is the original MOT one-based image number.
"""
from __future__ import annotations

import ast
from collections import Counter, defaultdict
from copy import deepcopy
import hashlib
import math
from pathlib import Path


FROZEN = {
    "r15e3_regions_common.py": {
        "sha256": "e2dd5687f6b5574d1aa49a3396cba97baee453c20c6870e7515bc2a86f8f25e4",
        "functions": ("nearest_boundary", "signed_distance"),
    },
    "r15e3_e2_core.py": {
        "sha256": "a9d4ef470e8adbd7b6cb0f0a0017c8592873a885b3ea2b5e9423c31484476c89",
        "functions": ("zone_from_distances", "extract_region_events"),
    },
    "r15e6_core.py": {
        "sha256": "91bb6c597db1c404738f153d8ed86608b449c71aa4f48204d489ff8047447ded",
        "functions": ("height_at_foot", "edge_distance", "evidence"),
    },
    "r15_dedup_direction.py": {
        "sha256": "dbf70dc6eb38875250d4248f3b49f36c03bba0d0fd1bf7ac90241f4d20bcb9f7",
        "functions": ("_event_frame", "_event_key", "_valid_point", "_observation_detail", "_window", "transform_events"),
        "constants": ("VARIANTS", "SOURCE_ZONE", "TARGET_ZONE"),
    },
    "r15e3_head.py": {
        "sha256": "e67a1c05abb9f5039433054aadfef9491a488c42b6bb336ffe4b20086afa2f17",
        "functions": ("finite_point", "keypoint_mean", "predict_height", "select_point"),
    },
}
C1_KEY = "C1_q0p2_observed"


def make_height_model(coefficients, fitting_coordinate_range):
    """Package externally fitted G1; do not fit, round, clip or infer ranges."""
    if len(coefficients) != 3 or not all(math.isfinite(float(x)) for x in coefficients):
        raise ValueError("G1 requires three finite coefficients")
    for key in ("head_x_norm", "head_y_norm"):
        values = fitting_coordinate_range[key]
        if len(values) != 2 or not all(math.isfinite(float(x)) for x in values) or values[0] > values[1]:
            raise ValueError(f"Invalid externally supplied G1 range: {key}")
    return {"available": True, "coefficients": list(coefficients),
            "fitting_coordinate_range": deepcopy(fitting_coordinate_range)}


def load_frozen(read_bytes, project_root, numpy_module=None):
    """Explicitly read and verify every selected source before compiling any.

    read_bytes must return bytes and record the read in the caller's ledger.
    Only named function AST nodes and named literal constants are compiled;
    imports, module-level I/O, constructors, main guards and selftests are not.
    numpy_module is optional and required only when select_hybrid is called.
    """
    sources = []
    for filename, spec in FROZEN.items():
        path = str(Path(project_root) / "scripts" / filename)
        raw = read_bytes(path, purpose="MOT20 E24 exact frozen pure-function source")
        if not isinstance(raw, bytes):
            raise TypeError("read_bytes must return bytes")
        digest = hashlib.sha256(raw).hexdigest()
        if digest != spec["sha256"]:
            raise RuntimeError(f"Frozen source hash mismatch: {path}")
        source = raw.decode("utf-8-sig")
        sources.append((path, raw, source, ast.parse(source, filename=path), spec))

    namespace = {"__name__": "r15e24_exact_frozen_functions", "math": math,
                 "defaultdict": defaultdict, "Counter": Counter, "deepcopy": deepcopy,
                 "np": numpy_module}
    audit = []
    for path, raw, source, tree, spec in sources:
        definitions = {n.name: n for n in tree.body if isinstance(n, ast.FunctionDef)}
        constants = {}
        for node in tree.body:
            if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
                if node.targets[0].id in spec.get("constants", ()):
                    constants[node.targets[0].id] = node
        if set(spec["functions"]) - definitions.keys() or set(spec.get("constants", ())) - constants.keys():
            raise RuntimeError(f"Frozen AST member missing: {path}")
        selected = [constants[name] for name in spec.get("constants", ())]
        selected += [definitions[name] for name in spec["functions"]]
        segments = []
        for node in selected:
            segment = ast.get_source_segment(source, node)
            segments.append({"name": node.name if isinstance(node, ast.FunctionDef) else node.targets[0].id,
                             "first_line": node.lineno, "last_line": node.end_lineno,
                             "ast_source_segment_sha256_utf8": hashlib.sha256(segment.encode("utf-8")).hexdigest()})
        code = compile(ast.Module(body=selected, type_ignores=[]), path, "exec")
        exec(code, namespace)
        audit.append({"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
                      "expected_sha256": spec["sha256"], "exact_original_ast": True, "selected_members": segments})
    return FrozenEvents(namespace, audit)


class FrozenEvents:
    def __init__(self, functions, audit):
        self._functions = functions
        self._audit = audit

    @property
    def function_audit(self):
        return deepcopy(self._audit)

    def select_hybrid(self, detection, model, size):
        """Optional secondary P1 point; original .5-confidence frozen choice."""
        if self._functions["np"] is None:
            raise RuntimeError("The caller must supply numpy_module for optional hybrid selection")
        return self._functions["select_point"](detection, "hybrid", model, size, confidence=.5)

    def evaluate_sequence_gate(self, observations, *, sequence, gate_id, width, height,
                               nb_frames, fps, model, polygons):
        """Run extraction, observed C1 and R1+R2 on one complete sequence/gate.

        Input observations supply frame, track_id, point (or None), point_source.
        They may also supply source_frame/time_s/source_time_s; supplied clocks
        must equal frame+1 and frame/25 respectively. Other fields (boxes,
        confidence, raw index, physical row references) are retained. Polygons
        are external native-coordinate {'tunnel': [...], 'plaza': [...]}.
        No boundary clipping, invalid-point fallback, window filtering, or
        output-dependent parameter choices occur in this adapter.
        """
        if float(fps) != 25.:
            raise ValueError("Frozen MOT20 protocol requires 25 fps")
        if width <= 0 or height <= 0 or int(nb_frames) != nb_frames or nb_frames <= 0:
            raise ValueError("Invalid external sequence metadata")
        if set(polygons) != {"tunnel", "plaza"}:
            raise ValueError("Exactly two externally supplied native polygons are required")
        for polygon in polygons.values():
            if len(polygon) < 3 or any(len(p) != 2 or not all(math.isfinite(float(v)) for v in p) for p in polygon):
                raise ValueError("Polygon coordinates must be finite native 2D points")
        clip_id = f"{sequence}:{gate_id}"
        normalized = []
        for original in observations:
            o = deepcopy(original)
            f = o["frame"]
            if isinstance(f, bool) or int(f) != f or not 0 <= f < nb_frames:
                raise ValueError("Observation frame must be a valid zero-based sequence ordinal")
            f = int(f)
            t = f / float(fps)
            if "source_frame" in o and o["source_frame"] != f + 1:
                raise ValueError("source_frame must be the one-based MOT image number")
            for key in ("time_s", "source_time_s"):
                if key in o and float(o[key]) != t:
                    raise ValueError(f"Observation {key} differs from frame/25")
            o["track_id"]
            o["point_source"]
            point = o["point"]
            if point is not None and (len(point) != 2 or not all(math.isfinite(float(v)) for v in point)):
                raise ValueError("Point must be finite or explicitly None; no implicit fallback")
            distances = {name: self._functions["signed_distance"](point, poly) if point is not None else None
                         for name, poly in polygons.items()}
            o.update(frame=f, source_frame=f+1, time_s=t, source_time_s=t,
                     sequence=sequence, gate_id=gate_id, clip_id=clip_id, signed_distances=distances)
            o["zone"] = self._functions["zone_from_distances"](distances, 0.) if point is not None else None
            normalized.append(o)
        # Only chronological ordering is supplied to the original FSM. Duplicate
        # observations for a known ID/frame still fail its original assertion.
        normalized.sort(key=lambda o: o["frame"])
        candidates, fragments, extraction_stats = self._functions["extract_region_events"](
            normalized, margin=0., max_gap_s=.5)
        tracks = defaultdict(list)
        for o in normalized:
            if o["track_id"] is not None:
                tracks[o["track_id"]].append(o)
        fragment_index = {(f["track_id"], f["fragment_index"]): f for f in fragments}
        clip = {"camera": str(gate_id), "metadata": {
            "width": width, "height": height, "nb_frames": int(nb_frames), "fps": float(fps)}}
        cfg = {"window_s": 2., "epsilon": 1e-9,
               "conditions": [{"key": C1_KEY, "rule": "C1", "coefficient": .2, "coverage": "observed"}],
               "geometry": {"facing_edges_zero_based": {str(gate_id): {"tunnel": [0], "plaza": [0]}}}}
        c1_results = []
        confirmed = []
        for event in candidates:
            target = event["endpoints"][1]
            event.update(clip_id=clip_id, sequence=sequence, gate_id=gate_id,
                         event_key=f"{clip_id}:{event['prediction_id']}", target_frame=target["frame"],
                         source_frame=target["source_frame"], source_time_s=target["source_time_s"],
                         crossing_position_native_px=deepcopy(target["point"]))
            detail = self._functions["evidence"](
                event, tracks[event["track_id"]], fragment_index[(event["track_id"], event["fragment_index"])],
                clip, model, polygons, cfg)
            detail.update(sequence=sequence, gate_id=gate_id, event_key=event["event_key"],
                          source_frame=event["source_frame"], source_time_s=event["source_time_s"])
            c1_results.append(detail)
            event["c1_evidence_index"] = len(c1_results)-1
            event["confirmer"] = dict(deepcopy(detail["verdicts"][C1_KEY]), condition_key=C1_KEY,
                                      evidence_index=event["c1_evidence_index"], evidence_event_key=event["event_key"])
            if detail["verdicts"][C1_KEY]["keep"]:
                confirmed.append(deepcopy(event))
        groups, group_details = self._functions["transform_events"](confirmed, normalized, "R1+R2")
        final = []
        for group in groups:
            if group["keep"]:
                representative = deepcopy(group["representative"])
                representative.update(group_id=group["group_id"], global_group_id=f"{clip_id}:{group['group_id']}",
                                      member_prediction_ids=deepcopy(group["member_prediction_ids"]),
                                      member_event_keys=[e["event_key"] for e in group["member_events"]],
                                      member_events=deepcopy(group["member_events"]),
                                      first_t=group["first_t"], last_t=group["last_t"],
                                      dedup_decision=group["decision"], dedup_variant="R1+R2")
                final.append(representative)
        return {"schema": "r15e24_sequence_gate_events_v1", "sequence": sequence, "gate_id": gate_id,
                "frame_semantics": "frame/target_frame zero based; source_frame one-based MOT image ordinal",
                "time_semantics": "sequence seconds = (source_frame-1)/25; no scoring-window truncation",
                "metadata": clip["metadata"], "observations": normalized, "fragments": fragments,
                "raw_candidates": candidates, "c1_evidence": c1_results, "raw_confirmed_events": confirmed,
                "groups": groups, "group_details": group_details, "final_events": final,
                "extraction_stats": extraction_stats, "function_audit": self.function_audit,
                "event_parameters": cfg, "dedup_variant": "R1+R2",
                "model": deepcopy(model), "native_polygons": deepcopy(polygons)}
