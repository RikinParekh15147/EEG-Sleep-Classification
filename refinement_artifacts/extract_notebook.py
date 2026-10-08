"""Extract original saved notebook evidence without rerunning its historical cells."""
import json, hashlib, re, csv, shutil
from pathlib import Path
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'refinement_artifacts'
OUT.mkdir(exist_ok=True)
source=ROOT/'Biomarker_N1_N2_Refinement.ipynb'
n=json.loads(source.read_text(encoding='utf8'))
class Table(HTMLParser):
    def __init__(self): super().__init__(); self.rows=[]; self.row=[]; self.cell=None
    def handle_starttag(self,tag,attrs):
        if tag=='tr': self.row=[]
        if tag in ('th','td'): self.cell=''
    def handle_data(self,data):
        if self.cell is not None:self.cell+=data
    def handle_endtag(self,tag):
        if tag in ('th','td') and self.cell is not None:self.row.append(self.cell.strip());self.cell=None
        if tag=='tr' and self.row:self.rows.append(self.row)
def table(index,last=True):
    outputs=[o for o in n['cells'][index].get('outputs',[]) if 'text/html' in o.get('data',{})]
    t=Table();t.feed(''.join(outputs[-1 if last else 0]['data']['text/html']))
    headers=t.rows[0][1:]
    return [dict(zip(headers,row[1:])) for row in t.rows[1:] if len(row)==len(headers)+1 and row[0]!='...']
def save(name,rows):
    with (OUT/(name+'.csv')).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
    (OUT/(name+'.json')).write_text(json.dumps(rows,indent=2),encoding='utf8')
for i,name in [(38,'master_sleep_health_features'),(41,'train_reference_features'),(42,'reference_stats'),(43,'test_deviation_profiles'),(44,'domain_profiles'),(45,'sleep_health_profiles')]:
    save(name,table(i))
save('subject_performance',table(26))
save('refinement_coefficients',table(22))
for name in ['final_sleep_stage_project_presentation.pptx','sleep_stage_project_12_slides.pptx','mid.original_backup.pptx','final_sleep_stage_project_presentation.pdf','sleep_stage_project_12_slides.pdf']:
    dest=OUT/'originals'/name;dest.parent.mkdir(exist_ok=True)
    if not dest.exists():shutil.copy2(ROOT/name,dest)
ns={'a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
from zipfile import ZipFile
inventory={}
for p in ROOT.glob('*.pptx'):
    with ZipFile(p) as z:
        slides=sorted([s for s in z.namelist() if re.fullmatch(r'ppt/slides/slide\d+\.xml',s)],key=lambda s:int(re.search(r'(\d+)\.xml',s)[1]))
        inventory[p.name]=[' | '.join(t.text or '' for t in ET.fromstring(z.read(s)).findall('.//a:t',ns)) for s in slides]
(OUT/'original_slide_inventory.json').write_text(json.dumps(inventory,indent=2,ensure_ascii=False),encoding='utf8')
(OUT/'notebook_sources.txt').write_text('\n\n'.join(f'CELL {i}\n'+''.join(c['source'])+'\nOUTPUT\n'+'\n'.join(''.join(o.get('text',o.get('data',{}).get('text/plain',[]))) for o in c.get('outputs',[])) for i,c in enumerate(n['cells'][:47])),encoding='utf8')
(OUT/'source_manifest.json').write_text(json.dumps({'source_notebook':source.name,'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'current_pipeline_cells':list(range(1,47)),'historical_cells_start':47,'matrix_numeric_columns':22,'deviation_features':21},indent=2))
print('Extracted notebook evidence; original presentations/PDFs backed up.')
