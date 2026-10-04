#!/usr/bin/env python3
"""Plan and stage three-way upstream updates. Never installs or touches live state."""
from __future__ import annotations
import argparse,base64,hashlib,json,re,shutil,subprocess,tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
HEADER='\n## OpenAI runtime contract\n\nRead [the adapter contract](../../references/runtime-contract.md) before this workflow. It maps provider selection, agent calls, loops, persistent state, history, verification, and authorization. That contract supersedes Cursor-specific execution syntax and unverified model fallbacks below; the engineering steps remain required. Use native tools in the current host; cloud uses available OpenAI models. Never create a remote laptop connection or require a URL/MCP setup.\n'
OWNED={'skills/setup-pstack/SKILL.md','skills/make-bot-ui/SKILL.md','README.md','plugin.json','.codex-plugin/plugin.json'}
def sha(data):return hashlib.sha256(data).hexdigest() if data is not None else None
def encode(data):return base64.b64encode(data).decode() if data is not None else None
def inventory_row(path,data):
 file=Path(path)
 row={'path':path,'sha256':sha(data),'bytes':len(data)}
 if file.suffix not in {'.md','.mdc','.ts','.mjs','.sh','.json','.yaml','.html','.js','.css'} and file.name not in {'watch-pr','bun.lock'}:
  return {**row,'kind':'asset'}
 text=data.decode()
 row['references']=sorted(set(re.findall(r'`([^`\n]{1,180})`',text)))
 if file.name=='SKILL.md':
  row['kind']='automation-skill' if '/automations/' in path else 'skill'
  description=re.search(r'^description: (.*)$',text,re.M)
  row['description']=description.group(1) if description else ''
 elif '/playbooks/' in path:
  row.update(kind='playbook',steps=re.findall(r'^\d+\. (.*)',text,re.M))
 else:
  row['kind']=next(
   (kind for part,kind in [('agents','agent'),('rules','rule'),('scripts','runtime')]
    if '/'+part+'/' in path),
   'reference/config/guide',
  )
 return row
def git(repo,*argv):return subprocess.run(['git','-C',str(repo),*argv],capture_output=True,check=True).stdout
def mapped(path):
 pack,rest=path.split('/',1)
 if rest.startswith('agents/') and rest.endswith('.md'):return 'skills/agent-'+Path(rest).stem+'/SKILL.md'
 if rest.startswith('rules/'):return 'references/team-kit-rules/'+Path(rest).name
 if rest.startswith(('skills/','assets/')):return rest
 if pack=='pstack' and rest.startswith(('docs/','automations/')):return rest
 if rest=='LICENSE':return 'LICENSE' if pack=='pstack' else 'LICENSE.cursor-team-kit'
 if pack=='pstack' and rest=='README.md':return rest
 return None

def adapt(path,data):
 target=mapped(path)
 if not target:return data
 try:text=data.decode()
 except UnicodeDecodeError:return data
 if '/agents/' in path:
  text=re.sub(r'^name: .*$',f'name: agent-{Path(path).stem}',text,flags=re.M);text=re.sub(r'^model: .*\n|^is_background: .*\n','',text,flags=re.M)
 if target.startswith(('skills/','docs/','automations/')) and target.endswith(('.md','.yaml','.yml')):
  text=text.replace('~/.cursor/rules/pstack-models.mdc','the persistent pstack runtime configuration (pstack_config)').replace('`pstack-models.mdc`','`pstack_config`')
  text=text.replace('.cursor/automations/benny/','.agents/automations/benny/').replace('.cursor/benny/','.agents/benny/').replace('.cursor/skills/','.agents/skills/').replace('~/.cursor/skills/','~/.agents/skills/')
  if target.startswith('automations/'):
   text=text.replace('prefer_cursor_actions','prefer_native_actions')
  if target.endswith('/SKILL.md'):
   end=text.find('\n---',4)+4 if text.startswith('---\n') else 0
   header=HEADER if not target.startswith('automations/') else HEADER.replace('Read [the adapter contract](../../references/runtime-contract.md)', 'Call `pstack_context` for this workspace and read its returned `adapter_contract` path')
   if end:text=text[:end]+header+text[end:]
   text=re.sub(r'^name: Poteto Mode$','name: poteto-mode',text,flags=re.M)
 return text.encode()

def merge(ours,base,incoming):
 if ours==base:return incoming,False
 if incoming==base or ours==incoming:return ours,False
 if ours is None or base is None or incoming is None:return ours,True
 if any(b'\0' in x for x in [ours,base,incoming]):return ours,True
 with tempfile.TemporaryDirectory() as folder:
  paths=[Path(folder)/n for n in ['current','base','incoming']]
  for path,data in zip(paths,[ours,base,incoming]):path.write_bytes(data)
  p=subprocess.run(['git','merge-file','-p',*map(str,paths)],capture_output=True)
  if p.returncode<0 or p.returncode>127:raise RuntimeError(p.stderr.decode(errors='replace'))
  return p.stdout,p.returncode!=0

def plan(repo,ref,root=ROOT):
 lock=json.loads((root/'UPSTREAM.lock.json').read_text());commit=git(repo,'rev-parse',ref+'^{commit}').decode().strip()
 # Only blobs under these two packs are consumed; no upstream code is executed.
 raw=git(repo,'ls-tree','-r','--name-only','-z',commit,'--','pstack','cursor-team-kit');paths=[x.decode() for x in raw.split(b'\0') if x]
 old_paths=[str(p.relative_to(root/'upstream')) for p in (root/'upstream').rglob('*') if p.is_file()]
 targets={}
 for path in sorted(set(paths)|set(old_paths)):
  target=mapped(path)
  if target and target in targets and targets[target]!=path:raise ValueError('upstream mapping collision needs explicit adapter review: '+target)
  if target:targets[target]=path
 entries=[];inventory=[]
 for path in sorted(set(paths)|set(old_paths)):
  if not path.startswith(('pstack/','cursor-team-kit/')) or '..' in Path(path).parts:raise ValueError('unsafe upstream path')
  old=(root/'upstream'/path).read_bytes() if (root/'upstream'/path).is_file() else None
  new=git(repo,'show',commit+':'+path) if path in paths else None
  if new is not None:inventory.append(inventory_row(path,new))
  if old==new:continue
  target=mapped(path);current=(root/target).read_bytes() if target and (root/target).is_file() else None
  base=adapt(path,old) if old is not None else None;incoming=adapt(path,new) if new is not None else None
  if target in OWNED or path.endswith('/LICENSE'):merged=current;conflict=True;action='adapter-review'
  elif target:
   merged,conflict=merge(current,base,incoming);action='conflict' if conflict else 'delete' if merged is None else 'merge' if current!=base else 'copy'
  else:merged=None;conflict=False;action='vendor-only'
  entries.append({'upstream_path':path,'target':target,'action':action,'old_sha':sha(old),'new_sha':sha(new),'current_sha':sha(current),'new_original':encode(new),'proposed':encode(merged),'incoming':encode(incoming) if conflict else None})
 inventory.sort(key=lambda row:(0 if row['path'].startswith('pstack/') else 1,row['path']))
 return {'format':1,'repository':lock['repository'],'from_commit':lock['commit'],'to_commit':commit,'changes':entries,'inventory':inventory,'blockers':[e['upstream_path'] for e in entries if e['action'] in {'conflict','adapter-review'}],'required_behavior_review':[e['upstream_path'] for e in entries],'install_performed':False}

def stage(doc,destination,root=ROOT):
 dest=Path(destination).resolve()
 if dest.exists() or dest.is_relative_to(root) or '.codex/plugins' in str(dest):raise ValueError('stage needs a new directory outside source and installed plugin paths')
 lock=json.loads((root/'UPSTREAM.lock.json').read_text())
 if lock['commit']!=doc['from_commit']:raise ValueError('source pin changed after plan')
 for e in doc['changes']:
  archive=(root/'upstream'/e['upstream_path']).resolve()
  if not archive.is_relative_to((root/'upstream').resolve()):raise ValueError('unsafe upstream archive target')
  if sha(archive.read_bytes() if archive.is_file() else None)!=e['old_sha']:raise ValueError('upstream baseline changed after plan')
  if sha(base64.b64decode(e['new_original']) if e['new_original'] is not None else None)!=e['new_sha']:raise ValueError('incoming archive digest mismatch')
  if e['target']:
   path=(root/e['target']).resolve()
   if not path.is_relative_to(root.resolve()):raise ValueError('unsafe mapped target')
   current=path.read_bytes() if path.is_file() else None
   if sha(current)!=e['current_sha']:raise ValueError('port changed after plan: '+e['target'])
 shutil.copytree(root,dest,ignore=shutil.ignore_patterns('__pycache__','.DS_Store','node_modules','.git','.upstream-update','upstream-history'))
 shutil.copytree(root/'upstream',dest/'upstream-history'/lock['commit'])
 for e in doc['changes']:
  archive=dest/'upstream'/e['upstream_path'];archive.parent.mkdir(parents=True,exist_ok=True)
  if e['new_original'] is None:archive.unlink(missing_ok=True)
  else:archive.write_bytes(base64.b64decode(e['new_original']))
  if not e['target']:continue
  target=dest/e['target'];target.parent.mkdir(parents=True,exist_ok=True)
  if e['action'] in {'conflict','adapter-review'}:
   conflict=dest/'.upstream-update/conflicts'/e['target'];conflict.parent.mkdir(parents=True,exist_ok=True)
   if e.get('incoming') is not None:Path(str(conflict)+'.incoming').write_bytes(base64.b64decode(e['incoming']))
   if e.get('proposed') is not None:Path(str(conflict)+'.proposed').write_bytes(base64.b64decode(e['proposed']))
  elif e['proposed'] is None:target.unlink(missing_ok=True)
  else:target.write_bytes(base64.b64decode(e['proposed']))
 lock.update({'commit':doc['to_commit'],'previous_commit':doc['from_commit'],'update_status':'requires_behavior_review'})
 version=json.loads((dest/'upstream/pstack/.cursor-plugin/plugin.json').read_text())['version'];lock['pstack_version']=version
 (dest/'UPSTREAM.lock.json').write_text(json.dumps(lock,indent=2)+'\n')
 adapter_version=None
 for manifest in [dest/'plugin.json',dest/'.codex-plugin/plugin.json']:
  if not manifest.exists():continue
  meta=json.loads(manifest.read_text())
  if adapter_version is None:
   adapter_version=version+'-openai.'+str(int(meta['version'].rsplit('.',1)[-1])+1)
  meta['version']=adapter_version
  manifest.write_text(json.dumps(meta,indent=2)+'\n')
 for manifest in [dest/'runtime/package.json',dest/'runtime/package-lock.json']:
  if not manifest.exists() or adapter_version is None:
   continue
  meta=json.loads(manifest.read_text())
  meta['version']=adapter_version
  if 'packages' in meta:
   meta['packages']['']['version']=adapter_version
  manifest.write_text(json.dumps(meta,indent=2)+'\n')
 (dest/'references').mkdir(exist_ok=True)
 (dest/'.upstream-update').mkdir(exist_ok=True);(dest/'.upstream-update/plan.json').write_text(json.dumps(doc,indent=2)+'\n');(dest/'references/upstream-inventory.json').write_text(json.dumps({'repository':doc['repository'],'commit':doc['to_commit'],'pstack_version':version,'files':doc['inventory']},indent=2)+'\n')
 return {'candidate':str(dest),'pin':doc['to_commit'],'blockers':doc['blockers'],'next':'Review semantic changes/conflicts, run runtime and installed workflow tests, write UPDATE-REVIEW.json with evidence, then install via runtime/install.py. Live configuration, marketplace and state were never changed.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();s=p.add_subparsers(dest='command',required=True);a=s.add_parser('plan');a.add_argument('--repo',required=True);a.add_argument('--ref',required=True);a.add_argument('--out',required=True);b=s.add_parser('stage');b.add_argument('--plan',required=True);b.add_argument('--destination',required=True);args=p.parse_args()
 if args.command=='plan':
  doc=plan(Path(args.repo),args.ref);Path(args.out).write_text(json.dumps(doc,indent=2)+'\n');print(json.dumps({k:v for k,v in doc.items() if k not in {'changes','inventory'}}|{'change_count':len(doc['changes'])}))
 else:print(json.dumps(stage(json.loads(Path(args.plan).read_text()),args.destination)))
