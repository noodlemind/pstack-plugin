from pathlib import Path
import tempfile,sys,unittest,json,subprocess,os,time
from unittest.mock import patch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
from store import Store, ROOT
from api import API,context,select_playbook
from engine import Engine
from providers import configure,ROLES
from hooks_test import hook_for_test
import benny,github,harnesses
import worktrees,frontier,install
from bridge import relay
from concurrent.futures import ThreadPoolExecutor
from xai_worker import path_in_scope, run

class RuntimeTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(prefix='pstack-tests-');self.root=Path(self.temp.name);self.scope=str(self.root/'repo');Path(self.scope).mkdir();self.store=Store(self.root/'data');self.api=API(self.store);self.store.put("config","execution",{"host":"local","mode":"local-cli","enabled_cli":["codex","claude","grok","gemini"],"machine":harnesses.fingerprint()})
  subprocess.run(['git','init','-q',self.scope],check=True);subprocess.run(['git','-C',self.scope,'config','user.email','test@localhost'],check=True);subprocess.run(['git','-C',self.scope,'config','user.name','pstack fixture'],check=True)
  (Path(self.scope)/'sample.txt').write_text('baseline');subprocess.run(['git','-C',self.scope,'add','sample.txt'],check=True);subprocess.run(['git','-C',self.scope,'commit','-qm','fixture'],check=True)
 def tearDown(self):self.api.engine.owner_lock.close();self.temp.cleanup()
 def call(self,op,action,**data):return self.api.call('pstack_'+op,action,data)
 def test_mode_survives_new_store_and_session_opt_out(self):
  self.call('context','activate',workspace=self.scope,prompt='fix a bug')
  self.assertTrue(context(Store(self.root/'data'),{'workspace':self.scope,'session':'new'})['mode']['enabled'])
  self.call('context','deactivate',workspace=self.scope,session='new')
  self.assertFalse(context(self.store,{'workspace':self.scope,'session':'new'})['mode']['enabled'])
  self.assertTrue(context(self.store,{'workspace':self.scope,'session':'other'})['mode']['enabled'])
 def test_all_playbooks_have_real_steps(self):
  books=list((ROOT/'skills/poteto-mode/playbooks').glob('*.md'));self.assertEqual(len(books),23)
  for p in books:self.assertTrue(context(self.store,{'workspace':self.scope,'playbook':p.stem})['steps'],p.name)
 def test_ci_word_does_not_steal_feature(self):self.assertEqual(select_playbook('implement a specification'),'feature')
 def test_unavailable_model_rejected(self):
  with self.assertRaises(ValueError):configure(self.store,'unlimited',{r:['codex:invented'] for r in ROLES},'user choice')
 def test_missing_confirmation_rejected(self):
  with self.assertRaises(ValueError):configure(self.store,'unlimited',{r:['auto'] for r in ROLES},'')
 def test_configuration_with_remote_workspace_persists_and_rejects_unconfirmed_changes(self):
  model={'key':'codex:fixture','provider':'codex','model':'fixture','family':'openai','efforts':['max'],'verified':True}
  self.store.put('model',model['key'],model)
  config=self.call('config','set',workspace=self.scope,budget='unlimited',roles={r:[model['key']] for r in ROLES},confirmation='Explicit fixture choices')
  self.assertEqual(Store(self.root/'data').get('config','models'),config)
  self.assertEqual(len(config['roles']),17)
  with self.assertRaises(ValueError):self.call('config','set',workspace=self.scope,budget='small',roles={r:[model['key']] for r in ROLES},confirmation='')
  self.assertEqual(self.call('config','get',workspace=self.scope),config)
 def test_model_probe_receives_provider_inputs_without_workspace_routing(self):
  with patch('providers.probe',return_value={'verified':True}) as probe:
   self.call('models','probe',workspace=self.scope,provider='codex',model='fixture',effort='max')
   probe.assert_called_once_with(self.store,provider='codex',model='fixture',effort='max')
 def test_all_roles_required(self):
  with self.assertRaises(ValueError):configure(self.store,'unlimited',{'swarm workers':['auto']},'user choice')
 def test_alias_without_parent_fails(self):
  configure(self.store,'unlimited',{r:['auto'] for r in ROLES},'user choice')
  with self.assertRaises(ValueError):self.call('agent','spawn',workspace=self.scope,prompt='test')
 def test_single_provider_panel_does_not_spawn(self):
  model={'key':'codex:fixture','provider':'codex','model':'fixture','family':'openai','efforts':['max'],'verified':True}
  self.store.put('model',model['key'],model);configure(self.store,'unlimited',{r:[model['key']] for r in ROLES},'fixture config')
  with self.assertRaises(ValueError):self.call('panel','start',workspace=self.scope,prompt='review')
  self.assertEqual(self.store.list('job'),[])
 def test_tasks_hold_dependencies_and_skips(self):
  a=self.call('task','add',workspace=self.scope,title='gate');b=self.call('task','add',workspace=self.scope,title='dependent',depends_on=[a['id']])
  with self.assertRaises(ValueError):self.call('task','set',id=b['id'],state='running')
  with self.assertRaises(ValueError):self.call('task','set',id=a['id'],state='skipped')
  self.call('task','set',id=a['id'],state='skipped',reason='not applicable')
  self.assertEqual(self.call('task','set',id=b['id'],state='running')['state'],'running')
 def test_done_task_requires_receipt(self):
  a=self.call('task','add',workspace=self.scope,title='verify')
  with self.assertRaises(ValueError):self.call('task','set',id=a['id'],state='done')
 def test_decision_trail_append_only_and_formula_safe(self):
  for n in ['=1+1','supersedes previous']:self.call('decision','append',workspace=self.scope,phase='run',decision=n,why='evidence',evidence='sample.txt',result='open')
  text=Path(self.call('decision','export',workspace=self.scope)['path']).read_text();self.assertIn("'=1+1",text);self.assertEqual(len(text.splitlines()),3)
 def test_recovery_is_workspace_scoped(self):
  self.call('checkpoint','save',workspace=self.scope,intent='resume',next_steps='verify')
  other=str(self.root/'other');Path(other).mkdir();self.call('checkpoint','save',workspace=other,intent='private')
  got=self.call('checkpoint','recover',workspace=self.scope);self.assertEqual(len(got['checkpoints']),1);self.assertEqual(got['checkpoints'][0]['intent'],'resume')
 def test_verification_failure_is_failure(self):
  r=self.call('verify','run',workspace=self.scope,argv=[sys.executable,'-c','raise SystemExit(3)'],method='actual failing CLI',lane='live');self.assertEqual(r['state'],'FAIL');self.assertEqual(r['proof']['exit_code'],3)
 def test_verification_success_has_exact_head_and_output(self):
  r=self.call('verify','run',workspace=self.scope,argv=[sys.executable,'-c',"print('real proof')"],method='CLI fixture',lane='live');self.assertEqual(r['state'],'PASS');self.assertEqual(r['proof']['stdout'],'real proof\n');self.assertEqual(len(r['head']),40)
 def test_head_mismatch_blocks_verification(self):
  with self.assertRaises(ValueError):self.call('verify','run',workspace=self.scope,argv=['true'],method='wrong head',head='0'*40)
 def test_artifact_changed_during_verification_fails(self):
  r=self.call('verify','run',workspace=self.scope,argv=[sys.executable,'-c',"open('sample.txt','w').write('changed')"],method='mutating verifier',lane='live');self.assertEqual(r['state'],'FAIL')
 def test_foreground_continuation_stops_on_predicate_and_cancel(self):
  row=self.call('loop','arm_foreground',workspace=self.scope,session='test',prompt='finish',done_command=[sys.executable,'-c','raise SystemExit(1)'],max_seconds=30,max_iterations=2)
  result=hook_for_test(self.store,{'cwd':self.scope,'session_id':'test','hook_event_name':'Stop'});self.assertEqual(result['decision'],'block')
  self.call('loop','cancel',id=row['id']);self.assertEqual(hook_for_test(self.store,{'cwd':self.scope,'session_id':'test','hook_event_name':'Stop'}),{})
 def test_foreground_budget_is_blocked(self):
  row=self.call('loop','arm_foreground',workspace=self.scope,session='test',prompt='finish',done_command=['false'],max_seconds=30,max_iterations=1)
  hook_for_test(self.store,{'cwd':self.scope,'session_id':'test','hook_event_name':'Stop'});hook_for_test(self.store,{'cwd':self.scope,'session_id':'test','hook_event_name':'Stop'})
  self.assertEqual(self.store.get('foreground',row['id'])['state'],'blocked')
 def test_foreground_timeout_is_blocked_without_continuation(self):
  row=self.call('loop','arm_foreground',workspace=self.scope,session='test',prompt='finish',done_command=[sys.executable,'-c','import time;time.sleep(3)'],max_seconds=.05,max_iterations=2)
  result=hook_for_test(self.store,{'cwd':self.scope,'session_id':'test','hook_event_name':'Stop'})
  self.assertNotEqual(result.get('decision'),'block');self.assertEqual(self.store.get('foreground',row['id'])['state'],'blocked')
 def test_foreground_predicate_cannot_overwrite_concurrent_cancel(self):
  row=self.call('loop','arm_foreground',workspace=self.scope,session='test',prompt='finish',done_command=['false'],max_seconds=30,max_iterations=2)
  def cancel_then_return(*_):self.call('loop','cancel',id=row['id']);return {'exit_code':1}
  with patch('lifecycle.execute',side_effect=cancel_then_return):result=hook_for_test(self.store,{'cwd':self.scope,'session_id':'test','hook_event_name':'Stop'})
  self.assertEqual(result,{});self.assertEqual(self.store.get('foreground',row['id'])['state'],'cancelled')
 def test_benny_setup_preserves_destination_files_and_conflicts(self):
  target=Path(self.scope)/'.agents/automations/benny';target.mkdir(parents=True);(target/'owned.txt').write_text('owned');(target/'README.md').write_text('locally changed')
  got=benny.setup(self.store,{'workspace':self.scope});self.assertEqual((target/'owned.txt').read_text(),'owned');self.assertEqual((target/'README.md').read_text(),'locally changed');self.assertTrue(got['conflicts']);self.assertFalse(got['enabled'])
 def benny_config(self):
  self.fixture_models()
  return benny.setup(self.store,{'workspace':self.scope,'config':{'repository':'fixture','default_branch':'main','source_channel':'C_FIXTURE','triage_identity':'U_TRIAGE','tracker':'fixture','control_skill':'control-ui','feature_map':'feature-map.md','models':{role:'codex:a' for role in benny.MODEL_ROLES},'budgets':{name:1 for name in benny.BUDGET_FIELDS}}})
 def test_benny_requires_own_verified_models_and_execution_budgets(self):
  got=benny.setup(self.store,{'workspace':self.scope,'config':{name:'fixture' for name in benny.REQUIRED}})
  self.assertEqual(got['state'],'incomplete');self.assertEqual(len(got['missing']),12)
 def test_benny_rejects_unverified_role_and_boolean_budget(self):
  row=self.benny_config();config=row['config'];config['models']['triage']='codex:unavailable';config['budgets']['poll_seconds']=True
  got=benny.setup(self.store,{'workspace':self.scope,'config':config});self.assertEqual(got['state'],'incomplete');self.assertEqual(len(got['missing']),2)
 def report(self):
  self.benny_config();return benny.ingest(self.store,{'workspace':self.scope,'event':{'channel':'C_FIXTURE','ts':'100.1','text':'bug'},'parent_preflight':True,'tracker_preflight':True})
 def test_benny_missing_preflight_has_no_run(self):
  self.benny_config()
  with self.assertRaises(ValueError):benny.ingest(self.store,{'workspace':self.scope,'event':{'channel':'C_FIXTURE','ts':'100.1'}})
  self.assertEqual(self.store.list('benny_run'),[])
 def test_benny_duplicate_trigger_is_idempotent(self):
  a=self.report();b=benny.ingest(self.store,{'workspace':self.scope,'event':{'channel':'C_FIXTURE','ts':'100.1'},'parent_preflight':True,'tracker_preflight':True});self.assertEqual(a['id'],b['id']);self.assertEqual(len(self.store.list('benny_run')),1)
 def test_benny_rejects_reply_trigger(self):
  self.benny_config()
  with self.assertRaises(ValueError):benny.ingest(self.store,{'workspace':self.scope,'event':{'channel':'C_FIXTURE','ts':'101.2','thread_ts':'100.1'},'parent_preflight':True,'tracker_preflight':True})
 def test_benny_rejects_untrusted_marker(self):
  row=self.report()
  with self.assertRaises(ValueError):benny.verdict(self.store,{'id':row['id'],'identity':'UNTRUSTED','marker':'[benny:bug]','text':'bug','parent_preflight':True})
 def test_benny_one_thread_verdict_and_acknowledgement(self):
  row=self.report();args={'id':row['id'],'identity':'U_TRIAGE','marker':'[benny:bug]','text':'verified','parent_preflight':True}
  a=benny.verdict(self.store,args);b=benny.verdict(self.store,args);self.assertEqual(a['id'],b['id']);self.assertEqual(a['source'],{'channel':'C_FIXTURE','thread_ts':'100.1'})
  with self.assertRaises(ValueError):benny.acknowledge(self.store,{'id':row['id'],'channel':'C_FIXTURE','thread_ts':'WRONG','message_ts':'101'})
  got=benny.acknowledge(self.store,{'id':row['id'],'channel':'C_FIXTURE','thread_ts':'100.1','message_ts':'101'});self.assertEqual(got['state'],'await_repro')
  with self.assertRaises(ValueError):benny.repro_gate(self.store,{'id':row['id'],'identity':'U_TRIAGE'})
 def test_no_shipping_without_user_authorization(self):
  with self.assertRaises(ValueError):github.ship(self.store,{'plan_id':'imaginary'})


 def test_existing_dirty_file_mutation_fails_receipt(self):
  (Path(self.scope)/'sample.txt').write_text('already dirty')
  r=self.call('verify','run',workspace=self.scope,argv=[sys.executable,'-c',"open('sample.txt','w').write('differently dirty')"],method='verifier changes already-dirty bytes',lane='live');self.assertEqual(r['state'],'FAIL');self.assertNotEqual(r['artifact_before'],r['artifact_after'])
 def test_trail_exports_beyond_history_page(self):
  for i in range(505):self.store.event('decision',{'phase':'test','decision':str(i)},self.scope)
  self.assertEqual(len(Path(self.store.decisions(self.scope)).read_text().splitlines()),506)
 def test_concurrent_benny_verdict_is_single_outbox(self):
  row=self.report();args={'id':row['id'],'identity':'U_TRIAGE','marker':'[benny:bug]','text':'verified','parent_preflight':True}
  with ThreadPoolExecutor(max_workers=8) as pool:results=list(pool.map(lambda _:benny.verdict(self.store,args),range(16)))
  self.assertEqual(len({x['id'] for x in results}),1)
 def test_xai_paths_and_session_ids_stay_scoped(self):
  with self.assertRaises(ValueError):path_in_scope(Path(self.scope),'../outside')
  with self.assertRaises(ValueError):run('no-model','high','unused',resume='../escape')


 def fixture_models(self):
  bin_dir = self.root / 'fixture-bin'
  bin_dir.mkdir(exist_ok=True)
  for name in ('codex', 'claude'):
   executable = bin_dir / name
   executable.write_text('#!/bin/sh\nexit 99\n')
   executable.chmod(0o755)
  path_patch = patch.dict(os.environ, {'PATH': str(bin_dir) + os.pathsep + os.environ.get('PATH', '')})
  path_patch.start()
  self.addCleanup(path_patch.stop)
  models=[{'key':'codex:a','provider':'codex','model':'a','family':'openai','efforts':['max'],'verified':True},{'key':'claude:b','provider':'claude','model':'b','family':'anthropic','efforts':['max'],'verified':True}]
  for model in models:self.store.put('model',model['key'],model)
  configure(self.store,'unlimited',{r:[m['key'] for m in models] if r in {'arena runners','arena cross-judge pool','architect runners','interrogate reviewers'} else ['codex:a'] for r in ROLES},'explicit isolated test fixture')
 def test_cancel_between_check_and_launch_never_starts_process(self):
  with patch('engine.threading.Thread.start'):
   j=self.api.engine.command_job(self.scope,[sys.executable,'-c',"open('must-not-exist','w').write('bad')"],3)
  def cancel_at_boundary():self.api.engine.cancel(j['id']);return dict(os.environ)
  with patch('engine.providers.safe_env',side_effect=cancel_at_boundary):self.api.engine.run_job(j['id'])
  self.assertEqual(self.store.get('job',j['id'])['state'],'cancelled');self.assertFalse((Path(self.scope)/'must-not-exist').exists())
 def test_cancel_predicate_never_launches_writer_or_overwrites_cancel(self):
  self.fixture_models();loop=self.api.engine.loop_start({'workspace':self.scope,'prompt':'never launch owner','done_command':[sys.executable,'-c','import time;time.sleep(5);raise SystemExit(1)'],'max_seconds':20,'max_iterations':2})
  deadline=time.time()+3
  while 'loop:'+loop['id'] not in self.api.engine.processes and time.time()<deadline:time.sleep(.01)
  self.api.engine.loop_stop(loop['id']);time.sleep(.15);self.assertEqual(self.store.get('loop',loop['id'])['state'],'cancelled');self.assertEqual(self.store.list('job',self.scope),[])
 def test_predicate_timeout_blocks_without_spawning_repair(self):
  self.fixture_models();loop=self.api.engine.loop_start({'workspace':self.scope,'prompt':'never launch owner','done_command':[sys.executable,'-c','import time;time.sleep(3)'],'predicate_timeout':.05,'max_seconds':10,'max_iterations':2})
  deadline=time.time()+3
  while self.store.get('loop',loop['id'])['state']=='running' and time.time()<deadline:time.sleep(.01)
  self.assertEqual(self.store.get('loop',loop['id'])['state'],'blocked');self.assertEqual(self.store.list('job'),[])
 def test_panel_retry_preserves_distinct_seats_and_returns_same_panel(self):
  self.fixture_models()
  with patch('engine.threading.Thread.start'):
   p=self.api.engine.panel({'workspace':self.scope,'prompt':'panel test','idempotency_key':'retry'});q=self.api.engine.panel({'workspace':self.scope,'prompt':'panel test','idempotency_key':'retry'})
  self.assertEqual(p['id'],q['id']);self.assertEqual(len(set(p['jobs'])),2);self.assertEqual(len({self.store.get('job',j)['selection']['model'] for j in p['jobs']}),2)
 def test_second_engine_cannot_recover_a_live_owner(self):
  self.api.engine
  with self.assertRaises(RuntimeError):Engine(Store(self.root/'data'))
 def test_agent_launch_failure_writes_result_and_coordinator_mail(self):
  with patch('engine.threading.Thread.start'):job=self.api.engine.command_job(self.scope,['/missing/pstack-fixture-cli'],2)
  self.api.engine.run_job(job['id']);row=self.store.get('job',job['id'])
  self.assertEqual(row['state'],'failed');self.assertFalse(json.loads(Path(row['result_path']).read_text())['completed']);self.assertTrue(any(m['to']=='coordinator' and m['from']==job['id'] for m in self.store.list('message',self.scope)))
 def test_resumed_result_retains_original_coordinator(self):
  row={'id':'old','workspace':self.scope,'cwd':self.scope,'state':'completed','session':'fixture-native-session','role':'how explorer','readonly':True,'timeout':30,'parent_id':'coordinator'};self.store.put('job','old',row,self.scope)
  with patch.object(self.api.engine,'spawn',return_value={'id':'new'}) as spawn:self.api.engine.resume('old','next')
  self.assertEqual(spawn.call_args.args[0]['parent_id'],'coordinator')
 def test_loop_overall_deadline_cancels_a_queued_owner(self):
  self.fixture_models()
  def queued_owner(_):
   with patch('engine.threading.Thread.start'):
    return self.api.engine.command_job(self.scope,[sys.executable,'-c',"open('late-owner','w').write('bad')"],30)
  with patch.object(self.api.engine,'spawn',side_effect=queued_owner):
   loop=self.api.engine.loop_start({'workspace':self.scope,'prompt':'deadline fixture','done_command':['false'],'max_seconds':.1,'max_iterations':2})
   deadline=time.time()+4
   while self.store.get('loop',loop['id'])['state']=='running' and time.time()<deadline:time.sleep(.02)
  row=self.store.get('loop',loop['id']);self.assertEqual(row['state'],'blocked');self.assertIn('time budget',row['stop_reason']);self.assertEqual(self.store.get('job',row['current_job'])['state'],'cancelled');self.assertFalse((Path(self.scope)/'late-owner').exists())
 def test_worktree_cleanup_holds_dirty_tree_then_removes_clean_owned_tree(self):
  tree=self.store.home/'worktrees/fixture';tree.parent.mkdir()
  subprocess.run(['git','-C',self.scope,'worktree','add','--detach',str(tree),'HEAD'],capture_output=True,check=True)
  self.store.put('job','fixture',{'id':'fixture','workspace':self.scope,'cwd':str(tree),'state':'completed'},self.scope)
  (tree/'local.txt').write_text('keep')
  with self.assertRaises(ValueError):worktrees.cleanup(self.store,{'workspace':self.scope,'path':str(tree),'user_authorization':'isolated fixture'})
  self.assertTrue((tree/'local.txt').exists());(tree/'local.txt').unlink()
  self.assertEqual(worktrees.cleanup(self.store,{'workspace':self.scope,'path':str(tree),'user_authorization':'isolated fixture'})['exit_code'],0);self.assertFalse(tree.exists())
 def test_worktree_cleanup_requires_authorization(self):
  with self.assertRaises(ValueError):worktrees.cleanup(self.store,{'workspace':self.scope,'path':self.scope})
 def test_frontier_frozen_order_is_readable_by_upstream_runtime(self):
  folder=self.root/'orch';folder.mkdir();(folder/'frontier.json').write_text('{"generation":0,"prs":[],"lowestUnmerged":null}')
  rows=[{'nameWithOwner':'fixture/repo'},{'number':1,'state':'MERGED','headRefName':'first','baseRefName':'main','headRefOid':'1'*40},{'number':2,'state':'OPEN','headRefName':'second','baseRefName':'main','headRefOid':'2'*40}]
  with patch('frontier.gh_json',side_effect=rows) as fetch:
   got=self.call('orch','run',workspace=self.scope,argv=['--json','frontier','set','--repo','fixture/repo','--prs','1,2'],store_path=str(folder))
  self.assertEqual(fetch.call_args_list[0].args[0],['repo','view','fixture/repo','--json','nameWithOwner'])
  self.assertEqual(got['lowestUnmerged'],2);self.assertEqual(got['generation'],1);self.assertFalse((folder/'.orch.lock').exists())
  result=subprocess.run(['bun',str(ROOT/'skills/poteto-mode/scripts/orch/orch.ts'),'--store',str(folder),'--json','frontier','show'],capture_output=True,text=True)
  self.assertEqual(result.returncode,0,result.stderr);self.assertEqual(json.loads(result.stdout)['prs'][1]['sha'],'2'*40)
 def test_frontier_rejects_noncontiguous_open_chain_without_mutation(self):
  folder=self.root/'orch';folder.mkdir();initial='{"generation":0,"prs":[],"lowestUnmerged":null}';(folder/'frontier.json').write_text(initial)
  rows=[{'nameWithOwner':'fixture/repo'},{'number':1,'state':'OPEN','headRefName':'first','baseRefName':'main','headRefOid':'1'*40},{'number':2,'state':'OPEN','headRefName':'second','baseRefName':'wrong','headRefOid':'2'*40}]
  with patch('frontier.gh_json',side_effect=rows),self.assertRaises(ValueError):frontier.frontier({'workspace':self.scope,'argv':['frontier','set','--prs','1,2'],'store_path':str(folder)})
  self.assertEqual((folder/'frontier.json').read_text(),initial)
 def test_native_bridge_disabled_uninstalled_and_nondefault_marketplace(self):
  home=self.root/'fake-home';(home/'.codex/plugins/pstack/hooks').mkdir(parents=True);(home/'.agents/plugins').mkdir(parents=True)
  (home/'.agents/plugins/marketplace.json').write_text('{"name":"my-personal"}')
  (home/'.codex/config.toml').write_text('[plugins."pstack@my-personal"]\nenabled = false\n')
  script=home/'.codex/plugins/pstack/hooks/lifecycle.py';script.write_text('print(\'{"injected":true}\')')
  self.assertEqual(relay(home,'{}')[1],'{}\n')
  (home/'.codex/config.toml').write_text('[plugins."pstack@my-personal"]\nenabled = true\n');self.assertTrue(json.loads(relay(home,'{}')[1])['injected'])
  script.unlink();self.assertEqual(relay(home,'{}')[1],'{}\n')
 def test_bundled_hook_support_removes_only_our_bridge(self):
  hooks={'hooks':{'Stop':[{'hooks':[{'command':'ours'},{'command':'keep'}]},{'hooks':[{'command':'old'}]}]}}
  got=install.hook_groups(hooks,{'Stop':[]},'old','ours',False)
  self.assertEqual(got['hooks']['Stop'],[{'hooks':[{'command':'keep'}]}])
 def test_update_installer_removes_reviewed_deletions_preserves_extras(self):
  source=self.root/'source';target=self.root/'installed';backup=self.root/'backup';source.mkdir();target.mkdir();backup.mkdir();(source/'.upstream-update').mkdir()
  (target/'deleted.md').write_text('baseline');(target/'personal.txt').write_text('personal');(source/'new.md').write_text('new')
  digest=install.hashlib.sha256(b'baseline').hexdigest()
  (source/'.upstream-update/plan.json').write_text(json.dumps({'changes':[{'new_original':'YQ==','action':'delete','target':'deleted.md','current_sha':digest}]}))
  install.sync_source(source,target,backup);self.assertFalse((target/'deleted.md').exists());self.assertEqual((target/'personal.txt').read_text(),'personal');self.assertEqual((backup/'plugin-source/deleted.md').read_text(),'baseline')
 def test_update_installer_holds_locally_modified_deletions(self):
  source=self.root/'source';target=self.root/'installed';backup=self.root/'backup';source.mkdir();target.mkdir();backup.mkdir();(source/'.upstream-update').mkdir();(target/'deleted.md').write_text('manual change')
  (source/'.upstream-update/plan.json').write_text(json.dumps({'changes':[{'new_original':'YQ==','action':'delete','target':'deleted.md','current_sha':install.hashlib.sha256(b'baseline').hexdigest()}]}))
  with self.assertRaisesRegex(ValueError,'installed file changed'):install.sync_source(source,target,backup)
  self.assertEqual((target/'deleted.md').read_text(),'manual change');self.assertFalse((backup/'plugin-source').exists())
 def shipping_fixture(self,state='PASS'):
  head=subprocess.check_output(['git','-C',self.scope,'rev-parse','HEAD'],text=True).strip()
  author={'id':'author','workspace':self.scope,'readonly':False,'state':'completed','selection':{'family':'openai'}}
  verifier={'id':'verifier','workspace':self.scope,'readonly':True,'state':'completed','start_head':head,'end_head':head,'selection':{'family':'anthropic'}}
  self.store.put('job','author',author,self.scope);self.store.put('job','verifier',verifier,self.scope)
  receipts=[]
  for lane in ['unit','live']:
   receipts.append(self.call('verify','run',workspace=self.scope,argv=[sys.executable,'-c','assert 1+1==2; print("fixture proof")'],method='explicit test fixture proof for shipping guard',lane=lane,verifier_job='verifier'))
  verdict={'state':state,'repo':'fixture/repo','number':1,'head':head,'base':head,'verifier_job':'verifier','author_job':'author','method':'isolated fixture guard test','receipts':[r['id'] for r in receipts],'behavior':[{'surface':'fixture CLI','expected':'fixture proof','actual':'fixture proof','receipt_id':receipts[1]['id']}]}
  verifier['result']={'completed':True,'text':json.dumps(verdict)};self.store.put('job','verifier',verifier,self.scope)
  path=Path(self.scope)/'verdict.json';path.write_text(json.dumps(verdict));pr={'state':'OPEN','isDraft':False,'mergeable':'MERGEABLE','mergeStateStatus':'CLEAN','reviewDecision':'APPROVED','headRefOid':head,'baseRefOid':head,'statusCheckRollup':[{'conclusion':'SUCCESS'}]}
  return {'workspace':self.scope,'repo':'fixture/repo','number':1,'author_job':'author','verifier_job':'verifier','receipt_ids':[r['id'] for r in receipts],'verdict_evidence':str(path)}, {'pr':pr,'threads':[],'comments_incomplete':False}
 def test_shipping_rejects_completed_issues_verifier(self):
  args,pr=self.shipping_fixture('ISSUES')
  with patch('github.pr_snapshot',return_value=pr),self.assertRaisesRegex(ValueError,'verdict must be PASS'):github.prepare_shipping(self.store,args)
 def test_shipping_rejects_empty_lane_gate(self):
  args,pr=self.shipping_fixture();args['required_lanes']=[]
  with patch('github.pr_snapshot',return_value=pr),self.assertRaisesRegex(ValueError,'nonempty'):github.prepare_shipping(self.store,args)
 def test_shipping_rejects_fabricated_verdict_file(self):
  args,pr=self.shipping_fixture();j=self.store.get('job','verifier');j['result']['text']='ISSUES: defect still present';self.store.put('job','verifier',j,self.scope)
  with patch('github.pr_snapshot',return_value=pr),self.assertRaisesRegex(ValueError,'not emitted'):github.prepare_shipping(self.store,args)
 def test_shipping_rejects_verifier_old_actual_head(self):
  args,pr=self.shipping_fixture();j=self.store.get('job','verifier');j['start_head']='0'*40;self.store.put('job','verifier',j,self.scope)
  with patch('github.pr_snapshot',return_value=pr),self.assertRaisesRegex(ValueError,'actual verifier'):github.prepare_shipping(self.store,args)
 def test_shipping_prepares_bound_pass_without_merging(self):
  args,pr=self.shipping_fixture()
  with patch('github.pr_snapshot',return_value=pr):plan=github.prepare_shipping(self.store,args)
  self.assertEqual(plan['state'],'prepared');self.assertEqual(plan['author_job'],'author');self.assertEqual(plan['required_lanes'],['live','unit']);self.assertEqual(plan['verdict']['state'],'PASS')
 def test_authorized_shipping_uses_exact_head_guard(self):
  args,pr=self.shipping_fixture()
  with patch('github.pr_snapshot',return_value=pr):plan=github.prepare_shipping(self.store,args)
  merged={**pr,'pr':{**pr['pr'],'state':'MERGED'}}
  with patch('github.pr_snapshot',side_effect=[pr,merged]),patch('github.execute',return_value={'exit_code':0,'stdout':'isolated guard fixture'}) as execute:
   row=github.ship(self.store,{'plan_id':plan['id'],'user_authorization':'explicit isolated fixture authorization'})
  argv=execute.call_args.args[0];self.assertIn('--match-head-commit',argv);self.assertEqual(argv[-1],plan['head']);self.assertEqual(row['state'],'merged')
 def test_shipping_changed_head_never_calls_merge(self):
  args,pr=self.shipping_fixture()
  with patch('github.pr_snapshot',return_value=pr):plan=github.prepare_shipping(self.store,args)
  changed={**pr,'pr':{**pr['pr'],'headRefOid':'0'*40}}
  with patch('github.pr_snapshot',return_value=changed),patch('github.execute') as execute,self.assertRaisesRegex(ValueError,'head/base changed'):github.ship(self.store,{'plan_id':plan['id'],'user_authorization':'isolated fixture authorization'})
  execute.assert_not_called()

if __name__=='__main__':unittest.main(verbosity=2)
