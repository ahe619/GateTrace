"""Exercise the real renderer using generated colour blocks and in-memory rows.

No study image, GT file, tracking result, answer or browser storage is read.
The renderer and Inspector.read are real; only the inspector's data is synthetic.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest

from scratch_support import scratch_parent

PACKAGE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACKAGE))
from PIL import Image
from src.inspection import Inspector, render_event


class FakeInspector:
    def __init__(self, image_paths, *, width, height, length, frames):
        self.package = PACKAGE
        self.reads = []
        self.allowed_images = {p.resolve() for p in image_paths}
        self.summary = {'sequences': {'MOT20-01': {'metadata': {
            'width': width, 'height': height, 'seqLength': length}}}}
        self.gt = {'MOT20-01': {7: [SimpleNamespace(
            frame=f, track_id=7, x0=width*.10, y0=height*.45,
            x1=width*.30, y1=height*.85) for f in frames]}}
        self.frames = {'MOT20-01': {f: [{'track_id': 100,
            'box': [width*.65, height*.45, width*.85, height*.85]}] for f in frames}}

    def read(self, path, alias, binding=None):
        path = Path(path)
        if path.resolve() not in self.allowed_images or not alias.startswith('image:MOT20-01:'):
            raise AssertionError('Unexpected non-synthetic renderer read: ' + str(path))
        # Use the actual byte read and actual read-ledger implementation.
        return Inspector.read(self, path, alias, binding)


class RenderingTests(unittest.TestCase):
    def setUp(self):
        self.parent = scratch_parent()
        self.temporary = tempfile.TemporaryDirectory(prefix='render_round2_', dir=self.parent)
        self.root = Path(self.temporary.name).absolute()
        self.assertEqual(self.root.parent, self.parent)
        self.addCleanup(self.checked_cleanup)

    def checked_cleanup(self):
        if self.root.parent != self.parent or not self.root.name.startswith('render_round2_'):
            raise RuntimeError('Refusing cleanup outside the synthetic renderer root')
        if self.root.is_symlink() or self.root.resolve().parent != self.parent.resolve():
            raise RuntimeError('Refusing redirected renderer cleanup root')
        self.temporary.cleanup()

    def fixture(self, *, anchor=50, length=100, size=(400, 200), omit=(), wrong_sizes=None, name='case'):
        width, height = size
        case = self.root/name
        images = case/'MOT20-01/img1'
        images.mkdir(parents=True)
        frames = sorted({max(1, min(length, anchor+d)) for d in (-25, -12, 0, 12, 25)})
        image_paths = []
        for frame in frames:
            if frame in omit:
                continue
            path = images/f'{frame:06d}.jpg'
            frame_size = (wrong_sizes or {}).get(frame, size)
            with Image.new('RGB', frame_size, color=(17+frame % 10, 31, 47)) as image:
                image.save(path, format='JPEG')
            image_paths.append(path)
        inspector = FakeInspector(image_paths, width=width, height=height, length=length, frames=frames)
        detail = {'reference_label': {'sequence':'MOT20-01', 'event_id':'synthetic_only',
            'gt_frame_1based':anchor, 'track_id':7},
            'geometry': {'orientation':'H', 'line_coordinate_px':height*.50,
                'line_extent_px':[width*.05,width*.95],
                'polygons': {
                    'tunnel':[[width*.05,height*.20],[width*.95,height*.20],
                              [width*.95,height*.40],[width*.05,height*.40]],
                    'plaza':[[width*.05,height*.60],[width*.95,height*.60],
                             [width*.95,height*.95],[width*.05,height*.95]]}}}
        return inspector, detail, images, case/'render_output', frames

    def verify_complete(self, inspector, detail, images, output, frames, receipt, size):
        self.assertEqual([r['source_frame_1based'] for r in receipt], frames)
        self.assertEqual(len(receipt), len(set(frames)))
        self.assertEqual([r['asset'] for r in inspector.reads], [f'image:MOT20-01:{f}' for f in frames])
        manifest = json.loads((output/'render_manifest.json').read_text(encoding='utf-8'))
        self.assertEqual(manifest['sequence'], 'MOT20-01')
        self.assertEqual(manifest['event_id'], detail['reference_label']['event_id'])
        self.assertEqual(manifest['frames'], receipt)
        self.assertTrue(manifest['no_matching_outcome_drawn'])
        self.assertTrue(manifest['original_media_not_redistributed'])
        expected_names = {f'frame_{f:06d}.png' for f in frames} | {'render_manifest.json'}
        self.assertEqual({p.name for p in output.iterdir()}, expected_names)
        for frame, row, read in zip(frames, receipt, inspector.reads):
            original = (images/f'{frame:06d}.jpg').read_bytes()
            expected_input_hash = hashlib.sha256(original).hexdigest()
            self.assertEqual(row['input_sha256'], expected_input_hash)
            self.assertEqual(read['sha256'], expected_input_hash)
            self.assertEqual(read['bytes'], len(original))
            self.assertEqual(read['read_status'], 'READ')
            self.assertEqual(row['output_file'], f'frame_{frame:06d}.png')
            rendered = output/row['output_file']
            self.assertEqual(row['output_sha256'], hashlib.sha256(rendered.read_bytes()).hexdigest())
            with Image.open(rendered) as image:
                self.assertEqual(image.size, size)
                colours = set(image.convert('RGB').getdata())
                self.assertIn((0,255,100), colours)  # Synthetic GT overlay.
                self.assertIn((40,150,255), colours)  # Synthetic system overlay.

    def test_normal_five_frames_manifest_hashes_and_overlays(self):
        inspector,detail,images,out,frames=self.fixture()
        receipt=render_event(inspector,detail,images,out)
        self.assertEqual(frames,[25,38,50,62,75])
        self.verify_complete(inspector,detail,images,out,frames,receipt,(400,200))

    def test_square_100_pixel_synthetic_images(self):
        inspector,detail,images,out,frames=self.fixture(size=(100,100))
        receipt=render_event(inspector,detail,images,out)
        self.verify_complete(inspector,detail,images,out,frames,receipt,(100,100))

    def test_beginning_anchor_clamps_and_deduplicates(self):
        inspector,detail,images,out,frames=self.fixture(anchor=1,length=50)
        receipt=render_event(inspector,detail,images,out)
        self.assertEqual(frames,[1,13,26])
        self.verify_complete(inspector,detail,images,out,frames,receipt,(400,200))

    def test_ending_anchor_clamps_and_deduplicates(self):
        inspector,detail,images,out,frames=self.fixture(anchor=50,length=50)
        receipt=render_event(inspector,detail,images,out)
        self.assertEqual(frames,[25,38,50])
        self.verify_complete(inspector,detail,images,out,frames,receipt,(400,200))

    def test_single_frame_sequence_renders_only_once(self):
        inspector,detail,images,out,frames=self.fixture(anchor=1,length=1,size=(100,100))
        receipt=render_event(inspector,detail,images,out)
        self.assertEqual(frames,[1])
        self.verify_complete(inspector,detail,images,out,frames,receipt,(100,100))

    def test_wrong_first_image_dimensions_fail_after_actual_read(self):
        inspector,detail,images,out,_=self.fixture(wrong_sizes={25:(100,100)})
        expected=(images/'000025.jpg').read_bytes()
        with self.assertRaisesRegex(ValueError,'Image dimensions differ'):
            render_event(inspector,detail,images,out)
        self.assertEqual(len(inspector.reads),1)
        self.assertEqual(inspector.reads[0]['asset'],'image:MOT20-01:25')
        self.assertEqual(inspector.reads[0]['bytes'],len(expected))
        self.assertEqual(inspector.reads[0]['sha256'],hashlib.sha256(expected).hexdigest())
        self.assertEqual(inspector.reads[0]['read_status'],'READ')
        self.assertTrue(out.exists())
        self.assertEqual(list(out.iterdir()),[])
        self.assertFalse((out/'render_manifest.json').exists())

    def test_wrong_later_dimensions_preserve_earlier_pngs_and_read_hash(self):
        inspector,detail,images,out,_=self.fixture(wrong_sizes={50:(100,100)})
        expected=(images/'000050.jpg').read_bytes()
        with self.assertRaisesRegex(ValueError,'Image dimensions differ'):
            render_event(inspector,detail,images,out)
        self.assertEqual([r['asset'] for r in inspector.reads],
            ['image:MOT20-01:25','image:MOT20-01:38','image:MOT20-01:50'])
        self.assertEqual(inspector.reads[-1]['sha256'],hashlib.sha256(expected).hexdigest())
        self.assertEqual({p.name for p in out.iterdir()},{'frame_000025.png','frame_000038.png'})
        self.assertFalse((out/'render_manifest.json').exists())

    def test_missing_frame_rejected_before_output_mkdir_and_read(self):
        inspector,detail,images,out,_=self.fixture(omit=(50,))
        with self.assertRaisesRegex(ValueError,'Missing or inaccessible'):
            render_event(inspector,detail,images,out)
        self.assertFalse(out.exists())
        self.assertEqual(inspector.reads,[])

    def test_existing_output_is_not_overwritten(self):
        inspector,detail,images,out,_=self.fixture()
        out.mkdir();sentinel=out/'keep.txt';sentinel.write_bytes(b'preserve synthetic previous output')
        before=sentinel.read_bytes()
        with self.assertRaisesRegex(ValueError,'new directory outside'):
            render_event(inspector,detail,images,out)
        self.assertEqual(sentinel.read_bytes(),before)
        self.assertEqual({p.name for p in out.iterdir()},{'keep.txt'})
        self.assertEqual(inspector.reads,[])

    def test_output_inside_source_images_rejected_before_read(self):
        inspector,detail,images,_,_=self.fixture()
        out=images/'new_render_output'
        with self.assertRaisesRegex(ValueError,'new directory outside'):
            render_event(inspector,detail,images,out)
        self.assertFalse(out.exists())
        self.assertEqual(inspector.reads,[])


if __name__=='__main__':
    unittest.main(verbosity=2)
