"""Reproduce first-use, budget changes and real verification without model access.

Only an aggregate, anonymous result is printed; temp paths and runtime IDs stay
inside the temporary fixture and are removed when the test exits.
"""
from pathlib import Path
import json
import os
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT/'plugins/pstack/runtime/pstack.py'


def main():
    with tempfile.TemporaryDirectory(prefix='pstack-first-use-') as folder:
        root = Path(folder)
        repo = root/'project';repo.mkdir()
        state = root/'private-state'
        env = {**os.environ,'PSTACK_DATA':str(state),'PSTACK_EXECUTION_HOST':'local'}

        def cli(*args, success=True):
            result = subprocess.run([sys.executable,str(RUNTIME),*args],env=env,capture_output=True,text=True,check=False)
            assert (result.returncode == 0) == success, 'Unexpected helper exit status'
            return json.loads(result.stdout)

        initial = cli('setup','--host','local')
        assert initial['preferences']['requires_budget_choice'] and initial['preferences']['budget'] is None
        blocked = cli('call','pstack_environment','plan',json.dumps({'role':'coding'}),success=False)
        assert 'Choose a reasoning budget' in blocked['error']
        cli('setup','--host','local','--budget','small')
        assert cli('call','pstack_environment','preferences')['budget'] == 'small'
        cli('setup','--host','local')
        assert cli('call','pstack_environment','preferences')['budget'] == 'small'
        cli('setup','--host','local','--budget','medium')
        assert cli('call','pstack_environment','preferences')['budget'] == 'medium'
        assert not (state/'supervisor.json').exists()
        subprocess.run(['git','init','-q',str(repo)],check=True)
        subprocess.run(['git','-C',str(repo),'config','user.name','Synthetic fixture'],check=True)
        subprocess.run(['git','-C',str(repo),'config','user.email','fixture@example.com'],check=True)
        (repo/'verify.py').write_text('assert 2 + 2 == 4\nprint("FRESH_SETUP_VERIFIED")\n')
        subprocess.run(['git','-C',str(repo),'add','verify.py'],check=True)
        subprocess.run(['git','-C',str(repo),'commit','-qm','Synthetic fixture'],check=True)
        proof = cli('call','pstack_verify','run',json.dumps({'workspace':str(repo),'argv':[sys.executable,'verify.py'],'method':'real synthetic behavior command','lane':'unit'}))
        assert proof['state'] == 'PASS' and proof['proof']['exit_code'] == 0
        checkpoint = cli('call','pstack_checkpoint','save',json.dumps({'workspace':str(repo),'intent':'fresh setup fixture','progress':'verified','verified':[proof['id']],'next_steps':'none','key_files':['verify.py']}))
        recovered = cli('call','pstack_checkpoint','recover',json.dumps({'workspace':str(repo)}))
        assert any(row['id'] == checkpoint['id'] for row in recovered['checkpoints'])
        assert not (state/'supervisor.json').exists()
    print(json.dumps({'fresh_budget_unselected':True,'planning_requires_choice':True,'budget_persists_and_can_change':True,'real_verification':'PASS','fresh_process_recovery':True,'daemon_started':False,'provider_invoked':False}))


if __name__ == '__main__':
    main()
