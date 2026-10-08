import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
import {createHash} from 'node:crypto';
import {execFileSync} from 'node:child_process';
const ROOT=path.resolve('.');
const R='C:/Users/Rikin Parekh/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const SK='C:/Users/Rikin Parekh/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.11814/skills/presentations';
process.env.RUNTIME_NODE_MODULES=R+'/node/node_modules';
const {PresentationFile,FileBlob}=await import(pathToFileURL(R+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const {finalizePresentation}=await import(pathToFileURL(SK+'/container_tools/artifact_tool_utils.mjs').href);
const BUILD=path.join(ROOT,'mid_viva_artifacts/build/blue_revision');
const OUT=path.join(ROOT,'mid_viva_artifacts/output');
const source=path.join(OUT,'EEG_Sleep_Mid_Viva_13_Slides.pptx');
const sourceSha256=createHash('sha256').update(await fs.readFile(source)).digest('hex');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
const C={bg:'#0E2C50',ink:'#FFFFFF',muted:'#BED0E4',accent:'#75D5FF'};
function text(s,v,x,y,w,h,z=25,b=false,c=C.ink,align='left'){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=v;q.text.style={typeface:'Arial',fontSize:z,bold:b,color:c,autoFit:'none',alignment:align,verticalAlignment:'top',insets:{left:0,right:0,top:0,bottom:0}};return q;
}
function base(s,title,src){
 s.shapes.deleteAll();for(const kind of ['images','tables','charts'])for(const q of [...s[kind].items])s[kind].deleteById(q.id);
 s.background.fill=C.bg;
 s.shapes.add({geometry:'rect',position:{left:0,top:0,width:12,height:720},fill:C.accent,line:{fill:C.accent,width:1.5}});
 text(s,title,64,36,1150,80,36,true);
 s.shapes.add({geometry:'line',position:{left:64,top:130,width:1148,height:0},fill:'none',line:{fill:C.accent,width:2}});
 text(s,src,64,684,1070,22,12,false,C.muted);
}
const abstract=p.slides.items[1].duplicate();abstract.moveTo(1);
base(abstract,'Abstract','Source: Biomarker_N1_N2_Refinement.ipynb and verified held-out results');
const sections=[
 ['BACKGROUND','Sleep-stage sequences describe sleep continuity and architecture. N1/N2 confusion can distort these profiles.',64,181],
 ['METHOD','Four-channel EEG is scored in 30-second epochs. A retained hybrid model is refined using nine spectral features and logistic regression.',674,181],
 ['RESULTS','On the same 3,109 test epochs, accuracy rose from 55.45% to 59.34%; macro-F1 rose from 57.42% to 59.51%.',64,403],
 ['FUTURE WORK','Develop coarse and NREM specialist models, combine their probabilities, add temporal context, and validate on external recordings.',674,403]
];
for(const [label,body,x,y] of sections){text(abstract,label,x,y,534,40,25,true,C.accent);text(abstract,body,x,y+56,534,154,25);}
abstract.speakerNotes.textFrame.setText('Background: sleep staging supports descriptive sleep architecture; the project does not diagnose disorders. Method: the saved Fast SCFormer-U classifier uses four-channel 100 Hz EEG, 30-second epochs, with Conv1D, self-attention and BiLSTM within an epoch. The refinement uses nine spectral features, StandardScaler and balanced logistic regression; training uses training recordings only and inference gates on predicted N1/N2. Results are measured on the identical 3,109 held-out epochs: accuracy 55.4519% to 59.3438% (+3.89 percentage points); macro-F1 57.4155% to 59.5122% (+2.10 percentage points). Future work is proposed, not implemented: hierarchical coarse and NREM experts, probabilistic composition, optional baseline fusion, temporal context and external validation. Sources: Biomarker_N1_N2_Refinement.ipynb; refinement_artifacts/verified/final_results.json.');
p.slides.items[0].images.add({blob:await fs.readFile(path.join(ROOT,'pdeuofficial_logo.jpg')),contentType:'image/jpeg',alt:'Official PDEU logo supplied by the project team',fit:'contain',position:{left:1078,top:27,width:130,height:130}});
const team=p.slides.items[1].duplicate();team.moveTo(14);
base(team,'Team members and project mentor','Information and Communication Technology · Pandit Deendayal Energy University');
const members=[
 {name:'Om Ahuja',role:'TEAM MEMBER',id:'23BIT014',file:'om_cutout.png',x:455,crop:{left:0,top:0,right:0,bottom:0.32}},
 {name:'Rikin Parekh',role:'TEAM MEMBER',id:'23BIT044',file:'rikin_cutout.png',x:846,crop:{left:0,top:0.06,right:0,bottom:0.08}},
 {name:'Dr. Santosh Sathpathy',role:'PROJECT MENTOR',id:'Project guide',file:'santosh_cutout.png',x:64,crop:{left:0,top:0,right:0,bottom:0}}
];
for(const m of members){
 text(team,m.role,m.x,174,366,32,20,true,C.accent,'center');
 team.images.add({blob:await fs.readFile(path.join(ROOT,'mid_viva_artifacts/assets',m.file)),contentType:'image/png',alt:m.name+' portrait with transparent background',fit:'contain',crop:m.crop,position:{left:m.x+33,top:227,width:300,height:313}});
 text(team,m.name,m.x,565,366,45,27,true,C.ink,'center');
 text(team,m.id,m.x,615,366,35,23,false,C.muted,'center');
}
team.speakerNotes.textFrame.setText('Team: Om Ahuja (23BIT014) and Rikin Parekh (23BIT044). Project guide: Dr. Santosh Sathpathy. Names and IDs follow the supplied project presentation. Portraits and official logo were supplied by the user. Portrait backgrounds were removed with imagegen; the logo artwork was preserved.');
for(const [i,s] of p.slides.items.entries()){
 s.background.fill=C.bg;let found=false;
 for(const q of s.shapes.items){if(q.position.left>1160&&q.position.top>675){q.text=`${String(i+1).padStart(2,'0')} / 15`;found=true;}}
 if(!found)text(s,`${String(i+1).padStart(2,'0')} / 15`,1178,684,72,22,12,false,C.muted);
}
const cand=path.join(BUILD,'candidate-blue15.pptx');
await (await PresentationFile.exportPptx(p)).save(cand);
console.log(execFileSync(R+'/python/python.exe',[path.join(BUILD,'theme.py'),source,cand],{encoding:'utf8'}).trim());
const final=path.join(OUT,'EEG_Sleep_Mid_Viva_Blue_15_Slides_Mentor_First_Final.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:cand,finalPath:final,pythonExecutable:R+'/python/python.exe',integrityValidatorPath:SK+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SK+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','4','--require-native-table-slide','5','--require-native-table-slide','6','--require-native-table-slide','10'],explicitTotalSlideCount:15,requiredNativeTableOwnerSlides:[4,5,6,10],requiredNativeChartOwnerSlides:[9,11],fontPolicy:{basis:'reference',families:['Arial'],referencePath:source,referenceSha256:sourceSha256},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation-mentor-first-final.json')});
console.log('Final: '+final);
