from pathlib import Path
p=Path('mid_viva_artifacts/build/blue_revision')
s=(p/'build_blue.mjs').read_text(encoding='utf-8')
for a,b in [("file:'om_cutout.png',x:64","file:'om_cutout.png',x:455"),("file:'rikin_cutout.png',x:455","file:'rikin_cutout.png',x:846"),("file:'santosh_cutout.png',x:846","file:'santosh_cutout.png',x:64"),('EEG_Sleep_Mid_Viva_Blue_15_Slides_Final.pptx','EEG_Sleep_Mid_Viva_Blue_15_Slides_Mentor_First_Final.pptx'),('validation-blue15-final.json','validation-mentor-first-final.json')]:s=s.replace(a,b)
(p/'build_mentor_first.mjs').write_text(s,encoding='utf-8')
r=Path('mid_viva_artifacts/build/render_mentor_first.ps1')
r.write_text(r.read_text(encoding='utf-8-sig').replace('EEG_Sleep_Mid_Viva_Blue_15_Slides_Mentor_First','EEG_Sleep_Mid_Viva_Blue_15_Slides_Mentor_First_Final'),encoding='utf-8-sig')
