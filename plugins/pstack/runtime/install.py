#!/usr/bin/env python3
"""Preserving personal marketplace installation through the supported CLI."""
from pathlib import Path
import datetime,hashlib,json,os,shutil,subprocess,tempfile
from providers import codex_rpc

def deletions(source,target):
 plan=source/'.upstream-update/plan.json'
 if not plan.is_file():return []
 rows=[]
 for change in json.loads(plan.read_text())['changes']:
  candidates=[]
  if change['new_original'] is None:candidates.append(('upstream/'+change['upstream_path'],change['old_sha']))
  if change['action']=='delete' and change['target']:candidates.append((change['target'],change['current_sha']))
  for relative,digest in candidates:
   path=(target/relative).resolve()
   if path != target.resolve()/relative or not path.is_relative_to(target.resolve()):raise ValueError('unsafe update deletion')
   if not path.exists():continue
   if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('installed file changed; merge it before update: '+relative)
   rows.append(relative)
 return rows

SKIP_DIRECTORIES = {'__pycache__', '.DS_Store', 'node_modules', '.git', '.upstream-update', 'upstream-history'}


def same_file(left, right):
    return (left.is_file() and right.is_file()
            and left.read_bytes() == right.read_bytes()
            and bool(left.stat().st_mode & 0o111) == bool(right.stat().st_mode & 0o111))


def check_local_edits(source, target, installed):
    # Compare the marketplace source to the last version installed by Codex.
    # A missing cache cannot authorize overwriting different local content.
    for folder, dirs, files in os.walk(source):
        dirs[:] = [name for name in dirs if name not in SKIP_DIRECTORIES]
        for name in files:
            if name in SKIP_DIRECTORIES:
                continue
            incoming = Path(folder) / name
            relative = incoming.relative_to(source)
            current = target / relative
            if current.resolve() != target.resolve() / relative:
                raise ValueError('symlink in installed package path: ' + str(relative))
            baseline = installed / relative
            if same_file(incoming, current):
                continue
            if not current.exists() and not baseline.exists():
                continue
            if not same_file(current, baseline):
                raise ValueError('installed file changed; merge it before update: ' + str(relative))


def sync_source(source,target,backup,installed=None):
 removed=deletions(source,target)
 retirement=source/'RETIRED-FILES.json'
 if retirement.exists():
  for row in json.loads(retirement.read_text())['files']:
   path=(target/row['path']).resolve()
   if path != target.resolve()/row['path'] or not path.is_relative_to(target.resolve()):raise ValueError('unsafe retired path')
   if path.exists():
    expected={row['sha256'],*row.get('previous_sha256', [])}
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() not in expected:raise ValueError('retired file changed; inspect before removing: '+row['path'])
    removed.append(row['path'])
 if target.is_symlink():raise ValueError('refusing a symlinked plugin source')
 if installed is not None:
  check_local_edits(source,target,installed)
  for relative in removed:
   baseline=installed/relative
   if baseline.is_file() and not same_file(target/relative,baseline):raise ValueError('installed file changed; merge it before update: '+relative)
 target.parent.mkdir(parents=True,exist_ok=True)
 staged=Path(tempfile.mkdtemp(prefix='.pstack-install-',dir=target.parent))
 try:
  if target.exists():shutil.copytree(target,staged,dirs_exist_ok=True,symlinks=True)
  for relative in removed:(staged/relative).unlink(missing_ok=True)
  shutil.copytree(source,staged,dirs_exist_ok=True,ignore=shutil.ignore_patterns(*SKIP_DIRECTORIES))
  if target.exists():os.replace(target,backup/'plugin-source')
  try:os.replace(staged,target)
  except BaseException:
   if (backup/'plugin-source').exists():os.replace(backup/'plugin-source',target)
   raise
 finally:
  if staged.exists():shutil.rmtree(staged)

def hook_groups(hooks,bundled,previous_command,command,use_bridge):
 for event,groups in bundled.items():
  destination=hooks.setdefault('hooks',{}).setdefault(event,[])
  if not use_bridge:
   # Hosts that discover bundled hooks must not also run our compatibility hook.
   for group in destination:group['hooks']=[h for h in group.get('hooks',[]) if h.get('command') not in {previous_command,command}]
   hooks['hooks'][event]=[g for g in destination if g.get('hooks')]
   continue
  for group in destination:
   for handler in group.get('hooks',[]):
    if handler.get('command')==previous_command:handler['command']=command
  if not any(h.get('command')==command for g in destination for h in g.get('hooks',[])):
   for group in groups:
    group=json.loads(json.dumps(group))
    for handler in group['hooks']:handler['command']=command
    destination.append(group)
 return hooks

def install(source, home):
    target = home / '.codex/plugins/pstack'
    market = home / '.agents/plugins/marketplace.json'
    doc = json.loads(market.read_text()) if market.exists() else {
        'name': 'personal', 'interface': {'displayName': 'Personal Plugins'}, 'plugins': []
    }
    name = doc['name']
    if not name or Path(name).name != name or name in {'.', '..'}:
        raise ValueError('invalid marketplace name')
    entry = {
        'name': 'pstack', 'source': {'source': 'local', 'path': './.codex/plugins/pstack'},
        'policy': {'installation': 'AVAILABLE', 'authentication': 'ON_INSTALL'}, 'category': 'Coding'
    }
    previous = next((p for p in doc['plugins'] if p['name'] == 'pstack'), None)
    if previous is not None and previous != entry:
        raise SystemExit('Existing marketplace pstack entry differs; reconcile before replacing')

    codex_config = Path(os.environ.get('CODEX_HOME') or home / '.codex')
    plugin_cache = codex_config / 'plugins/cache' / name / 'pstack'
    installed = None
    if target.exists():
        current = json.loads((target/'UPSTREAM.lock.json').read_text()) if (target/'UPSTREAM.lock.json').exists() else {}
        owner = json.loads((target/'PORT.lock.json').read_text()) if (target/'PORT.lock.json').exists() else {}
        if owner.get('adapter') != 'pstack-openai-personal' and current.get('commit') != '7022c81efb48d8b5eb15498ce6043a3bd74b694c':
            raise SystemExit('Existing pstack source has different ownership; reconcile before replacing')
        version = json.loads((target/'plugin.json').read_text())['version']
        if not version or Path(version).name != version or version in {'.', '..'}:
            raise ValueError('invalid installed package version')
        installed = plugin_cache / version
        next_pin = json.loads((source/'UPSTREAM.lock.json').read_text())['commit']
        if current.get('commit') != next_pin:
            review = json.loads((source/'UPDATE-REVIEW.json').read_text()) if (source/'UPDATE-REVIEW.json').exists() else {}
            if (review.get('commit') != next_pin or not review.get('resolved_conflicts')
                    or not review.get('behavior_review') or not review.get('installed_workflow_evidence')):
                raise SystemExit('Upstream upgrade requires UPDATE-REVIEW.json for this exact pin, resolved conflicts and real installed workflow evidence')

    backup = home / '.local/share/pstack/install-backups' / datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup.mkdir(parents=True, exist_ok=False)
    bridge_script = codex_config / 'hooks/pstack-bridge.py'
    hooks_path = codex_config / 'hooks.json'
    settings = [market, codex_config/'config.toml', hooks_path, bridge_script]
    for path in settings:
        if path.exists():
            shutil.copy2(path, backup/path.name)
    # The CLI may remove the old version's cache before a later command fails.
    # That cache is also the baseline needed to retry a reviewed upgrade.
    if plugin_cache.exists():
        shutil.copytree(plugin_cache, backup/'plugin-cache', symlinks=True)
    sync_source(source, target, backup, installed)
    try:
        market.parent.mkdir(parents=True, exist_ok=True)
        if previous is None:
            doc['plugins'].append(entry)
        market.write_text(json.dumps(doc, indent=2)+'\n')
        subprocess.run(['codex', 'plugin', 'marketplace', 'add', str(home), '--json'], check=True)
        subprocess.run(['codex', 'plugin', 'add', 'pstack@'+name, '--json'], check=True)
        detail = codex_rpc('plugin/read', {'pluginName': 'pstack', 'marketplacePath': str(market)})
        bridge = not detail['plugin']['hooks']
        if bridge:
            bridge_script.parent.mkdir(parents=True, exist_ok=True)
            if bridge_script.exists() and 'PSTACK_OWNED_NATIVE_HOOK_BRIDGE_V1' not in bridge_script.read_text():
                raise ValueError('Existing native hook bridge has different ownership')
            shutil.copy2(source/'hooks/bridge.py', bridge_script)
        hooks = json.loads(hooks_path.read_text()) if hooks_path.exists() else {'hooks': {}}
        bundled = json.loads((source/'hooks/hooks.json').read_text())['hooks']
        hooks = hook_groups(hooks, bundled, f'python3 "{target / "hooks/lifecycle.py"}"', f'python3 "{bridge_script}"', bridge)
        hooks_path.write_text(json.dumps(hooks, indent=2)+'\n')
    except BaseException as error:
        try:
            os.replace(target, backup/'failed-plugin-source')
            if (backup/'plugin-source').exists():
                os.replace(backup/'plugin-source', target)
            if plugin_cache.exists():
                shutil.rmtree(plugin_cache)
            if (backup/'plugin-cache').exists():
                shutil.copytree(backup/'plugin-cache', plugin_cache, symlinks=True)
            for path in settings:
                saved = backup/path.name
                if saved.exists():
                    shutil.copy2(saved, path)
                else:
                    path.unlink(missing_ok=True)
        except OSError as rollback_error:
            raise RuntimeError(f'Install failed ({error}); local rollback incomplete. Recover from {backup}') from rollback_error
        raise RuntimeError(f'Install failed ({error}). Restored local source, cache and settings. '
                           f'Codex may retain other registration metadata. Retry the installer. Backup: {backup}') from error
    print(json.dumps({'marketplace': name, 'source': str(target), 'backup': str(backup),
                      'native_hook_compatibility_bridge': bridge, 'hook_trust_required': True}, indent=2))


def main():
    install(Path(__file__).resolve().parents[1], Path.home())


if __name__ == '__main__':
    main()
