"""Synthetic portability and strict-input checks; no real GT or examples are read."""
import importlib.util
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts.resource_entry import build_command, cpu_environment, external_output, normalize_arguments

spec = importlib.util.spec_from_file_location(
    "resource_synthetic_mot_reader", ROOT / "core/src/motchallenge.py"
)
mot_reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mot_reader)


class ResourceAdapterTests(unittest.TestCase):
    def test_rejects_repository_output_and_ancestors(self):
        for path in (ROOT, ROOT / "new_runtime", ROOT.parent):
            with self.subTest(path=path):
                with self.assertRaises(ValueError):
                    external_output(path)

    def test_external_output_must_be_new(self):
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaises(ValueError):
                external_output(temp)
            new = Path(temp) / "new"
            self.assertEqual(external_output(new), new.resolve())
            self.assertFalse(new.exists())

    def test_path_arguments_are_absolute_and_scientific_flags_unchanged(self):
        with tempfile.TemporaryDirectory() as temp:
            out = Path(temp) / "new"
            arguments = normalize_arguments(
                ["--self-test", "--gt-root", "official/train",
                 "--seqinfo-root=metadata/train", "--out", str(out)]
            )
            self.assertEqual(arguments[0], "--self-test")
            self.assertEqual(Path(arguments[2]), Path("official/train").resolve())
            self.assertEqual(Path(arguments[4]), Path("metadata/train").resolve())
            self.assertEqual(Path(arguments[6]), out.resolve())

    def test_only_frozen_resource_entries_can_launch(self):
        with self.assertRaises(ValueError):
            build_command("other.py", [])
        command = build_command("score_tracker.py", ["--help"], executable="python")
        self.assertEqual(command[:2], ["python", "-B"])
        self.assertEqual(Path(command[2]), ROOT / "core/score_tracker.py")
        self.assertEqual(command[3:], ["--help"])

    def test_cpu_environment_keeps_assertions_and_no_bytecode(self):
        env = cpu_environment()
        self.assertEqual(env["CUDA_VISIBLE_DEVICES"], "")
        self.assertEqual(env["PYTHONDONTWRITEBYTECODE"], "1")
        self.assertNotIn("PYTHONOPTIMIZE", env)
        self.assertNotIn("PYTHONPATH", env)
        self.assertEqual(env["OPENBLAS_NUM_THREADS"], "1")

    def test_missing_paths_rejected(self):
        for arguments in (["--out"], ["--out="], ["--out", "--self-test"]):
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    normalize_arguments(arguments)

    def test_abbreviations_cannot_bypass_output_location_checks(self):
        for arguments in (["--ou", str(ROOT / "runtime")],
                          ["--render-o=" + str(ROOT / "rendered")]):
            with self.subTest(arguments=arguments):
                with self.assertRaises(ValueError):
                    normalize_arguments(arguments)

    def test_mot_conversion_preserves_row_order(self):
        frames, stats = mot_reader.parse_results(
            "1,8,11,21,30,40,0.9,-1,-1,-1\n1,2,12,22,30,40,0.8,-1,-1,-1\n", 3
        )
        self.assertEqual([row["track_id"] for row in frames[1]], [8, 2])
        self.assertEqual(frames[1][0]["box"], [10.0, 20.0, 40.0, 60.0])
        self.assertEqual(stats["rows"], 2)

    def test_duplicate_or_nonfinite_mot_rows_fail(self):
        row = "1,8,11,21,30,40,0.9,-1,-1,-1\n"
        for text in (row + row, row.replace("0.9", "nan"), row.replace(",30,", ",0,")):
            with self.subTest(text=text):
                with self.assertRaises(ValueError):
                    mot_reader.parse_results(text, 3)


if __name__ == "__main__":
    unittest.main()

