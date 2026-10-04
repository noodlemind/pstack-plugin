from __future__ import annotations
import json,subprocess
from pathlib import Path
from engine import execute

def audit(store,scope):
 r=subprocess.run(['git','worktree','list','--porcelain','-z'],cwd=scope,capture_output=True,check=True)
 entries=[]
 for block in r.stdout.decode().split('\0\0'):
  parts=block.split('\0');fields={p.partition(' ')[0]:p.partition(' ')[2] for p in parts if p}
  if 'worktree' not in fields:continue
  path=fields['worktree'];owners=[j for j in store.list('job',scope) if Path(j['cwd']).resolve()==Path(path).resolve()]
  dirty=execute(['git','status','--porcelain'],path)
  owned=Path(path).resolve().is_relative_to((store.home/'worktrees').resolve()) and bool(owners)
  entries.append({'path':path,'head':fields.get('HEAD'),'branch':fields.get('branch'),'locked':'locked' in fields,'dirty':dirty['stdout'],'runtime_owned':owned,'active_jobs':[j['id'] for j in owners if j['state'] in {'queued','running'}],'owners':[j['id'] for j in owners],'eligible_for_runtime_cleanup':dirty['exit_code']==0 and not dirty['stdout'] and owned and 'locked' not in fields and not any(j['state'] in {'queued','running'} for j in owners)})
 return {'workspace':scope,'worktrees':entries,'note':'Native app-managed worktrees must use archive_worktree for recovery snapshots. Runtime cleanup only removes clean, inactive trees owned by this service. No unrelated session history is scanned.'}

def cleanup(store,args):
 if not args.get('user_authorization'):raise ValueError('explicit cleanup authorization required')
 report=audit(store,args['workspace']);path=str(Path(args['path']).resolve());row=next(x for x in report['worktrees'] if str(Path(x['path']).resolve())==path)
 if not row['runtime_owned'] or not row['eligible_for_runtime_cleanup']:raise ValueError('worktree is not clean, inactive and runtime-owned')
 result=execute(['git','worktree','remove',path],args['workspace']);store.event('worktree_cleanup',{'path':path,'result':result},args['workspace']);return result
