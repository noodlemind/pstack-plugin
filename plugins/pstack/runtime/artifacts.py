"""Read scoped runtime evidence through MCP, including actual image pixels."""
import base64
import hashlib
import json
import mimetypes
from pathlib import Path
import re

from store import workspace


def read(store, args):
    scope, kind, key = workspace(args['workspace']), args['kind'], args['id']
    if kind == 'verification':
        row = store.get('verification', key)
        if row['workspace'] != scope:
            raise ValueError('verification belongs to another workspace')
        return {'_mcp_content': [{'type': 'text', 'text': json.dumps(row)}]}
    if kind not in {'job', 'control'} or not re.fullmatch(r'[a-f0-9]{32}', key):
        raise ValueError('unknown artifact kind or ID')
    folder = store.home / ('jobs' if kind == 'job' else 'controls') / key
    if kind == 'job':
        if store.get('job', key)['workspace'] != scope:
            raise ValueError('job belongs to another workspace')
        allowed = {'events.jsonl', 'stderr.txt', 'result.json'}
    else:
        if json.loads((folder / 'owner.json').read_text())['workspace'] != scope:
            raise ValueError('control belongs to another workspace')
        allowed = {p.name for p in folder.iterdir() if p.is_file() and p.suffix in {'.png', '.webm', '.zip', '.jsonl', '.txt', '.cpuprofile', '.heapsnapshot'}}
    name = args.get('name')
    if not name:
        return {'id': key, 'kind': kind, 'files': sorted(allowed)}
    if name not in allowed or Path(name).name != name:
        raise ValueError('artifact is outside the owned evidence set')
    target = (folder / name).resolve(strict=True)
    if not target.is_relative_to(folder.resolve()) or not target.is_file() or target.stat().st_size > 8 * 1024 * 1024:
        raise ValueError('artifact is unowned or exceeds 8 MiB')
    data = target.read_bytes()
    mime = mimetypes.guess_type(name)[0] or 'application/octet-stream'
    meta = {'id': key, 'kind': kind, 'name': name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'mimeType': mime}
    blocks = [{'type': 'text', 'text': json.dumps(meta)}]
    if mime in {'image/png', 'image/jpeg', 'image/webp'}:
        blocks.append({'type': 'image', 'mimeType': mime, 'data': base64.b64encode(data).decode()})
    elif target.suffix in {'.json', '.jsonl', '.txt', '.cpuprofile', '.heapsnapshot'}:
        blocks.append({'type': 'text', 'text': data.decode('utf-8')})
    else:
        blocks.append({'type': 'resource', 'resource': {'uri': f'pstack://{kind}/{key}/{name}', 'mimeType': mime, 'blob': base64.b64encode(data).decode()}})
    return {**meta, '_mcp_content': blocks}


def content(value):
    return value['_mcp_content'] if isinstance(value, dict) and '_mcp_content' in value else [{'type': 'text', 'text': json.dumps(value)}]
