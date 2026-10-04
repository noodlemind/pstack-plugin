"""Verify archived originals and corresponding unchanged component licenses."""
from pathlib import Path
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / 'plugins/pstack'


def main():
    inventory = json.loads((PLUGIN/'references/upstream-inventory.json').read_text())
    lock = json.loads((PLUGIN/'UPSTREAM.lock.json').read_text())
    assert inventory['commit'] == lock['commit'], 'Inventory and pin differ'
    for row in inventory['files']:
        path = (PLUGIN/'upstream'/row['path']).resolve()
        assert path.is_relative_to((PLUGIN/'upstream').resolve()), 'Unsafe upstream path'
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], row['path']
    actual = {str(p.relative_to(PLUGIN/'upstream')) for p in (PLUGIN/'upstream').rglob('*') if p.is_file() and '__pycache__' not in p.parts and 'node_modules' not in p.parts}
    assert actual == {row['path'] for row in inventory['files']}, 'Original file inventory drifted'
    assert (PLUGIN/'LICENSE').read_bytes() == (PLUGIN/'upstream/pstack/LICENSE').read_bytes()
    assert (PLUGIN/'LICENSE.cursor-team-kit').read_bytes() == (PLUGIN/'upstream/cursor-team-kit/LICENSE').read_bytes()
    print(json.dumps({'upstream_commit':lock['commit'],'original_files_verified':len(actual),'original_licenses_unchanged':True}))


if __name__ == '__main__':
    main()
