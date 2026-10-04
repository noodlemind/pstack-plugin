from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from check_upstream import PLUGIN, check


class ReleaseChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.plugin = Path(self.temp.name)/'plugin'
        shutil.copytree(PLUGIN, self.plugin, ignore=shutil.ignore_patterns('node_modules', '__pycache__'))

    def test_missing_new_skill_fails_even_with_intact_archive(self):
        (self.plugin/'skills/correct/SKILL.md').unlink()
        with self.assertRaisesRegex(AssertionError, 'Missing adapted skill file: skills/correct'):
            check(self.plugin)

    def test_stale_package_version_fails(self):
        path = self.plugin/'runtime/package.json'
        data = json.loads(path.read_text())
        data['version'] = '0.15.5-openai.7'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(AssertionError, 'runtime/package.json: version differs'):
            check(self.plugin)

    def test_wrong_pin_version_fails(self):
        path = self.plugin/'UPSTREAM.lock.json'
        data = json.loads(path.read_text())
        data['pstack_version'] = '0.15.5'
        path.write_text(json.dumps(data))
        with self.assertRaisesRegex(AssertionError, 'Upstream versions disagree'):
            check(self.plugin)

    def test_hourly_plan_passes_and_old_cadence_fails(self):
        template = (self.plugin/'skills/poteto-mode/playbooks/multi-phase-plan.md').read_text()
        plan = template.split('````markdown\n', 1)[1].split('\n````', 1)[0]
        plan = plan.replace('<swarm workers model>', 'fixture-model')
        path = Path(self.temp.name)/'plan.md'
        script = self.plugin/'skills/poteto-mode/scripts/check-plan.mjs'
        path.write_text(plan)
        passed = subprocess.run(['node', str(script), str(path)], capture_output=True, text=True)
        self.assertEqual(passed.returncode, 0, passed.stderr)
        path.write_text(plan.replace('/loop 1h', '/goal with a 30-minute audit'))
        failed = subprocess.run(['node', str(script), str(path)], capture_output=True, text=True)
        self.assertNotEqual(failed.returncode, 0)
        self.assertIn('Program checklist lacks "/loop 1h"', failed.stderr)


if __name__ == '__main__':
    unittest.main()
