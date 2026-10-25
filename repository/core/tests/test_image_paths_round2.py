"""Pure synthetic filesystem tests; no real images, GT or answers are accessed."""
import importlib.util
import os
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock
from scratch_support import scratch_parent

HERE = Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("image_paths_round2", HERE.parent / "src/image_paths.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class ImagePathTests(unittest.TestCase):
    def setUp(self):
        # Only newly created fixtures under the caller's explicit scratch root.
        self.scratch = scratch_parent()
        self.temporary = tempfile.TemporaryDirectory(prefix="imagepaths_synthetic_", dir=self.scratch)
        self.root = Path(self.temporary.name).absolute()
        self.assertEqual(self.root.parent, self.scratch)
        self.addCleanup(self.checked_cleanup)
        self.img = self.root / "MOT20-01/img1"
        self.img.mkdir(parents=True)
        for frame in (100, 101, 102):
            (self.img / f"{frame:06d}.jpg").write_bytes(f"synthetic file for frame {frame}".encode())

    def checked_cleanup(self):
        if self.root.parent != self.scratch or not self.root.name.startswith("imagepaths_synthetic_"):
            raise RuntimeError("Refusing cleanup outside the synthetic fixture root")
        if self.root.is_symlink() or self.root.resolve().parent != self.scratch.resolve():
            raise RuntimeError("Refusing redirected synthetic cleanup root")
        self.temporary.cleanup()

    def link_or_skip(self, source, target, *, directory=False):
        try:
            os.symlink(target, source, target_is_directory=directory)
        except (OSError, NotImplementedError) as error:
            self.skipTest("Real symlink creation unavailable; separate mock coverage retained: " + str(error))

    def test_regular_files_pass_and_order_is_preserved(self):
        directory, frames = MODULE.resolve_image_inputs(self.img, "MOT20-01", [102, 100])
        self.assertEqual(directory, self.img.resolve())
        self.assertEqual(frames, [self.img.resolve()/"000102.jpg", self.img.resolve()/"000100.jpg"])

    def test_second_development_sequence_passes(self):
        image_dir=self.root/"MOT20-02/img1"; image_dir.mkdir(parents=True)
        (image_dir/"000001.jpg").write_bytes(b"synthetic")
        directory,frames=MODULE.resolve_image_inputs(image_dir,"MOT20-02",[1])
        self.assertEqual(frames,[directory/"000001.jpg"])

    def test_directory_tail_must_be_exact(self):
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.root,"MOT20-01",[100])

    def test_wrong_sequence_rejected(self):
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-02",[100])

    def test_confirmation_sequence_rejected_before_any_path_io(self):
        with mock.patch.object(Path,"lstat",side_effect=AssertionError("must not inspect path")):
            with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.root/"MOT20-03/img1","MOT20-03",[1])

    def test_parent_traversal_rejected(self):
        path=self.root/"unused/../MOT20-01/img1"
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(path,"MOT20-01",[100])

    def test_missing_directory_rejected(self):
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.root/"missing/MOT20-01/img1","MOT20-01",[100])

    def test_missing_frame_rejected(self):
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[103])

    def test_directory_disguised_as_frame_rejected(self):
        (self.img/"000103.jpg").mkdir()
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[103])

    def test_invalid_frame_types_rejected(self):
        for frames in ([],[0],[-1],[True],[100.0],["100"],None):
            with self.subTest(frames=frames):
                with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",frames)

    def test_frame_contents_not_read(self):
        with mock.patch.object(Path,"read_bytes",side_effect=AssertionError("pixel read prohibited")), \
             mock.patch.object(Path,"open",side_effect=AssertionError("pixel open prohibited")):
            MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])

    def test_real_same_directory_frame_symlink_rejected(self):
        source=self.img/"000100.jpg"
        source.unlink()  # This file was created above inside the checked synthetic root.
        self.link_or_skip(source,self.img/"000101.jpg")
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])

    def test_real_outside_directory_file_symlink_rejected(self):
        target=self.root/"different_frame.jpg";target.write_bytes(b"synthetic outside img1")
        source=self.img/"000103.jpg";self.link_or_skip(source,target)
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[103])

    def test_real_img1_directory_symlink_rejected(self):
        seq=self.root/"alias/MOT20-01";seq.mkdir(parents=True)
        self.link_or_skip(seq/"img1",self.img,directory=True)
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(seq/"img1","MOT20-01",[100])

    def test_real_ancestor_symlink_rejected(self):
        target=self.root/"real_parent";image_dir=target/"MOT20-01/img1";image_dir.mkdir(parents=True)
        (image_dir/"000100.jpg").write_bytes(b"synthetic")
        link=self.root/"alias_parent";self.link_or_skip(link,target,directory=True)
        with self.assertRaises(ValueError):MODULE.resolve_image_inputs(link/"MOT20-01/img1","MOT20-01",[100])

    def mock_redirect_metadata(self, flagged, *, symlink=False):
        original=Path.lstat
        def fake(path,*args,**kwargs):
            result=original(path,*args,**kwargs)
            if path.absolute()==flagged.absolute():
                return SimpleNamespace(st_mode=stat.S_IFLNK if symlink else result.st_mode,
                    st_file_attributes=0 if symlink else 0x400)
            return result
        return mock.patch.object(Path,"lstat",fake)

    def test_mock_file_symlink_metadata_rejected(self):
        with self.mock_redirect_metadata(self.img/"000100.jpg",symlink=True):
            with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])

    def test_mock_img1_junction_reparse_rejected(self):
        with self.mock_redirect_metadata(self.img):
            with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])

    def test_mock_sequence_junction_reparse_rejected(self):
        with self.mock_redirect_metadata(self.img.parent):
            with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])

    def test_mock_ancestor_junction_reparse_rejected(self):
        with self.mock_redirect_metadata(self.root):
            with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])

    def test_mock_file_reparse_rejected(self):
        with self.mock_redirect_metadata(self.img/"000100.jpg"):
            with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])

    def test_mock_same_directory_resolve_frame_change_rejected(self):
        original=Path.resolve
        def fake(path,*args,**kwargs):
            if path==self.img/"000100.jpg":return self.img/"000101.jpg"
            return original(path,*args,**kwargs)
        with mock.patch.object(Path,"resolve",fake):
            with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])

    def test_mock_external_resolve_rejected(self):
        target=self.root/"outside.jpg";target.write_bytes(b"synthetic")
        original=Path.resolve
        def fake(path,*args,**kwargs):
            if path==self.img/"000100.jpg":return target
            return original(path,*args,**kwargs)
        with mock.patch.object(Path,"resolve",fake):
            with self.assertRaises(ValueError):MODULE.resolve_image_inputs(self.img,"MOT20-01",[100])


if __name__ == "__main__":
    unittest.main(verbosity=2)
