import contextlib
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import install


class InstallerRollbackTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        self.home = root / 'user'
        self.profile = root / 'codex-profile'
        self.source = root / 'package'
        self.source.mkdir()
        self.target = self.home / '.codex/plugins/pstack'
        self.cache = self.profile / 'plugins/cache/personal/pstack'
        self.market = self.home / '.agents/plugins/marketplace.json'
        self.config = self.profile / 'config.toml'
        self.hooks = self.profile / 'hooks.json'
        self.bridge = self.profile / 'hooks/pstack-bridge.py'
        self.set_release('1.0')
        self.write(self.source/'PORT.lock.json', '{"adapter":"pstack-openai-personal"}')
        self.write(self.source/'hooks/bridge.py', '# PSTACK_OWNED_NATIVE_HOOK_BRIDGE_V1\n')
        self.write(self.source/'hooks/hooks.json', '{"hooks":{}}')
        self.fail_at = None

    @staticmethod
    def write(path, value):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(value)

    def set_release(self, version):
        self.write(self.source/'plugin.json', json.dumps({'version': version}))
        self.write(self.source/'UPSTREAM.lock.json', json.dumps({'commit': version}))
        self.write(self.source/'UPDATE-REVIEW.json', json.dumps({
            'commit': version, 'resolved_conflicts': ['fixture'], 'behavior_review': ['fixture'],
            'installed_workflow_evidence': ['fixture']
        }))

    def codex_cli(self, args, check):
        self.assertTrue(check)
        version = json.loads((self.target/'plugin.json').read_text())['version']
        self.write(self.config, 'current = "' + version + '"\n')
        step = 'marketplace' if args[2] == 'marketplace' else 'plugin'
        if step == 'plugin':
            if self.cache.exists():
                shutil.rmtree(self.cache)
            shutil.copytree(self.target, self.cache/version)
        if self.fail_at == step:
            raise subprocess.CalledProcessError(1, args)

    def read_plugin(self, method, params):
        if self.fail_at == 'read':
            raise RuntimeError('synthetic RPC failure')
        return {'plugin': {'hooks': []}}

    def run_install(self):
        with patch.dict(os.environ, {'CODEX_HOME': str(self.profile)}), \
                patch.object(install.subprocess, 'run', side_effect=self.codex_cli), \
                patch.object(install, 'codex_rpc', side_effect=self.read_plugin), \
                contextlib.redirect_stdout(io.StringIO()):
            install.install(self.source, self.home)

    def test_failed_upgrade_restores_previous_release_and_can_retry(self):
        self.run_install()
        self.write(self.target/'personal.txt', 'preserve')
        settings = [self.market, self.config, self.hooks, self.bridge]
        before = {path: path.read_bytes() for path in settings}
        self.set_release('2.0')
        for step in ('marketplace', 'plugin', 'read', 'hooks'):
            with self.subTest(step=step):
                self.fail_at = step
                if step == 'hooks':
                    self.write(self.source/'hooks/bridge.py', '# PSTACK_OWNED_NATIVE_HOOK_BRIDGE_V1\n# new\n')
                    self.write(self.source/'hooks/hooks.json', 'invalid JSON')
                with self.assertRaisesRegex(RuntimeError, 'Restored local source'):
                    self.run_install()
                self.assertEqual(json.loads((self.target/'plugin.json').read_text())['version'], '1.0')
                self.assertEqual((self.target/'personal.txt').read_text(), 'preserve')
                self.assertEqual({path: path.read_bytes() for path in settings}, before)
                self.assertEqual({p.name for p in self.cache.iterdir()}, {'1.0'})
                self.assertEqual((self.cache/'1.0/plugin.json').read_bytes(), (self.target/'plugin.json').read_bytes())
        self.write(self.source/'hooks/hooks.json', '{"hooks":{}}')
        self.fail_at = None
        self.run_install()
        self.assertEqual(json.loads((self.target/'plugin.json').read_text())['version'], '2.0')
        self.assertTrue((self.cache/'2.0/plugin.json').is_file())
        self.assertEqual((self.target/'personal.txt').read_text(), 'preserve')

    def test_failed_first_install_restores_absent_files_and_keeps_unrelated_marketplace_entry(self):
        original = '{"name":"personal","plugins":[{"name":"fixture-other"}]}'
        self.write(self.market, original)
        self.fail_at = 'read'
        with self.assertRaisesRegex(RuntimeError, 'Restored local source'):
            self.run_install()
        self.assertEqual(self.market.read_text(), original)
        for path in (self.target, self.config, self.hooks, self.bridge, self.cache):
            self.assertFalse(path.exists(), path)
        self.fail_at = None
        self.run_install()
        self.assertEqual([plugin['name'] for plugin in json.loads(self.market.read_text())['plugins']],
                         ['fixture-other', 'pstack'])
