from pathlib import Path
from PIL import Image,ImageDraw
import re
ROOT=Path(__file__).resolve().parent
for parent in ['source_renders','renders']:
    if not (ROOT/parent).exists():continue
    for d in (ROOT/parent).iterdir():
        if not d.is_dir():continue
        files=sorted([p for p in d.iterdir() if p.suffix.lower()=='.png'],key=lambda p:int(re.search(r'(\d+)',p.stem)[1]))
        if not files:continue
        for page in range((len(files)+11)//12):
            group=files[page*12:(page+1)*12];canvas=Image.new('RGB',(1600,3*250),'#dce5eb');draw=ImageDraw.Draw(canvas)
            for i,p in enumerate(group):
                im=Image.open(p).convert('RGB');im.thumbnail((395,223));x=i%4*400;y=i//4*250+23
                canvas.paste(im,(x,y));draw.text((x+5,y-19),p.stem,fill='black')
            canvas.save(d/f'contact_{page+1}.jpg',quality=93)
print('Prepared contact sheets for all available slides.')
