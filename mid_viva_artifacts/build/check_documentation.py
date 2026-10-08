from pathlib import Path
import re,json,hashlib
s=Path('README.md').read_text(encoding='utf-8')
missing=[]
for target in re.findall(r'\]\(([^)]+)\)',s):
    if target.startswith(('https://','http://','#')):continue
    if not Path(target.split('#')[0]).exists():missing.append(target)
assert not missing,missing
rows=json.loads(Path('mid_viva_artifacts/build/ppt_inventory.json').read_text(encoding='utf-8'))
assert len(rows)==26
assert all('`'+r['path']+'`' in s for r in rows)
for i in range(1,15):
    a=Path(f'mid_viva_artifacts/build/rendersblue15/Slide{i}.PNG').read_bytes()
    b=Path(f'mid_viva_artifacts/build/rendersmentorfirst/Slide{i}.PNG').read_bytes()
    assert hashlib.sha256(a).digest()==hashlib.sha256(b).digest(),f'Unexpected change to slide {i}'
print('README local links resolve; all 26 PowerPoints catalogued; slides 1–14 unchanged in native renders.')
