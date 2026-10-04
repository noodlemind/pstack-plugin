import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))
import harnesses
import install
import providers
import pstack
import xai_worker
from api import API
from engine import Engine
from hooks_test import hook_for_test
from store import Store


class HarnessTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.store = Store(self.root / 'state')
        self.repo = self.root / 'repo'
        self.repo.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def cli(self):
        with patch('harnesses.shutil.which', return_value='/verified/cli'):
            return harnesses.setup(self.store, 'local', 'local-cli', ['codex', 'claude'], 'explicit test choice')

    def test_scan_does_not_run_harnesses_or_read_credentials(self):
        with patch('harnesses.shutil.which', side_effect=lambda x: '/bin/' + x), \
             patch('subprocess.Popen', side_effect=AssertionError('execution')), \
             patch('providers.credential', side_effect=AssertionError('credential read')):
            result = providers.discover(self.store)
        self.assertEqual(len(result['harnesses']), 8)
        self.assertFalse(result['remote_access'])
        self.assertTrue(all(not h['enabled'] for h in result['harnesses']))

    def test_native_setup_persists_without_daemon(self):
        with patch.dict(os.environ, {'PSTACK_DATA': str(self.store.home)}), \
             patch('subprocess.Popen', side_effect=AssertionError('daemon')):
            pstack.call('pstack_environment', 'setup', {'host': 'local'})
            result = pstack.call('pstack_environment', 'scan', {})
        self.assertEqual(result['execution']['mode'], 'native')
        self.assertEqual(Store(self.store.home).get('config', 'execution')['host'], 'local')
        self.assertFalse((self.store.home / 'supervisor.json').exists())

    def test_native_agent_call_does_not_start_daemon(self):
        with patch.dict(os.environ, {'PSTACK_DATA': str(self.store.home)}), \
             patch('subprocess.Popen', side_effect=AssertionError('daemon')):
            with self.assertRaisesRegex(ValueError, 'native agents'):
                pstack.call('pstack_agent', 'spawn', {'workspace': str(self.repo), 'prompt': 'review'})

    def test_optional_adapter_requires_choice_and_installed_tool(self):
        with self.assertRaises(ValueError):
            harnesses.setup(self.store, 'local', 'local-cli', ['claude'])
        with patch('harnesses.shutil.which', return_value=None), self.assertRaises(ValueError):
            harnesses.setup(self.store, 'local', 'local-cli', ['claude'], 'choice')

    def test_detected_unsupported_adapter_cannot_be_enabled(self):
        with patch('harnesses.shutil.which', return_value='/bin/opencode'), self.assertRaises(ValueError):
            harnesses.setup(self.store, 'local', 'local-cli', ['opencode'], 'choice')

    def test_only_selected_harness_is_allowed(self):
        self.cli()
        with patch('harnesses.shutil.which', return_value='/bin/codex'):
            harnesses.require_cli(self.store, 'codex')
            with self.assertRaises(ValueError):
                harnesses.require_cli(self.store, 'grok')

    def test_cloud_rejects_cli_setup_and_copied_local_configuration(self):
        self.cli()
        with patch.dict(os.environ, {'PSTACK_EXECUTION_HOST': 'cloud'}):
            self.assertEqual(harnesses.settings(self.store)['mode'], 'native')
            with self.assertRaises(ValueError):
                harnesses.require_cli(self.store, 'codex')
            with self.assertRaises(ValueError):
                harnesses.setup(self.store, 'local', 'local-cli', ['claude'], 'old choice')

    def test_persisted_cloud_profile_rejects_local_cli(self):
        harnesses.setup(self.store, 'cloud')
        with self.assertRaises(ValueError):
            harnesses.require_cli(Store(self.store.home), 'claude')

    def test_local_consent_does_not_transfer_to_another_machine(self):
        self.cli()
        with patch('harnesses.fingerprint', return_value='other-machine'):
            self.assertEqual(harnesses.settings(self.store)['enabled_cli'], [])
            with self.assertRaises(ValueError):
                harnesses.require_cli(self.store, 'codex')

    def test_probe_cannot_run_in_native_mode(self):
        with patch('providers.capture', side_effect=AssertionError('provider invoked')):
            with self.assertRaises(ValueError):
                providers.probe(self.store, 'claude', 'unverified', 'max')

    def test_future_api_cannot_be_activated_by_an_existing_key_or_direct_call(self):
        with patch.dict(os.environ, {'XAI_API_KEY': 'fixture-not-a-real-key'}), \
             patch('pathlib.Path.read_text', side_effect=AssertionError('credential read')), \
             patch('urllib.request.urlopen', side_effect=AssertionError('network request')):
            self.assertIsNone(xai_worker.credential(required=False))
            with self.assertRaisesRegex(ValueError, 'API providers are disabled'):
                xai_worker.api_request('models')
            with self.assertRaisesRegex(ValueError, 'API providers are disabled'):
                xai_worker.run('unverified-model', 'max', 'must not run')

    def test_cloud_restart_does_not_resume_a_stale_local_loop(self):
        harnesses.setup(self.store, 'cloud')
        self.store.put('loop', 'old-local-loop', {'id': 'old-local-loop', 'workspace': str(self.repo), 'state': 'running'})
        with patch('engine.threading.Thread.start', side_effect=AssertionError('local work resumed')):
            engine = Engine(self.store)
        engine.owner_lock.close()
        self.assertEqual(self.store.get('loop', 'old-local-loop')['state'], 'blocked')

    def test_native_stop_hook_does_not_execute_a_legacy_predicate(self):
        self.store.put('foreground', 'old', {'id': 'old', 'workspace': str(self.repo), 'session': 'fixture', 'state': 'running'}, str(self.repo))
        with patch('lifecycle.execute', side_effect=AssertionError('predicate executed')):
            result = hook_for_test(self.store, {'cwd': str(self.repo), 'session_id': 'fixture', 'hook_event_name': 'Stop'})
        self.assertEqual(result, {})

    def test_native_plan_uses_only_host_models_and_supported_efforts(self):
        harnesses.setup(self.store, 'cloud')
        self.store.put('config', 'models', {'budget': 'unlimited', 'roles': {'review': [
            {'family': 'anthropic', 'model': 'saved-claude'}, {'family': 'openai', 'model': 'host-b'}]}})
        harnesses.catalog(self.store, [{'provider': 'openai', 'model': 'host-a', 'efforts': ['high']},
                                      {'provider': 'openai', 'model': 'host-b', 'efforts': ['medium', 'max']}], 'isolated fixture host catalog')
        plan = harnesses.native_plan(self.store, 'review', 3, True)
        self.assertEqual([s['model'] for s in plan['seats']], ['host-b', 'host-a', 'host-b'])
        self.assertEqual([s['effort'] for s in plan['seats']], ['max', 'high', 'max'])
        self.assertEqual(plan['distinct_models'], 2)
        self.assertFalse(plan['cross_provider_requirement_met'])
        self.assertEqual(plan['state'], 'planned')

    def test_unknown_host_model_is_not_invented(self):
        harnesses.budget(self.store, 'medium', 'explicit fixture choice')
        plan = harnesses.native_plan(self.store, 'review', 3)
        self.assertTrue(all(s['model'] is None and s['effort'] is None for s in plan['seats']))
        self.assertEqual(plan['distinct_models'], 0)
        self.assertTrue(plan['limitations'])

    def test_local_catalog_does_not_transfer_to_cloud(self):
        harnesses.budget(self.store, 'medium', 'explicit fixture choice')
        harnesses.setup(self.store, 'local')
        harnesses.catalog(self.store, [{'provider': 'openai', 'model': 'local-only', 'efforts': []}], 'fixture')
        with patch.dict(os.environ, {'PSTACK_EXECUTION_HOST': 'cloud'}):
            self.assertIsNone(harnesses.native_plan(self.store, 'review')['seats'][0]['model'])

    def test_native_catalog_rejects_external_provider(self):
        with self.assertRaises(ValueError):
            harnesses.catalog(self.store, [{'provider': 'anthropic', 'model': 'claude'}], 'fixture')

    def test_native_budget_and_roles_persist_without_touching_legacy_choices(self):
        original = {'budget': 'unlimited', 'roles': {'review': [{'family': 'anthropic', 'model': 'saved'}]}}
        self.store.put('config', 'models', original)
        harnesses.catalog(self.store, [{'provider': 'openai', 'model': 'host-a', 'efforts': ['medium', 'max']}], 'fixture')
        harnesses.budget(self.store, 'small', 'explicit fixture choice')
        roles = {role: ['host-a'] for role in providers.ROLES}
        roles['interrogate reviewers'] = ['host-a', 'host-a', 'host-a']
        API(self.store).call('pstack_environment', 'configure', {'roles': roles, 'confirmation': 'explicit fixture roles'})
        reopened = Store(self.store.home)
        plan = harnesses.native_plan(reopened, 'interrogate reviewers')
        self.assertEqual(len(plan['seats']), 3)
        self.assertTrue(all(s['effort'] == 'medium' for s in plan['seats']))
        self.assertEqual(plan['distinct_models'], 1)
        self.assertEqual(reopened.get('config', 'models'), original)

    def test_retired_native_model_never_silently_falls_back(self):
        harnesses.budget(self.store, 'medium', 'explicit fixture choice')
        harnesses.catalog(self.store, [{'provider': 'openai', 'model': 'host-a', 'efforts': []}], 'fixture')
        roles = {role: ['host-a'] for role in providers.ROLES}
        API(self.store).call('pstack_environment', 'configure', {'roles': roles, 'confirmation': 'fixture'})
        harnesses.catalog(self.store, [{'provider': 'openai', 'model': 'host-b', 'efforts': []}], 'changed fixture')
        with self.assertRaisesRegex(ValueError, 'no longer advertised'):
            harnesses.native_plan(self.store, 'swarm workers')

    def test_missing_native_budget_confirmation_rejected(self):
        with self.assertRaises(ValueError):
            harnesses.budget(self.store, 'small', '')

    def test_fresh_setup_never_selects_a_budget_or_dispatches_work(self):
        result = harnesses.setup(self.store, 'local')
        self.assertIsNone(result['preferences']['budget'])
        self.assertTrue(result['preferences']['requires_budget_choice'])
        self.assertIsNone(result['preferences']['reasoning_target'])
        self.assertEqual(result['preferences']['budget_options'], harnesses.BUDGETS)
        with self.assertRaisesRegex(ValueError, 'Choose a reasoning budget'):
            harnesses.native_plan(self.store, 'swarm workers')

    def test_every_budget_is_explicit_persistent_and_reconfigurable(self):
        harnesses.setup(self.store, 'local')
        harnesses.catalog(self.store, [{'provider': 'openai', 'model': 'host-model', 'efforts': list(harnesses.BUDGETS.values())}], 'fixture host')
        for choice, effort in harnesses.BUDGETS.items():
            with self.subTest(choice=choice):
                harnesses.budget(self.store, choice, 'explicit fixture change')
                reopened = Store(self.store.home)
                self.assertEqual(harnesses.setup(reopened, 'local')['preferences']['budget'], choice)
                self.assertEqual(harnesses.native_plan(reopened, 'coding')['seats'][0]['effort'], effort)

    def test_native_budget_readback_overrides_legacy_budget_without_rewriting_it(self):
        self.store.put('config', 'models', {'budget': 'unlimited', 'roles': {}})
        harnesses.budget(self.store, 'small', 'explicit fixture change')
        result = API(self.store).call('pstack_environment', 'preferences', {})
        self.assertEqual(result['budget'], 'small')
        self.assertEqual(self.store.get('config', 'models')['budget'], 'unlimited')

    def test_one_users_budget_does_not_seed_a_different_state_store(self):
        harnesses.budget(self.store, 'unlimited', 'explicit fixture choice')
        another = Store(self.root / 'another-user')
        self.assertTrue(harnesses.setup(another)['preferences']['requires_budget_choice'])
        self.assertIsNone(harnesses.preferences(another)['budget'])

    def test_native_recovery_records_are_scoped_and_not_fabricated_execution(self):
        with self.assertRaises(ValueError):
            harnesses.native_record(self.store, {'workspace': str(self.repo), 'native_id': 'real-host-id', 'state': 'completed'})
        row = harnesses.native_record(self.store, {'workspace': str(self.repo), 'native_id': 'fixture-host-id', 'state': 'interrupted', 'next_steps': 'verify files'})
        recovered = API(Store(self.store.home)).call('pstack_checkpoint', 'recover', {'workspace': str(self.repo)})
        self.assertEqual(recovered['native_jobs'][0]['id'], row['id'])
        self.assertIn('recorded by coordinator', row['origin'])
        other = self.root / 'other'; other.mkdir()
        self.assertEqual(API(self.store).call('pstack_checkpoint', 'recover', {'workspace': str(other)})['native_jobs'], [])

    def test_retirement_removes_only_the_expected_owned_file(self):
        source = self.root / 'source'; source.mkdir()
        target = self.root / 'installed'; target.mkdir()
        backup = self.root / 'backup'; backup.mkdir()
        (target / 'remote.py').write_text('old relay')
        (target / 'personal.txt').write_text('preserve')
        (source / 'RETIRED-FILES.json').write_text(json.dumps({'files': [{'path': 'remote.py', 'sha256': hashlib.sha256(b'old relay').hexdigest()}]}))
        install.sync_source(source, target, backup)
        self.assertFalse((target / 'remote.py').exists())
        self.assertEqual((target / 'personal.txt').read_text(), 'preserve')

    def test_retirement_rejects_changed_file(self):
        source = self.root / 'source'; source.mkdir()
        target = self.root / 'installed'; target.mkdir()
        backup = self.root / 'backup'; backup.mkdir()
        (target / 'remote.py').write_text('user edit')
        (source / 'RETIRED-FILES.json').write_text(json.dumps({'files': [{'path': 'remote.py', 'sha256': hashlib.sha256(b'old relay').hexdigest()}]}))
        with self.assertRaises(ValueError):
            install.sync_source(source, target, backup)
        self.assertEqual((target / 'remote.py').read_text(), 'user edit')


if __name__ == '__main__':
    unittest.main()
