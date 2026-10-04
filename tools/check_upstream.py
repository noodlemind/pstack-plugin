"""Verify archived originals and corresponding unchanged component licenses."""
from pathlib import Path
import argparse
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/pstack'
sys.path.insert(0, str(PLUGIN/'runtime'))
from upstream_sync import mapped


def check(plugin=PLUGIN):
    inventory = json.loads((plugin/'references/upstream-inventory.json').read_text())
    lock = json.loads((plugin/'UPSTREAM.lock.json').read_text())
    assert inventory['commit'] == lock['commit'], 'Inventory and pin differ'
    original_version = json.loads((plugin/'upstream/pstack/.cursor-plugin/plugin.json').read_text())['version']
    assert lock['pstack_version'] == inventory['pstack_version'] == original_version, 'Upstream versions disagree'
    version = json.loads((plugin/'plugin.json').read_text())['version']
    assert version.startswith(original_version + '-openai.'), 'Adapter version does not match upstream pin'
    for relative in ['.codex-plugin/plugin.json', 'runtime/package.json', 'runtime/package-lock.json']:
        meta = json.loads((plugin/relative).read_text())
        assert meta['version'] == version, f'{relative}: version differs from plugin.json'
        if 'packages' in meta:
            assert meta['packages']['']['version'] == version, f'{relative}: root package version differs'
    for row in inventory['files']:
        path = (plugin/'upstream'/row['path']).resolve()
        assert path.is_relative_to((plugin/'upstream').resolve()), 'Unsafe upstream path'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['path']
        target = mapped(row['path'])
        if target and target.startswith('skills/'):
            assert (plugin/target).is_file(), f'Missing adapted skill file: {target}'
    actual = {str(p.relative_to(plugin/'upstream')) for p in (plugin/'upstream').rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'node_modules' not in p.parts}
    assert actual == {row['path'] for row in inventory['files']}, 'Original file inventory drifted'
    assert (plugin/'LICENSE').read_bytes() == (plugin/'upstream/pstack/LICENSE').read_bytes()
    assert (plugin/'LICENSE.cursor-team-kit').read_bytes() == (plugin/'upstream/cursor-team-kit/LICENSE').read_bytes()
    return {'upstream_commit':lock['commit'],'adapter_version':version,'original_files_verified':len(actual),'installed_skills':len(list((plugin/'skills').glob('*/SKILL.md'))),'original_licenses_unchanged':True}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plugin-root', type=Path, default=PLUGIN)
    print(json.dumps(check(parser.parse_args().plugin_root)))


if __name__ == '__main__':
    main()
