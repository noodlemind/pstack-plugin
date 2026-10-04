from pathlib import Path
import sys,unittest.mock
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'hooks'))
import lifecycle

def hook_for_test(store,event):
 with unittest.mock.patch.object(lifecycle,'Store',return_value=store):return lifecycle.hook(event)
