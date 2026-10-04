from pathlib import Path
import tempfile,subprocess,json,sys,unittest,shutil
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'runtime'))
import upstream_sync as sync
class UpdateTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.home=Path(self.tmp.name);self.repo=self.home/'repo';self.repo.mkdir();self.root=self.home/'port';self.root.mkdir()
  subprocess.run(['git','init','-q',str(self.repo)],check=True)
  for k,v in [('user.name','update fixture'),('user.email','fixture@localhost')]:subprocess.run(['git','-C',str(self.repo),'config',k,v],check=True)
  self.file='pstack/skills/demo/SKILL.md';self.old=b'---\nname: demo\ndescription: fixture\n---\n\n# Demo\n\nFirst upstream paragraph.\n\nSecond upstream paragraph.\n\nThird upstream paragraph.\n'
  self.write(self.file,self.old);self.write('pstack/.cursor-plugin/plugin.json',b'{"version":"0.1.0"}');self.commit()
  shutil.copytree(self.repo/'pstack',self.root/'upstream/pstack');(self.root/'upstream/cursor-team-kit').mkdir()
  self.target=self.root/'skills/demo/SKILL.md';self.target.parent.mkdir(parents=True);self.target.write_bytes(sync.adapt(self.file,self.old))
  (self.root/'UPSTREAM.lock.json').write_text(json.dumps({'repository':'https://github.com/cursor/plugins','commit':self.sha(),'pstack_version':'0.1.0'}));(self.root/'plugin.json').write_text('{"name":"pstack","version":"0.1.0-openai.1"}')
 def tearDown(self):self.tmp.cleanup()
 def write(self,path,data):p=self.repo/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 def commit(self):subprocess.run(['git','-C',str(self.repo),'add','.'],check=True);subprocess.run(['git','-C',str(self.repo),'commit','-qm','fixture update'],check=True)
 def sha(self):return sync.git(self.repo,'rev-parse','HEAD').decode().strip()
 def test_noop_pin_is_empty(self):self.assertEqual(sync.plan(self.repo,'HEAD',self.root)['changes'],[])
 def test_plan_retains_reference_description_and_playbook_inventory(self):
  self.write('pstack/skills/poteto-mode/playbooks/demo.md',b'# Demo\n1. Run `verify`.\n2. Recover.\n')
  self.commit()
  rows={r['path']:r for r in sync.plan(self.repo,'HEAD',self.root)['inventory']}
  self.assertEqual(rows[self.file]['kind'],'skill')
  self.assertEqual(rows[self.file]['description'],'fixture')
  book=rows['pstack/skills/poteto-mode/playbooks/demo.md']
  self.assertEqual(book['references'],['verify'])
  self.assertEqual(book['steps'],['Run `verify`.','Recover.'])
  self.assertEqual(book['kind'],'playbook')
 def test_new_upstream_namespace_collision_requires_review(self):
  self.write('cursor-team-kit/skills/demo/SKILL.md',self.old);self.commit()
  with self.assertRaisesRegex(ValueError,'mapping collision'):sync.plan(self.repo,'HEAD',self.root)
 def test_three_way_preserves_nonoverlapping_port_edits(self):
  self.target.write_bytes(self.target.read_bytes().replace(b'Third upstream paragraph.',b'Third paragraph with personal adapter detail.'))
  self.write(self.file,self.old.replace(b'First upstream paragraph.',b'First paragraph from future upstream.'));self.commit();plan=sync.plan(self.repo,'HEAD',self.root)
  self.assertFalse(plan['blockers']);dest=self.home/'candidate';sync.stage(plan,dest,self.root);text=(dest/'skills/demo/SKILL.md').read_text();self.assertIn('future upstream',text);self.assertIn('personal adapter',text);self.assertIn('OpenAI runtime contract',text)
  self.assertEqual(json.loads((self.root/'UPSTREAM.lock.json').read_text())['commit'],plan['from_commit']);self.assertTrue((dest/'upstream-history'/plan['from_commit']).is_dir())
 def test_conflict_retains_current_and_incoming(self):
  self.target.write_bytes(self.target.read_bytes().replace(b'First upstream paragraph.',b'Port competing change.'));self.write(self.file,self.old.replace(b'First upstream paragraph.',b'Upstream competing change.'));self.commit();plan=sync.plan(self.repo,'HEAD',self.root);self.assertTrue(plan['blockers']);dest=self.home/'candidate';sync.stage(plan,dest,self.root);self.assertIn('Port competing',(dest/'skills/demo/SKILL.md').read_text());self.assertTrue((dest/'.upstream-update/conflicts/skills/demo/SKILL.md.incoming').is_file())
 def test_new_skill_imported_with_contract(self):
  self.write('pstack/skills/new/SKILL.md',self.old.replace(b'name: demo',b'name: new'));self.commit();plan=sync.plan(self.repo,'HEAD',self.root);dest=self.home/'candidate';sync.stage(plan,dest,self.root);self.assertIn('OpenAI runtime contract',(dest/'skills/new/SKILL.md').read_text())
 def test_stage_preserves_identity_and_updates_all_package_versions(self):
  (self.root/'plugin.json').write_text(json.dumps({'name':'pstack','version':'0.1.0-openai.1','homepage':'https://example.com/adapter'}))
  (self.root/'runtime').mkdir()
  for filename,meta in [
   ('package.json',{'version':'0.1.0-openai.1'}),
   ('package-lock.json',{'version':'0.1.0-openai.1','packages':{'':{'version':'0.1.0-openai.1'}}}),
  ]:
   (self.root/'runtime'/filename).write_text(json.dumps(meta))
  self.write('pstack/.cursor-plugin/plugin.json',b'{"version":"0.2.0"}')
  self.commit()
  dest=self.home/'candidate'
  sync.stage(sync.plan(self.repo,'HEAD',self.root),dest,self.root)
  self.assertEqual(json.loads((dest/'plugin.json').read_text())['homepage'],'https://example.com/adapter')
  for filename in ['plugin.json','runtime/package.json','runtime/package-lock.json']:
   self.assertEqual(json.loads((dest/filename).read_text())['version'],'0.2.0-openai.2')
  self.assertEqual(json.loads((dest/'runtime/package-lock.json').read_text())['packages']['']['version'],'0.2.0-openai.2')
 def test_stage_excludes_dependencies_and_old_candidate_metadata(self):
  for folder in ['node_modules','.git','.upstream-update','upstream-history']:
   path=self.root/folder
   path.mkdir()
   (path/'private-fixture').write_text('fixture')
  dest=self.home/'candidate'
  sync.stage(sync.plan(self.repo,'HEAD',self.root),dest,self.root)
  for folder in ['node_modules','.git','.upstream-update','upstream-history']:
   self.assertFalse((dest/folder/'private-fixture').exists())
 def test_stale_plan_does_not_stage(self):
  self.write(self.file,self.old+b'New step.\n');self.commit();plan=sync.plan(self.repo,'HEAD',self.root);self.target.write_text('changed after plan')
  with self.assertRaises(ValueError):sync.stage(plan,self.home/'candidate',self.root)
 def test_removed_custom_skill_requires_conflict_review(self):
  self.target.write_bytes(self.target.read_bytes()+b'Personal extension.\n');(self.repo/self.file).unlink();self.commit();plan=sync.plan(self.repo,'HEAD',self.root);self.assertIn(self.file,plan['blockers'])
 def test_stage_rejects_path_escape(self):
  self.write(self.file,self.old+b'Changed.\n');self.commit();plan=sync.plan(self.repo,'HEAD',self.root);plan['changes'][0]['upstream_path']='../../escape'
  with self.assertRaises(ValueError):sync.stage(plan,self.home/'candidate',self.root)
if __name__=='__main__':unittest.main()
