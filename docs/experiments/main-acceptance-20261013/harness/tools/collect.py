"""Preserve source identity and original build/test artifacts, without rewriting them."""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess

out = Path('/review')
source = Path('/main-source')
def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

before = json.loads((out / 'source-files-before.json').read_text())
tracked = subprocess.check_output(['git', 'ls-files', '-z'], cwd=source).decode().split('\0')
tracked = [p for p in tracked if p]
rows = [{'path': p, 'sha256': digest(source / p)} for p in tracked]
changed = [r['path'] for r in rows if before.get(r['path']) != r['sha256']]
diff = subprocess.check_output(['git', 'diff', 'HEAD', '--'], cwd=source).decode()
(out / 'source-integrity.json').write_text(json.dumps({'sha': subprocess.check_output(
    ['git', 'rev-parse', 'HEAD'], cwd=source, text=True).strip(), 'tracked_files': rows,
    'changed_from_before': changed, 'git_diff': diff}, indent=2) + '\n')
assert not changed and not diff, changed
copies = []
binaries = []
for base in [Path('/main-build'), Path('/main-ubsan-build')]:
    for path in sorted(base.rglob('*')):
        if not path.is_file() or path.is_symlink():
            continue
        rel = path.relative_to(base)
        if (path.suffix == '.xml' and ('test_results' in path.parts or 'Testing' in path.parts or path.name == 'pytest.xml') or
            path.name in ('compile_commands.json', 'CMakeCache.txt', 'link.txt', 'LastTest.log', 'LastTestsFailed.log', 'CTestTestfile.cmake') or
            (path.suffix == '.txt' and 'ament_cmake_gtest' in path.parts)):
            target = out / 'artifacts' / base.name / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(path, target)
            copies.append({'source': str(path), 'evidence': str(target.relative_to(out)), 'sha256': digest(path)})
        elif path.name.startswith('test_') and len(rel.parts) == 2 or path.suffix == '.so':
            binaries.append({'path': str(path), 'sha256': digest(path), 'size_bytes': path.stat().st_size})
(out / 'artifact-copies.json').write_text(json.dumps(copies, indent=2) + '\n')
(out / 'binary-identity.json').write_text(json.dumps(binaries, indent=2) + '\n')
print('Tracked source unchanged', len(rows), 'artifact copies', len(copies), 'binaries', len(binaries))
