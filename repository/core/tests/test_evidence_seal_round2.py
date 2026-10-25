"""Synthetic integrity faults; no real tracking output or reference labels."""
import copy
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import unittest
from scratch_support import scratch_parent

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from src.evidence_seal import (FILES, MANIFEST_NAME, load_evidence_bindings,
                               safe_evidence_path, seal_score_evidence)


class SealTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='synthetic_inspector_seal_', dir=scratch_parent())
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for name in FILES:
            value = dict(status='COMPLETE') if name == 'complete.json' else []
            (self.root/name).write_text(json.dumps(value), encoding='utf-8')

    @staticmethod
    def read(path, alias, binding=None):
        raw = Path(path).read_bytes()
        actual = dict(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if binding and any(actual[k] != binding[k] for k in ('bytes','sha256') if k in binding):
            raise ValueError('Bound input changed: '+alias)
        return raw

    def sealed(self):
        seal = seal_score_evidence(self.root, 'a'*64)
        return seal, load_evidence_bindings(self.root, seal['sha256'], self.read, 'a'*64)

    def rewrite_manifest(self, transform):
        path = self.root/MANIFEST_NAME
        data = json.loads(path.read_text(encoding='utf-8'))
        transform(data)
        raw = json.dumps(data).encode('utf-8')
        path.write_bytes(raw)
        return hashlib.sha256(raw).hexdigest()

    def test_new_score_seal_binds_all_six_inspected_artifacts(self):
        seal, mapping = self.sealed()
        self.assertEqual(seal['files'], 6)
        self.assertEqual(set(mapping), set(FILES))
        for name, binding in mapping.items():
            self.read(safe_evidence_path(self.root,name), name, binding)

    def test_manifest_bytes_reproducible_without_times_or_absolute_paths(self):
        first, _ = self.sealed()
        other = self.root/'second';other.mkdir()
        for name in FILES:
            (other/name).write_bytes((self.root/name).read_bytes())
        second = seal_score_evidence(other, 'a'*64)
        self.assertEqual(first,second)
        self.assertNotIn(str(self.root), (self.root/MANIFEST_NAME).read_text(encoding='utf-8'))

    def test_existing_seal_is_not_overwritten_or_blessed_again(self):
        seal, _ = self.sealed()
        before = (self.root/MANIFEST_NAME).read_bytes()
        with self.assertRaises(FileExistsError): seal_score_evidence(self.root, 'a'*64)
        self.assertEqual(before, (self.root/MANIFEST_NAME).read_bytes())

    def test_unsealed_stored_evidence_has_no_default_trust(self):
        for anchor in (None,'','0'*63,'G'*64,123):
            with self.subTest(anchor=anchor), self.assertRaises(ValueError):
                load_evidence_bindings(self.root,anchor,self.read,'a'*64)

    def test_non_complete_receipt_cannot_be_sealed(self):
        (self.root/'complete.json').write_text('{"status":"PARTIAL"}',encoding='utf-8')
        with self.assertRaises(ValueError):seal_score_evidence(self.root, 'a'*64)
        self.assertFalse((self.root/MANIFEST_NAME).exists())

    def test_missing_member_does_not_produce_a_seal(self):
        (self.root/FILES[-1]).unlink()
        with self.assertRaises(FileNotFoundError):seal_score_evidence(self.root, 'a'*64)
        self.assertFalse((self.root/MANIFEST_NAME).exists())

    def test_mutated_gzip_bytes_fail_binding_before_decompression(self):
        _, bindings = self.sealed()
        path = self.root/FILES[-1]
        path.write_bytes(b'valid-looking-but-changed')
        with self.assertRaisesRegex(ValueError,'Bound input changed'):
            self.read(path,FILES[-1],bindings[FILES[-1]])

    def test_mutated_manifest_fails_retained_anchor(self):
        seal,_ = self.sealed()
        self.rewrite_manifest(lambda x:x.update(scientific_qc='changed'))
        with self.assertRaisesRegex(ValueError,'Bound input changed'):
            load_evidence_bindings(self.root,seal['sha256'],self.read,'a'*64)

    def test_duplicate_entry_fails_even_with_fresh_anchor(self):
        self.sealed()
        anchor=self.rewrite_manifest(lambda x:x['files'].__setitem__(1,copy.deepcopy(x['files'][0])))
        with self.assertRaisesRegex(ValueError,'Duplicate'):
            load_evidence_bindings(self.root,anchor,self.read,'a'*64)

    def test_unexpected_and_escaping_paths_are_rejected(self):
        for name in ('../complete.json','/complete.json','unknown.json','C:/complete.json'):
            with self.subTest(name=name), self.assertRaises(ValueError):
                safe_evidence_path(self.root,name)

    def test_malformed_bound_sizes_and_hashes_are_rejected(self):
        for case_index,(key,value) in enumerate((('bytes',True),('bytes',-1),('bytes',1.5),('sha256','0'*63),('sha256',None))):
            with self.subTest(key=key,value=value):
                # Short fixture names remain usable below a long Windows checkout.
                folder=self.root/f'case_{case_index}';folder.mkdir()
                for name in FILES:(folder/name).write_bytes((self.root/name).read_bytes())
                seal_score_evidence(folder, 'a'*64)
                data=json.loads((folder/MANIFEST_NAME).read_text(encoding='utf-8'))
                data['files'][0][key]=value
                raw=json.dumps(data).encode();(folder/MANIFEST_NAME).write_bytes(raw)
                with self.assertRaises(ValueError):
                    load_evidence_bindings(folder,hashlib.sha256(raw).hexdigest(),self.read,'a'*64)


if __name__ == '__main__': unittest.main(verbosity=2)
