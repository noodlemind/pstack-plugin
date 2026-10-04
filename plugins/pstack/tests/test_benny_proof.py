import json
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'runtime'))

from api import API
import benny
import harnesses
from providers import ROLES, configure
from store import Store


class BennyProofTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='pstack-benny-proof-')
        self.root = Path(self.tmp.name).resolve(); self.repo = self.root / 'repo'; self.repo.mkdir()
        subprocess.run(['git', 'init', '-q', str(self.repo)], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'config', 'user.email', 'fixture@localhost'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'config', 'user.name', 'fixture'], check=True)
        (self.repo / 'feature-map.md').write_text('Click the count button and inspect its value.')
        (self.repo / 'config.json').write_text('{}')
        (self.repo / '.codex').mkdir()
        (self.repo / '.codex/config.toml').write_text('[plugins."pstack@fixture"]\nenabled=true\n')
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'commit', '-qm', 'fixture'], check=True)
        self.store = Store(self.root / 'data'); self.api = API(self.store)
        self.store.put('config', 'execution', {'host': 'local', 'mode': 'local-cli', 'enabled_cli': ['codex'], 'machine': harnesses.fingerprint()})
        model = {'key': 'codex:fixture', 'provider': 'codex', 'model': 'fixture', 'family': 'openai', 'verified': True, 'efforts': ['max']}
        self.store.put('model', model['key'], model)
        configure(self.store, 'unlimited', {r: [model['key']] for r in ROLES}, 'isolated guard fixture')
        cfg = {'repository': 'fixture', 'default_branch': 'main', 'source_channel': 'FIXTURE', 'triage_identity': 'TRIAGE', 'tracker': 'fixture',
               'control_skill': 'control-ui', 'control_url': 'http://fixture.invalid/', 'feature_map': 'feature-map.md',
               'models': {r: model['key'] for r in benny.MODEL_ROLES}, 'budgets': {b: 1 for b in benny.BUDGET_FIELDS}}
        benny.setup(self.store, {'workspace': str(self.repo), 'config': cfg})
        self.run = benny.ingest(self.store, {'workspace': str(self.repo), 'event': {'channel': 'FIXTURE', 'ts': '123'}, 'parent_preflight': True, 'tracker_preflight': True})
        self.set_run(state='reproduce')

    def tearDown(self):
        self.api.engine.owner_lock.close(); self.tmp.cleanup()

    def set_run(self, **changes):
        self.run = self.store.put('benny_run', self.run['id'], {**self.run, **changes}, str(self.repo))

    def capture(self, number, phase='baseline'):
        ident = format(number, '032x'); folder = self.store.home / 'controls' / ident; folder.mkdir(parents=True)
        # Deliberately synthetic artifacts: these tests establish guards only.
        for name in ['screenshot.png', 'video.webm', 'trace.zip']: (folder / name).write_bytes(b'guard fixture')
        (folder / 'owner.json').write_text(json.dumps({'workspace': str(self.repo)}))
        actions = [{'action': 'start', 'result': {'url': 'http://fixture.invalid/'}},
                   {'action': 'click', 'result': {'tree': 'Count: 0' if phase == 'baseline' else 'Count: 1', 'screenshot': str(folder / 'screenshot.png')}},
                   {'action': 'inspect', 'result': {'values': [{'text': '0' if phase == 'baseline' else '1'}]}},
                   {'action': 'stop', 'result': {'video': str(folder / 'video.webm'), 'trace': str(folder / 'trace.zip')}}]
        (folder / 'actions.jsonl').write_text('\n'.join(json.dumps(a) for a in actions))
        return benny.evidence(self.store, {'id': self.run['id'], 'phase': phase, 'control_id': ident, 'expected': 'Count: 1', 'broken': 'Count: 0'})

    def test_two_distinct_recordings_required_and_duplicate_is_idempotent(self):
        one = self.capture(1)
        with self.assertRaises(ValueError): benny.captures(self.store, self.run, 'baseline')
        got = benny.evidence(self.store, {'id': self.run['id'], 'phase': 'baseline', 'control_id': one['control_id'], 'expected': 'Count: 1', 'broken': 'Count: 0'})
        self.assertEqual(got['id'], one['id']); self.capture(2)
        self.assertEqual(len(benny.captures(self.store, self.run, 'baseline')), 2)

    def test_capture_bytes_cannot_change_after_recording(self):
        one = self.capture(1); self.capture(2)
        Path(one['screenshot']).write_bytes(b'changed')
        with self.assertRaises(ValueError): benny.captures(self.store, self.run, 'baseline')

    def test_wrong_scope_and_missing_recording_block_evidence(self):
        one = self.capture(1); folder = Path(one['screenshot']).parent
        (folder / 'owner.json').write_text(json.dumps({'workspace': '/another'}))
        with self.assertRaises(ValueError): benny.evidence(self.store, {'id': self.run['id'], 'phase': 'baseline', 'control_id': one['control_id'], 'expected': 'Count: 1', 'broken': 'Count: 0'})

    def test_code_cannot_launch_before_repro_or_after_cancellation(self):
        for state in ['reproduce', 'cancelled', 'fixing']:
            self.set_run(state=state)
            with self.assertRaises(ValueError): benny.launch(self.store, {'id': self.run['id'], 'role': 'code', 'prompt': 'never run'}, self.api.engine)
        self.assertEqual(self.store.list('job'), [])

    def test_fake_media_verdict_without_native_images_is_rejected(self):
        one = self.capture(1); two = self.capture(2)
        self.store.put('job', 'fake', {'id': 'fake', 'state': 'completed', 'readonly': True, 'result': {'text': json.dumps({'benny_media_verdict': 'CONFIRMED', 'evidence_ids': [one['id'], two['id']], 'observation': 'fake'})}})
        self.set_run(media_review_job='fake')
        with self.assertRaises(ValueError): benny.confirm_repro(self.store, {'id': self.run['id']})

    def test_rejection_window_existing_fix_and_single_attempt(self):
        self.capture(1); self.capture(2); self.set_run(state='repro_confirmed', rejection_deadline=time.time() + 60)
        with self.assertRaises(ValueError): benny.fix_gate(self.store, {'id': self.run['id'], 'parent_preflight': True, 'root_cause_evidence': 'missing'})
        held = benny.fix_gate(self.store, {'id': self.run['id'], 'existing_fix': 'https://github.com/fixture/repo/pull/1'})
        self.assertEqual(held['state'], 'verify_existing_fix')
        self.set_run(state='repro_confirmed', fix_attempts=1)
        with self.assertRaises(ValueError): benny.fix_gate(self.store, {'id': self.run['id']})

    def test_one_correction_invalidates_prior_proof(self):
        self.capture(1); self.capture(2); self.set_run(state='blocked')
        corrected = benny.reconsider(self.store, {'id': self.run['id'], 'reason': 'wrong fixture state'})
        with self.assertRaises(ValueError): benny.captures(self.store, corrected, 'baseline')
        with self.assertRaises(ValueError): benny.reconsider(self.store, {'id': self.run['id'], 'reason': 'again'})

    def test_native_schedule_plan_requires_committed_operational_files(self):
        with self.assertRaises(ValueError): benny.plan(self.store, {'workspace': str(self.repo), 'configuration_path': 'config.json'})
        subprocess.run(['git', '-C', str(self.repo), 'add', '.'], check=True)
        subprocess.run(['git', '-C', str(self.repo), 'commit', '-qm', 'commit dormant pack'], check=True)
        plan = benny.plan(self.store, {'workspace': str(self.repo), 'configuration_path': 'config.json'})
        self.assertFalse(plan['enabled']); self.assertEqual(len(plan['workflows']), 2)
        self.assertIn('triage-issue-reports/SKILL.md', plan['workflows'][0]['prompt'])

    def test_native_schedule_plan_refuses_disabled_project_plugin(self):
        (self.repo / '.codex/config.toml').write_text('[plugins."pstack@fixture"]\nenabled=false\n')
        with self.assertRaises(ValueError): benny.plan(self.store, {'workspace': str(self.repo), 'configuration_path': 'config.json'})


if __name__ == '__main__':
    unittest.main()
