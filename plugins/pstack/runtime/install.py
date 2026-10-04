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
   if not path.is_relative_to(target.resolve()):raise ValueError('unsafe update deletion')
   if not path.exists():continue
   if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=digest:raise ValueError('installed file changed; merge it before update: '+relative)
   rows.append(relative)
 return rows

def sync_source(source,target,backup):
 removed=deletions(source,target)
 retirement=source/'RETIRED-FILES.json'
 if retirement.exists():
  for row in json.loads(retirement.read_text())['files']:
   path=(target/row['path']).resolve()
   if not path.is_relative_to(target.resolve()):raise ValueError('unsafe retired path')
   if path.exists():
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=row['sha256']:raise ValueError('retired file changed; inspect before removing: '+row['path'])
    removed.append(row['path'])
 if target.is_symlink():raise ValueError('refusing a symlinked plugin source')
 target.parent.mkdir(parents=True,exist_ok=True)
 staged=Path(tempfile.mkdtemp(prefix='.pstack-install-',dir=target.parent))
 try:
  if target.exists():shutil.copytree(target,staged,dirs_exist_ok=True)
  for relative in removed:(staged/relative).unlink(missing_ok=True)
  shutil.copytree(source,staged,dirs_exist_ok=True,ignore=shutil.ignore_patterns('__pycache__','.DS_Store','node_modules','.git'))
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

def main():
 source=Path(__file__).resolve().parents[1];home=Path.home()
 target=home/'.codex/plugins/pstack';market=home/'.agents/plugins/marketplace.json'
 doc=json.loads(market.read_text()) if market.exists() else {'name':'personal','interface':{'displayName':'Personal Plugins'},'plugins':[]}
 entry={'name':'pstack','source':{'source':'local','path':'./.codex/plugins/pstack'},'policy':{'installation':'AVAILABLE','authentication':'ON_INSTALL'},'category':'Coding'}
 previous=next((p for p in doc['plugins'] if p['name']=='pstack'),None)
 if previous is not None and previous!=entry:raise SystemExit('Existing marketplace pstack entry differs; reconcile before replacing')
 if target.exists():
  current=json.loads((target/'UPSTREAM.lock.json').read_text()) if (target/'UPSTREAM.lock.json').exists() else {}
  owner=json.loads((target/'PORT.lock.json').read_text()) if (target/'PORT.lock.json').exists() else {}
  if owner.get('adapter')!='pstack-openai-personal' and current.get('commit')!='7022c81efb48d8b5eb15498ce6043a3bd74b694c':raise SystemExit('Existing pstack source has different ownership; reconcile before replacing')
  next_pin=json.loads((source/'UPSTREAM.lock.json').read_text())
  if current.get('commit')!=next_pin['commit']:
   review=json.loads((source/'UPDATE-REVIEW.json').read_text()) if (source/'UPDATE-REVIEW.json').exists() else {}
   if review.get('commit')!=next_pin['commit'] or not review.get('resolved_conflicts') or not review.get('behavior_review') or not review.get('installed_workflow_evidence'):raise SystemExit('Upstream upgrade requires UPDATE-REVIEW.json for this exact pin, resolved conflicts and real installed workflow evidence')
  deletions(source,target) # Validate all removals before changing any source/configuration.
 backup=home/'.local/share/pstack/install-backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
 backup.mkdir(parents=True,exist_ok=True)
 for p in [market,home/'.codex/config.toml',home/'.codex/hooks.json']:
  if p.exists():shutil.copy2(p,backup/p.name)
 sync_source(source,target,backup)
 market.parent.mkdir(parents=True,exist_ok=True)
 if previous is None:doc['plugins'].append(entry)
 market.write_text(json.dumps(doc,indent=2)+'\n')
 subprocess.run(['codex','plugin','marketplace','add',str(home),'--json'],check=True)
 subprocess.run(['codex','plugin','add','pstack@'+doc['name'],'--json'],check=True)
 detail=codex_rpc('plugin/read',{'pluginName':'pstack','marketplacePath':str(market)})
 bridge=not detail['plugin']['hooks'];bridge_script=home/'.codex/hooks/pstack-bridge.py'
 if bridge:
  bridge_script.parent.mkdir(parents=True,exist_ok=True)
  if bridge_script.exists() and 'PSTACK_OWNED_NATIVE_HOOK_BRIDGE_V1' not in bridge_script.read_text():raise SystemExit('Existing native hook bridge has different ownership')
  shutil.copy2(source/'hooks/bridge.py',bridge_script)
 hooks_path=home/'.codex/hooks.json';hooks=json.loads(hooks_path.read_text()) if hooks_path.exists() else {'hooks':{}}
 bundled=json.loads((source/'hooks/hooks.json').read_text())['hooks']
 hooks=hook_groups(hooks,bundled,'python3 "'+str(target/'hooks/lifecycle.py')+'"','python3 "'+str(bridge_script)+'"',bridge)
 hooks_path.write_text(json.dumps(hooks,indent=2)+'\n')
 print(json.dumps({'marketplace':doc['name'],'source':str(target),'backup':str(backup),'native_hook_compatibility_bridge':bridge,'hook_trust_required':True},indent=2))

if __name__=='__main__':main()
