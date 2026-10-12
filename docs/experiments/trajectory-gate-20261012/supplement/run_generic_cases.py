"""Serial, single-attempt delivered Fake scenarios; stop on incomplete cleanup."""
from pathlib import Path
from datetime import datetime,timezone
import json,subprocess,sys
raw=Path(__file__).resolve().parent;name=json.loads((raw/'runtime.json').read_text())['container']
records=[]
for mode in ['success','mismatch','cancel','identity']:
 top=subprocess.check_output(['docker','top',name,'-eo','pid,ppid,args'],text=True)
 assert len(top.strip().splitlines())==2 and top.strip().endswith('sleep infinity'),top
 label='generic-'+mode
 assert not (raw/'logs'/f'{label}.json').exists(),'No duplicate test'
 code=subprocess.run(['python3',str(raw/'run_step.py'),label,'125',str(raw/(label+'.sh'))],timeout=165).returncode
 content=subprocess.check_output(['docker','exec',name,'cat','/review-evidence/'+label+'/summary.json'],text=True)
 s=json.loads(content);assert s['empty_after'] and s['shutdown']['exit_code']==0 and not s['shutdown']['child_failures'] and not s['shutdown']['escalated']
 records.append({'mode':mode,'exit_code':code,'status':s['status'],'case_exit_codes':[x['exit_code'] for x in s['cases']],'finished_at':datetime.now(timezone.utc).isoformat()})
 (raw/'generic-run-sequence.json').write_text(json.dumps(records,indent=2)+'\n')
 print('SCENARIO_RECORDED',mode,code,s['status'],flush=True)
sys.exit(0 if all(r['exit_code']==0 for r in records) else 1)
