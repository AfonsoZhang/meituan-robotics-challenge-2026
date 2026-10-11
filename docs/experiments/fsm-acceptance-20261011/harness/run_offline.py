#!/usr/bin/env python3
"""Local acceptance harness, OpenAI Codex assisted, 2026-10-11.

Runs unmodified upstream offline tests; does not start ROS nodes or hardware.
"""
from pathlib import Path
import datetime
import hashlib
import json
import os
import subprocess
import xml.etree.ElementTree as ET

RUN = Path(__file__).resolve().parent
SRC = RUN / 'source'
env = os.environ.copy()
env.update(PYTHONNOUSERSITE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
           PYTHONDONTWRITEBYTECODE='1',
           PYTHONPATH=':'.join(str(p) for p in sorted((SRC/'src').iterdir()) if p.is_dir()))
records = []

def run(name, argv, timeout=180):
    started = datetime.datetime.now().astimezone().isoformat()
    p = subprocess.run(argv, cwd=SRC, env=env, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True, timeout=timeout)
    log = RUN/'logs'/f'{name}.log'
    log.write_text(p.stdout)
    row = dict(name=name, argv=argv, cwd=str(SRC), started_at=started,
               exit_code=p.returncode, log=str(log.relative_to(RUN)),
               log_sha256=hashlib.sha256(log.read_bytes()).hexdigest())
    records.append(row)
    (RUN/'artifacts'/'offline-commands.json').write_text(
        json.dumps({'environment_overrides':{k:env[k] for k in ('PYTHONNOUSERSITE',
                  'PYTEST_DISABLE_PLUGIN_AUTOLOAD','PYTHONDONTWRITEBYTECODE','PYTHONPATH')},
                    'commands':records}, ensure_ascii=False, indent=2)+'\n')
    print(name, p.returncode, p.stdout[-1000:], flush=True)
    return p

run('source-identity', ['git','rev-parse','HEAD'])
run('source-status-before', ['git','status','--porcelain'])
run('package-list', ['colcon','list','--base-paths','src'])
run('python-version', ['/usr/bin/python3','-s','--version'])
run('pytest-version', ['/usr/bin/python3','-s','-m','pytest','--version'])
totals = dict(tests=0, failures=0, errors=0, skipped=0)
packages=[]
for package in ('mtc_aubo_bridge','mtc_manipulation','mtc_motion_execution',
                'mtc_safety','mtc_task','mtc_tool'):
    xml=RUN/'artifacts'/f'{package}-pytest.xml'
    result=run(package+'-pytest', ['/usr/bin/python3','-s','-m','pytest','-q',
               '-p','no:cacheprovider',str(SRC/'src'/package/'test'),
               '--junitxml='+str(xml)])
    root=ET.parse(xml).getroot()
    suites=[root] if root.tag=='testsuite' else list(root.iter('testsuite'))
    counts={k:sum(int(s.get(k,0)) for s in suites) for k in totals}
    for k in totals: totals[k]+=counts[k]
    packages.append(dict(package=package,exit_code=result.returncode,**counts))
e2e=run('python-mock-e2e',['/usr/bin/python3','-s','tests/test_mock_end_to_end.py'])
run('source-status-after',['git','status','--porcelain'])
(RUN/'artifacts'/'python-summary.json').write_text(json.dumps(
    dict(environment='Ubuntu 22.04.5 WSL2 / Python 3.10.12; no ROS runtime',
         packages=packages, totals=totals, e2e_exit_code=e2e.returncode),indent=2)+'\n')
print(json.dumps(totals),flush=True)
