from pathlib import Path
import json
import os
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

    def test_missing_companion_asset_fails_even_with_intact_archive(self):
        (self.plugin/'assets/avatar.png').unlink()
        with self.assertRaisesRegex(AssertionError, 'Missing adapted file: assets/avatar.png'):
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

    @unittest.skipUnless(os.name == 'posix', 'Requires POSIX executable permissions')
    def test_launcher_mode_is_verified_in_archive_and_adaptation(self):
        launcher = 'skills/statechart/scripts/statechart'
        for path, message in [(self.plugin/'upstream/pstack'/launcher, 'Upstream file mode differs'),
                              (self.plugin/launcher, 'Adapted skill file must be executable')]:
            with self.subTest(path=path):
                path.chmod(0o644)
                with self.assertRaisesRegex(AssertionError, message):
                    check(self.plugin)
                path.chmod(0o755)

    @unittest.skipUnless(os.name == 'posix', 'The shell launcher is shipped for POSIX hosts')
    def test_statechart_launcher_replays_a_counterexample(self):
        scripts = self.plugin/'skills/statechart/scripts'
        fixture = scripts/'test/corpus/CounterDeadlock'
        output = Path(self.temp.name)/'output'
        env = dict(os.environ, JAVA=str(scripts/'test/java.ts'),
                   TLA2TOOLS='fixture.jar', STATECHART_REPLAY=str(fixture))
        run = subprocess.run(
            [scripts/'statechart', fixture/'CounterDeadlock.tla', '--out', output],
            env=env, capture_output=True, text=True, timeout=60,
        )
        self.assertEqual(run.returncode, 1, run.stderr)
        self.assertEqual(run.stderr, '')
        for artifact in ['chart.mmd', 'report.md']:
            self.assertEqual((output/artifact).read_bytes(), (fixture/artifact).read_bytes())


if __name__ == '__main__':
    unittest.main()
