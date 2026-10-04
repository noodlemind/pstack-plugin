#!/usr/bin/env python3
# PSTACK_OWNED_NATIVE_HOOK_BRIDGE_V1
"""Compatibility source for hosts that do not discover bundled hooks."""
from pathlib import Path
import json,subprocess,sys,tomllib

def relay(home: Path, payload: str) -> tuple[int,str,str]:
    config=home/'.codex/config.toml'
    source=home/'.codex/plugins/pstack/hooks/lifecycle.py'
    marketplace=home/'.agents/plugins/marketplace.json'
    settings=tomllib.loads(config.read_text()) if config.is_file() else {}
    name=json.loads(marketplace.read_text())['name'] if marketplace.is_file() else 'personal'
    enabled=settings.get('plugins',{}).get('pstack@'+name,{}).get('enabled',False)
    if not enabled or not source.is_file():return 0,'{}\n',''
    p=subprocess.run([sys.executable,str(source)],input=payload,capture_output=True,text=True)
    return p.returncode,p.stdout,p.stderr

if __name__=='__main__':
    try:
        code,output,error=relay(Path.home(),sys.stdin.read())
        sys.stdout.write(output);sys.stderr.write(error);raise SystemExit(code)
    except Exception as e:
        print(json.dumps({'systemMessage':'pstack hook bridge failed: '+str(e)}));raise SystemExit(1)
