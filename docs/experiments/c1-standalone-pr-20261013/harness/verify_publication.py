"""Check both C1 evidence sets, scoped publication, and preserved UI staging."""
import hashlib
import json
import re
import subprocess
from pathlib import Path

run = Path(__file__).resolve().parents[1]
project = run.parents[1]
original_run = project / 'outputs/c1-cancel-fix-20261013'
publication = original_run / 'publication'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sections = ['sources', 'project_decisions', 'external_references', 'local_observations']
data = json.loads((publication / 'materials/manifest.json').read_text())
identities = [e['id'] for section in sections for e in data[section]]
assert len(identities) == len(set(identities)), 'duplicate source IDs'
pattern = r'USER-[A-Z]+-[0-9]{8}(?:-[0-9]+)?|(?:VAC|AUBO|RS|CV)-[A-Z0-9]+|(?:VISION|ROBUST|DEMO|ENV|SPRINT)-[A-Z-]+-[0-9]{8}|CTRL-[A-Z]+-[0-9]{4}|TEAMMATE-[A-Z]+-[0-9]{8}|POLYU-[A-Z0-9]+(?:-[A-Z0-9]+)*'
files = [publication / 'README.md', publication / 'materials/README.md']
for directory in ['docs', 'demo', 'robot']:
    files.extend((publication / directory).glob('*.md'))
references = {identity for path in files for identity in re.findall(pattern, path.read_text())}
assert not references - set(identities), sorted(references - set(identities))
indices, members = [], {}
for section in ['sources', 'local_observations']:
    for entry in data[section]:
        if entry.get('index') and entry.get('index_sha256'):
            path = publication / entry['index']
            assert sha(path) == entry['index_sha256'], path
            indices.append(entry['id'])
            if entry['id'] not in {'ENV-CANCEL-FIX-20261013', 'ENV-CANCEL-PR-20261013'}:
                continue
            assert sha(project / entry['index']) == entry['index_sha256']
            index = json.loads(path.read_text())
            members[entry['id']] = len(index['files'])
            for item in index['files']:
                p = path.parent / item['path']
                assert p.stat().st_size == item['size'] and sha(p) == item['sha256'], p
                assert sha(project / p.relative_to(publication)) == item['sha256'], p
assert sha(publication / 'docs/experiments/c1-cancel-fix-20261013/index.json') == '4ac6577e8dcb81d2e1194ac7d4590eac3e71ed60b046a3d99f019a9e439b816b'
new_ids = {'USER-HW-20261013-03', 'TEAMMATE-CANCELFIX-20261013', 'ENV-CANCEL-FIX-20261013',
           'TEAMMATE-CANCELPR-20261013', 'ENV-CANCEL-PR-20261013'}
base = json.loads(subprocess.check_output(['git', '-C', str(publication), 'show', 'HEAD:materials/manifest.json']))
for key in base:
    current = data[key]
    if key in sections:
        current = [e for e in current if e.get('id') not in new_ids]
    assert current == base[key], key
for section in sections:
    for entry in data[section]:
        if entry['id'] in new_ids:
            for name in entry['derived_files']:
                assert (publication / name).is_file(), name
initial = json.loads((original_run / 'meta/initial-state.json').read_text())
assert sha(project / 'robot/fsm-baseline.repos') == initial['formal_pin_sha256']
assert hashlib.sha256(subprocess.check_output(['git', '-C', str(project), 'diff', '--cached', '--binary'])).hexdigest() == initial['index_patch_sha256']
assert (project / 'webui/p1-contract.md').is_file()
local = json.loads((project / 'materials/manifest.json').read_text())
assert 'P1：' in next(e['original_text'] for e in local['project_decisions'] if e['id'] == 'USER-HW-20261013-02')
assert sha(project / 'docs/c1-cancel-fix.md') == sha(publication / 'docs/c1-cancel-fix.md')
pr = json.loads((run / 'meta/standalone-pr.json').read_text())
assert pr['number'] == 15 and len(pr['commits']) == 1 and len(pr['files']) == 9
result = dict(status='PASS', registered_indices_verified=len(indices), frozen_members=members,
              source_identifiers_registered=True, preexisting_manifest_entries_unchanged=True,
              preexisting_staging_unchanged=True, p1_work_preserved=True, formal_pin_unchanged=True,
              pr_url=pr['url'], pr_commits=1, pr_files=9)
(run / 'pre-publication-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
