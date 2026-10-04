"""Audit the exact Git index; never print matched sensitive values.

This supplements human review and provider secret scanning. It is deliberately
conservative about runtime artifacts; it is not an exhaustive PII classifier.
"""
from pathlib import Path, PurePosixPath
import argparse
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
SECRET_PATTERNS = {
    'private-key': rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----',
    'provider-token': rb'(?<![A-Za-z0-9])(?:sk-(?:proj-|ant-)?[A-Za-z0-9_-]{30,}|xai-[A-Za-z0-9_-]{40,})',
    'github-token': rb'(?<![A-Za-z0-9])(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{35,})',
    'cloud-access-key': rb'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b',
    'literal-auth-secret': rb'"(?:access_token|refresh_token|client_secret|api_key)"\s*:\s*"[A-Za-z0-9_./+=-]{20,}"',
    'literal-bearer': rb'Bearer [A-Za-z0-9_.-]{30,}',
    'personal-home-path': rb'/(?:Users|home)/(?!you(?:/|\b)|user(?:/|\b)|example(?:/|\b)|<)[A-Za-z0-9_.-]+/',
    'host-account-receipt': rb'"(?:thread_id|session_id|client_id|source_channel|triage_identity)"\s*:\s*"(?:[0-9a-f]{8}-[0-9a-f-]{27,}|[CU][A-Z0-9]{9,})"',
    'personal-deployment-origin': rb'https://[a-z0-9-]+\.up\.railway\.app',
}
EMAIL = re.compile(rb'(?<![A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})')
FORBIDDEN_PARTS = {'node_modules','__pycache__','credentials','evidence','current-evidence','install-backups','.pstack-state','.pstack-data'}
FORBIDDEN_SUFFIXES = {'.key','.pem','.p12','.pfx','.sqlite','.db','.jsonl','.log','.har','.webm','.mp4','.zip','.pyc'}


def inspect_file(name: str, body: bytes, mode: str = '100644') -> list[str]:
    path = PurePosixPath(name)
    findings = []
    if mode not in {'100644','100755'}:
        findings.append('non-regular-index-entry')
    if any(p in FORBIDDEN_PARTS for p in path.parts) or path.suffix in FORBIDDEN_SUFFIXES or '.sqlite-' in path.name:
        findings.append('private-or-generated-artifact')
    if path.name.startswith('.env') and path.name != '.env.example':
        findings.append('environment-file')
    if name.endswith('.codex/config.toml') or path.name in {'auth.json','supervisor.json','tunnel.json','tunnel.key'}:
        findings.append('personal-runtime-configuration')
    for rule, pattern in SECRET_PATTERNS.items():
        if re.search(pattern, body):
            findings.append(rule)
    for match in EMAIL.finditer(body):
        domain = match.group(1).lower()
        if match.group(0) == b'git@github.com' or domain in {b'example.com',b'example.org',b'example.net'} or domain.endswith(b'.example'):
            continue
        findings.append('non-example-email')
        break
    return findings


def audit(root: Path) -> dict:
    entries = subprocess.check_output(['git','ls-files','--stage','-z'],cwd=root).split(b'\0')
    findings = []
    count = 0
    for entry in entries:
        if not entry:
            continue
        header, raw_path = entry.split(b'\t',1)
        mode, oid, stage = header.decode().split()
        name = raw_path.decode('utf-8')
        if stage != '0':
            findings.append({'path':name,'rules':['unmerged-index-entry']})
            continue
        body = subprocess.check_output(['git','cat-file','blob',oid],cwd=root)
        rules = inspect_file(name,body,mode)
        if rules:
            findings.append({'path':name,'rules':rules})
        count += 1
    return {'scope':'exact Git index','files_checked':count,'findings':findings,
            'limits':'Pattern checks supplement manual review; no matched values are printed.'}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--repo',type=Path,default=ROOT)
    args = parser.parse_args()
    report = audit(args.repo)
    print(json.dumps(report,indent=2))
    return 1 if report['findings'] or report['files_checked'] == 0 else 0


if __name__ == '__main__':
    sys.exit(main())
