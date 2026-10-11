"""Run existing package tests separately to avoid their shared test namespace.

OpenAI Codex assisted acceptance orchestration, 2026-10-11.
"""
import json
from pathlib import Path
import subprocess
import sys
import xml.etree.ElementTree as ET

source = Path('/fix-src')
evidence = Path('/fix-evidence/offline')
evidence.mkdir()
packages = ('mtc_aubo_bridge', 'mtc_manipulation', 'mtc_motion_execution',
            'mtc_safety', 'mtc_task', 'mtc_tool')
records = []
for package in packages:
    xml = evidence / (package + '.xml')
    argv = [sys.executable, '-m', 'pytest', '-q', '-p', 'no:cacheprovider',
            str(source / 'src' / package / 'test'), '--junitxml=' + str(xml)]
    completed = subprocess.run(argv, cwd=source, text=True,
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (evidence / (package + '.log')).write_text(completed.stdout)
    suites = list(ET.parse(xml).getroot().iter('testsuite'))
    counts = {key: sum(int(s.get(key, 0)) for s in suites)
              for key in ('tests', 'failures', 'errors', 'skipped')}
    records.append(dict(package=package, argv=argv,
                        exit_code=completed.returncode, **counts))
    print(json.dumps(records[-1]), flush=True)
    if completed.returncode:
        print(completed.stdout, flush=True)
argv = [sys.executable, 'tests/test_mock_end_to_end.py']
completed = subprocess.run(argv, cwd=source, text=True,
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(evidence / 'mock-e2e.log').write_text(completed.stdout)
summary = {'packages': records,
           'totals': {key: sum(r[key] for r in records)
                      for key in ('tests', 'failures', 'errors', 'skipped')},
           'e2e': {'argv': argv, 'exit_code': completed.returncode}}
(evidence / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(completed.stdout, flush=True)
print(json.dumps(summary['totals']), flush=True)
sys.exit(int(bool(completed.returncode or any(r['exit_code'] for r in records))))
