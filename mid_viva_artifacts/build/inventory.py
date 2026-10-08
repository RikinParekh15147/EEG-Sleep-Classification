from pathlib import Path
import zipfile,xml.etree.ElementTree as E,hashlib,json,re
rows=[]
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
for f in sorted(Path('.').rglob('*.pptx')):
    if f.name.startswith('~$'):continue
    with zipfile.ZipFile(f) as z:
        names=sorted([n for n in z.namelist() if re.fullmatch(r'ppt/slides/slide[0-9]+.xml',n)],key=lambda n:int(re.search(r'slide([0-9]+)',n).group(1)))
        titles=[' / '.join([t.text or '' for t in E.fromstring(z.read(n)).findall('.//a:t',ns)][:2]) for n in names]
        rows.append({'path':f.as_posix(),'slides':len(names),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'titles':titles})
Path('mid_viva_artifacts/build/ppt_inventory.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print(json.dumps(rows,ensure_ascii=True))
