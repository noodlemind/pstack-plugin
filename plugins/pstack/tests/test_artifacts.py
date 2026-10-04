import base64
import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))

from api import context
from artifacts import content, read
from store import Store


class ArtifactTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pstack-artifacts-')
        self.root = Path(self.tmp.name).resolve()
        self.scope = self.root / 'repo'; self.scope.mkdir()
        self.other = self.root / 'other'; self.other.mkdir()
        self.store = Store(self.root / 'state')
        self.key = 'a' * 32
        self.folder = self.store.home / 'controls' / self.key
        self.folder.mkdir(parents=True)
        (self.folder / 'owner.json').write_text(json.dumps({'workspace': str(self.scope)}))
        self.args = {'workspace': str(self.scope), 'kind': 'control', 'id': self.key}

    def tearDown(self):
        self.tmp.cleanup()

    def test_owned_image_is_native_mcp_content(self):
        pixels = b'\x89PNG\r\n\x1a\nfixture'
        (self.folder / 'capture.png').write_bytes(pixels)
        value = read(self.store, {**self.args, 'name': 'capture.png'})
        self.assertEqual(base64.b64decode(content(value)[1]['data']), pixels)
        self.assertEqual(content(value)[1]['type'], 'image')
        self.assertEqual(value['bytes'], len(pixels))

    def test_cross_workspace_and_arbitrary_files_rejected(self):
        (self.folder / 'capture.png').write_bytes(b'pixels')
        (self.folder / 'secret.key').write_text('private')
        for changes in [{'workspace': str(self.other), 'name': 'capture.png'},
                        {'name': '../state.sqlite'}, {'name': 'owner.json'}, {'name': 'secret.key'}]:
            with self.assertRaises(ValueError): read(self.store, {**self.args, **changes})
        self.assertEqual(read(self.store, self.args)['files'], ['capture.png'])

    def test_symlink_and_oversize_rejected(self):
        outside = self.root / 'outside.png'; outside.write_bytes(b'private')
        (self.folder / 'escape.png').symlink_to(outside)
        (self.folder / 'large.webm').write_bytes(b'0' * (8 * 1024 * 1024 + 1))
        for name in ['escape.png', 'large.webm']:
            with self.assertRaises(ValueError): read(self.store, {**self.args, 'name': name})

    def test_job_and_verification_use_actual_scope(self):
        self.store.put('job', self.key, {'workspace': str(self.other)})
        self.store.put('verification', 'receipt', {'workspace': str(self.other), 'state': 'PASS'})
        for kind, key in [('job', self.key), ('verification', 'receipt')]:
            with self.assertRaises(ValueError): read(self.store, {**self.args, 'kind': kind, 'id': key})
        self.store.put('verification', 'receipt', {'workspace': str(self.scope), 'state': 'PASS'})
        self.assertEqual(json.loads(content(read(self.store, {**self.args, 'kind': 'verification', 'id': 'receipt'}))[0]['text'])['state'], 'PASS')

    def test_local_context_returns_original_instructions(self):
        params = {'name': 'pstack_context', 'arguments': {'action': 'get', 'data': {'workspace': str(self.scope), 'playbook': 'feature'}}}
        args = {**params['arguments']['data'], 'include_content': True}
        value = context(self.store, args, 'get')
        self.assertEqual(value['playbook_text'], Path(value['playbook_path']).read_text())
        self.assertEqual(value['adapter_contract_text'], Path(value['adapter_contract']).read_text())
        self.assertIsInstance(value['leaf_principles'], dict)


if __name__ == '__main__':
    unittest.main()
