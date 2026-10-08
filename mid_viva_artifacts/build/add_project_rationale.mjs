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
const BUILD=path.join(ROOT,'mid_viva_artifacts/build/rationale_revision');
const OUT=path.join(ROOT,'mid_viva_artifacts/output');
await fs.mkdir(BUILD,{recursive:true});
const source=path.join(OUT,'EEG_Sleep_Mid_Viva_12_Slides_Reviewed.pptx');
const sourceSha256=createHash('sha256').update(await fs.readFile(source)).digest('hex');
const p=await PresentationFile.importPptx(await FileBlob.load(source));
if(p.slides.items.length!==12)throw new Error('Expected reviewed 12-slide source');
await fs.writeFile(path.join(BUILD,'source-inspection.ndjson'),(await p.inspect({kind:'slide,textbox,table,chart,notes,layout',maxChars:100000})).ndjson);
const C={bg:'#F5FAFC',ink:'#102E49',muted:'#526977',teal:'#18A69B',light:'#E8F2F5',white:'#FFFFFF'};
function text(s,v,x,y,w,h,z=25,b=false,c=C.ink){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=v;q.text.style={typeface:'Arial',fontSize:z,bold:b,color:c,autoFit:'none',alignment:'left',verticalAlignment:'top',insets:{left:0,right:0,top:0,bottom:0}};return q;
}
function base(s,title,src){
 s.shapes.deleteAll();for(const kind of ['images','tables','charts'])for(const q of [...s[kind].items])s[kind].deleteById(q.id);
 s.background.fill=C.bg;
 s.shapes.add({geometry:'rect',position:{left:0,top:0,width:12,height:720},fill:C.teal,line:{fill:C.teal,width:1.5}});
 text(s,title,64,36,1150,80,36,true);
 s.shapes.add({geometry:'line',position:{left:64,top:130,width:1148,height:0},fill:'none',line:{fill:C.teal,width:2}});
 text(s,src,64,684,1070,22,12,false,C.muted);
}
const rationale=p.slides.items[1];
base(rationale,'Why detect sleep stages? Why this project?','Sources: NIH sleep education; U-Sleep (2021); verified project artifacts');
text(rationale,'Sleep supports memory, learning and physical health.',64,163,1140,45,29,true);
text(rationale,'Duration alone does not show when sleep is interrupted or how stages are distributed.',64,217,1140,70,25,false,C.muted);
text(rationale,'What stage detection gives us',64,324,545,40,27,true,C.teal);
text(rationale,'Sleep onset and Wake time → continuity\nN1 / N2 / N3 / REM time → architecture\nA hypnogram → when patterns change',64,389,545,143,25);
text(rationale,'Why we chose this project',674,324,534,40,27,true,C.teal);
text(rationale,'EEG records brain activity used in staging.\nHMC provides labels to test our predictions.\nN1/N2 confusion is a measurable target.',674,389,534,143,25);
text(rationale,'Potential benefit: assist sleep-study review and quantify patterns for research.',64,573,1140,45,25,true,C.teal);
text(rationale,'Our contribution: targeted refinement + descriptive profiles. Stage labels alone do not diagnose disease.',64,633,1140,41,21,false,C.muted);
rationale.speakerNotes.textFrame.setText(
 'Why the project exists: Sleep supports learning, memory and physical health. Time asleep does not describe interruptions or stage distribution. Sleep staging creates a hypnogram and enables onset, Wake after sleep onset, stage durations and stage proportions to be measured. These measurements describe sleep organization and can support research and expert sleep-study review.\n\n'+
 'Why choose this engineering project: EEG provides brain activity used in staging; the public HMC dataset provides expert labels for reproducible testing. Our saved baseline has 506 true N2 epochs predicted as N1, giving a specific, measurable weakness to investigate with complementary spectral features. N1/N2 errors can distort their proportions and transition counts. Relabeling between two sleep stages does not change total sleep time or efficiency. This is the reason for targeted refinement rather than a general claim of improving every aspect of sleep quality.\n\n'+
 'Potential users: researchers analyzing recordings and, after suitable external and clinical validation, experts reviewing sleep studies. Automation could reduce repetitive scoring work; this project has not measured clinician time savings or demonstrated clinical utility. It does not infer apnea, diagnose disease, or prescribe treatment. Those tasks require appropriate additional measurements and validation. Research reference profiles are not healthy normative judgments.\n\n'+
 'Sources:\nhttps://www.nhlbi.nih.gov/health/sleep/why-sleep-important\nhttps://www.nhlbi.nih.gov/health/sleep/stages-of-sleep\nhttps://www.nature.com/articles/s41746-021-00440-5\nhttps://physionet.org/content/hmc-sleep-staging/1.1/\nBiomarker_N1_N2_Refinement.ipynb; refinement_artifacts/verified/final_results.json and confusion matrices.');

// Duplicate the edited source slide to retain its master/layout, then insert directly after it.
const stage=rationale.duplicate();
stage.moveTo(2);
if(p.slides.items[2].id!==stage.id){stage.moveTo(3);}
if(p.slides.items[2].id!==stage.id)throw new Error('Could not insert the stage explanation as slide 3');
base(stage,'Sleep stages and what a sleep cycle means','Sources: NIH / NHLBI Sleep Phases and Stages; NIH / NICHD What happens during sleep?');
const values=[['Stage','What it means','Why we measure it'],
 ['Wake','Awake before or between\nsleep periods','Sleep onset and interruptions'],
 ['N1','Transition from Wake\nto light sleep','Onset of sleep; distinguish N1 from N2'],
 ['N2','Light non-REM sleep;\nbrain activity slows','Time in N2; our refinement target'],
 ['N3','Deep, slow-wave sleep;\nsupports restoration','Time spent in deep sleep'],
 ['REM','Active brain, rapid eye movements;\ndreaming is common','Timing and duration of REM sleep']];
const t=stage.tables.add({rows:values.length,columns:3,left:64,top:171,width:1148,height:411,columnWidths:[135,510,503],values});
for(let i=0;i<values.length;i++)for(let j=0;j<3;j++){
 const c=t.getCell(i,j);c.fill=i===0?C.ink:(i%2?C.white:C.light);c.text.style={typeface:'Arial',fontSize:23,bold:i===0||j===0,color:i===0?C.white:C.ink,autoFit:'none'};
}
text(stage,'A cycle combines NREM and REM; these stages recur across the night.',64,609,1140,35,25,true,C.teal);
text(stage,'Typically, more N3 occurs early and REM periods lengthen later. Both phases support learning and memory.',64,650,1140,27,19,false,C.muted);
stage.speakerNotes.textFrame.setText(
 'Explain the distinction: N1, N2 and N3 are stages of non-REM sleep, and REM is the other sleep phase. Wake is an additional class used to score awake epochs; it is not a sleep stage. A sleep cycle is a repeating combination of NREM and REM, not a synonym for one stage. The real sequence varies and can include returns to lighter stages and brief awakenings. The current system classifies 30-second epochs and displays their sequence; it does not separately validate or count complete physiological cycles.\n\n'+
 'N1 is the transition into light sleep. N2 is light non-REM sleep with slower brain activity. N3 is deep slow-wave sleep and supports restoration. REM includes active brain activity, rapid eye movements and frequent vivid dreaming. N3 generally occupies more time early in the night; REM periods generally become longer later. Both non-REM and REM support learning and memory, so no single stage is a complete measure of sleep quality. Stage patterns vary with age and other factors. These are general physiology descriptions, not healthy threshold rules for this project. Eye movement and muscle tone are physiological characteristics; the current four-channel EEG classifier infers the stage and does not measure those signals directly.\n\n'+
 'Practical link: Wake epochs yield sleep onset and interruptions; sleep labels yield stage time and architecture. Confusing N1 and N2 changes the estimated architecture, motivating our focused refinement. Classifying stages is a prerequisite for useful descriptive summaries, while evidence for diagnosis or treatment remains separate.\n\n'+
 'Sources:\nhttps://www.nhlbi.nih.gov/health/sleep/stages-of-sleep\nhttps://www.nichd.nih.gov/health/topics/sleep/conditioninfo/Pages/what-happens.aspx\nhttps://www.nhlbi.nih.gov/health/sleep/why-sleep-important');

// Update all existing page markers; all other source content stays in its original sequence.
for(const [i,s] of p.slides.items.entries()){
 let found=false;
 for(const q of s.shapes.items){if(q.position.left>1160&&q.position.top>675){q.text=`${String(i+1).padStart(2,'0')} / 13`;found=true;}}
 if(!found)text(s,`${String(i+1).padStart(2,'0')} / 13`,1178,684,72,22,12,false,C.muted);
}
const cand=path.join(BUILD,'candidate-13.pptx');
await (await PresentationFile.exportPptx(p)).save(cand);
console.log(execFileSync(R+'/python/python.exe',[path.join(BUILD,'preserve_chart_parts.py'),source,cand],{encoding:'utf8'}).trim());
const final=path.join(OUT,'EEG_Sleep_Mid_Viva_13_Slides.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:cand,finalPath:final,pythonExecutable:R+'/python/python.exe',integrityValidatorPath:SK+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SK+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','3','--require-native-table-slide','4','--require-native-table-slide','5','--require-native-table-slide','9'],explicitTotalSlideCount:13,requiredNativeTableOwnerSlides:[3,4,5,9],requiredNativeChartOwnerSlides:[8,10],fontPolicy:{basis:'reference',families:['Arial'],referencePath:source,referenceSha256:sourceSha256},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation-13.json')});
await fs.writeFile(path.join(BUILD,'final-inspection.ndjson'),(await p.inspect({kind:'slide,textbox,table,chart,notes',maxChars:100000})).ndjson);
console.log('Revised deck: '+final);
