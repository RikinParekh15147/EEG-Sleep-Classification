import fs from 'node:fs/promises';
import path from 'node:path';
import {pathToFileURL} from 'node:url';
const ROOT=path.resolve('.');
const R='C:/Users/Rikin Parekh/.cache/codex-runtimes/codex-primary-runtime/dependencies';
const SK='C:/Users/Rikin Parekh/.codex/plugins/cache/openai-primary-runtime/presentations/26.909.11814/skills/presentations';
process.env.RUNTIME_NODE_MODULES=R+'/node/node_modules';
const {PresentationFile,FileBlob}=await import(pathToFileURL(R+'/node/node_modules/@oai/artifact-tool/dist/artifact_tool.mjs').href);
const {finalizePresentation,applyPresentationChartFont}=await import(pathToFileURL(SK+'/container_tools/artifact_tool_utils.mjs').href);
const BUILD=path.join(ROOT,'mid_viva_artifacts/build'),OUT=path.join(ROOT,'mid_viva_artifacts/output');
await fs.mkdir(BUILD,{recursive:true});await fs.mkdir(OUT,{recursive:true});
const D=path.join(ROOT,'refinement_artifacts/verified');
const results=JSON.parse(await fs.readFile(path.join(D,'final_results.json'),'utf8'));
const hparams=JSON.parse(await fs.readFile(path.join(D,'hyperparameters.json'),'utf8'));
const history=(await fs.readFile(path.join(D,'training_history.csv'),'utf8')).trim().split(/\r?\n/).slice(1).map(l=>l.split(',').map(Number));
const source=path.join(ROOT,'sleep_stage_project_12_slides.pptx');
const pres=await PresentationFile.importPptx(await FileBlob.load(source));
if(pres.slides.items.length!==12)throw new Error('Expected 12 source slides');
await fs.writeFile(path.join(BUILD,'source-inspection.ndjson'),(await pres.inspect({kind:'slide,textbox,table,image,layout',maxChars:50000})).ndjson);
const C={bg:'#F5FAFC',ink:'#102E49',muted:'#526977',teal:'#18A69B',light:'#E8F2F5',white:'#FFFFFF'};
const refs={deep:'https://arxiv.org/abs/1703.04046',seq:'https://arxiv.org/abs/1809.10932',robust:'https://arxiv.org/abs/2101.02452',u:'https://www.nature.com/articles/s41746-021-00440-5',sleepy:'https://arxiv.org/abs/2506.08574',long:'https://arxiv.org/abs/2301.03441',hmc:'https://physionet.org/content/hmc-sleep-staging/1.1/'};
const slides=pres.slides.items;
function text(s,v,x,y,w,h,z=25,b=false,c=C.ink,align='left'){
 const q=s.shapes.add({geometry:'textbox',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
 q.text=v;q.text.style={typeface:'Arial',fontSize:z,bold:b,color:c,autoFit:'none',alignment:align,verticalAlignment:'top',insets:{left:0,right:0,top:0,bottom:0}};return q;
}
function shape(s,g,x,y,w,h,fill=C.light,line=C.teal){return s.shapes.add({geometry:g,position:{left:x,top:y,width:w,height:h},fill,line:{fill:line,width:1.5}});}
function block(s,label,x,y,w,h,accent=false,size=23,g='rect'){
 const q=shape(s,g,x,y,w,h,accent?C.ink:C.light,accent?C.ink:C.teal);q.text=label;
 q.text.style={typeface:'Arial',fontSize:size,bold:true,color:accent?C.white:C.ink,autoFit:'none',alignment:'center',verticalAlignment:'middle',insets:{left:10,right:10,top:8,bottom:8}};return q;
}
function arrow(s,x,y,w=34,h=20,down=false){return shape(s,down?'downArrow':'rightArrow',x,y,w,h,C.teal,C.teal);}
function line(s,x,y,w,h=0){return s.shapes.add({geometry:'line',position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:C.teal,width:2}});}
function base(n,title,src='Notebook + verified run HMC-N1N2-20261007'){
 const s=slides[n-1];s.shapes.deleteAll();for(const kind of ['images','tables','charts'])for(const o of [...s[kind].items])s[kind].deleteById(o.id);
 s.background.fill=C.bg;shape(s,'rect',0,0,12,720,C.teal,C.teal);
 text(s,title,64,36,1150,80,36,true);line(s,64,130,1148);
 text(s,src,64,684,1070,22,12,false,C.muted);text(s,`${String(n).padStart(2,'0')} / 12`,1178,684,72,22,12,false,C.muted);
 return s;
}
function note(s,v,urls=[]){s.speakerNotes.textFrame.setText(v+'\n\nProject evidence: Biomarker_N1_N2_Refinement.ipynb; refinement_artifacts/verified; independent reproduction HMC-N1N2-20261007.\n'+urls.join('\n'));}
function table(s,values,x,y,w,h,widths,size=23){
 const t=s.tables.add({rows:values.length,columns:values[0].length,left:x,top:y,width:w,height:h,columnWidths:widths,values});
 for(let i=0;i<values.length;i++)for(let j=0;j<values[0].length;j++){
  const c=t.getCell(i,j);c.fill=i===0?C.ink:(i%2?C.white:C.light);c.text.style={typeface:'Arial',fontSize:size,bold:i===0,color:i===0?C.white:C.ink,autoFit:'none'};
 }
 return t;
}
async function image(s,file,x,y,w,h){s.images.add({blob:await fs.readFile(file),contentType:'image/png',alt:path.basename(file),fit:'contain',position:{left:x,top:y,width:w,height:h}});}
function chartFont(c){for(const series of c.series.items)series.values=series.values.map(v=>Number(v.toFixed(10)));applyPresentationChartFont(c,{fontFamily:'Arial'});}

// 1: Reuse source title identity and theme; update review scope.
{
 const s=base(1,'');
 text(s,'MID-VIVA • PROJECT PROGRESS',64,50,1120,35,18,true,C.teal);
 text(s,'EEG Sleep Classification and\nReference-Based Sleep-Health Profiling',64,125,1136,140,42,true);
 text(s,'Biomarker-assisted N1/N2 refinement',64,300,1110,48,28,false,C.muted);
 text(s,'Rikin Parekh · Om Ahuja\n23BIT044 · 23BIT014\nGuide: Dr. Santosh Sathpathy\nInformation and Communication Technology\nPandit Deendayal Energy University',64,420,1100,180,22);
 note(s,'Opening: Our project classifies five sleep stages, adds a targeted spectral refiner for N1/N2, and derives descriptive recording profiles. This is a progress presentation. The main implementation is the biomarker N1/N2 refinement notebook. Names and institutional details are retained from the existing deck.');
 // Remove standard title divider on the minimal cover.
 for(const q of [...s.shapes.items])if(q.position.top===130)s.shapes.deleteById(q.id);
}
// 2: Introduction, motivation and implemented objectives.
{
 const s=base(2,'Introduction, motivation and objectives','Context: U-Sleep (2021), RobustSleepNet (2021); project notebook');
 text(s,'Sleep staging assigns a label to each 30-second EEG segment.',64,164,1120,50,28,true);
 const labels=['Wake','N1','N2','N3','REM'];labels.forEach((v,i)=>{block(s,v,64+i*235,242,205,65,i===2,27);});
 text(s,'Motivation',64,365,330,42,27,true,C.teal);
 text(s,'Manual scoring takes time.\nN1/N2 discrimination remains\na difficult part of automation.',64,426,345,130,25);
 text(s,'Research question',455,365,330,42,27,true,C.teal);
 text(s,'Can spectral EEG features\ncomplement the existing\nfive-stage classifier?',455,426,350,130,25);
 text(s,'Current objectives',850,365,350,42,27,true,C.teal);
 text(s,'Improve N1/N2 labels.\nGenerate a hypnogram.\nSummarize recording profiles.',850,426,350,130,25);
 text(s,'Five output classes represent Wake, three NREM stages, and REM sleep.',64,624,1140,35,20,false,C.muted);
 note(s,'EEG measures electrical activity at scalp electrodes; sleep staging turns successive epochs into a hypnogram. The objective is complementary spectral information for N1/N2, rather than an unsupported claim of diagnostic accuracy. The project extends an existing saved classifier. The stage strip lists classes; the arrows represent the label sequence concept, not physiologically mandatory transitions.',[refs.u,refs.robust]);
}
// 3: Literature review, directly tied to proposed design.
{
 const s=base(3,'Literature review and project direction','Selected primary papers; full citations and links in speaker notes');
 table(s,[['Study','Main contribution','Relevance to our project'],
 ['DeepSleepNet\nSupratak et al., 2017','CNN features + BiLSTM\nacross EEG epochs','Compare a learned\nsequence-context baseline'],
 ['SeqSleepNet\nPhan et al., 2019','Hierarchical recurrent\nsequence-to-sequence staging','Add context between epochs;\ncurrent model is within-epoch'],
 ['U-Sleep\nPerslev et al., 2021','Fully convolutional staging\nacross clinical cohorts','Test transfer and robustness\non a separate dataset'],
 ['RobustSleepNet\nGuillot & Thorey, 2021','Montage flexibility and\nleave-one-dataset-out testing','Check channel compatibility\nand external generalization'],
 ['SLEEPYLAND\nDei Rossi et al., 2025*','Standardized evaluation;\nSOMNUS soft-voting ensemble','Test model fusion and\ncalibrate the final output']],64,168,1148,420,[330,410,408],22);
 text(s,'Design direction: targeted experts + sequence context + fair external evaluation',64,610,1140,36,24,true,C.teal);
 text(s,'*2025 arXiv preprint. Published scores use different datasets and protocols; no direct ranking is claimed.',64,651,1140,25,16,false,C.muted);
 note(s,'Literature review: DeepSleepNet: a Model for Automatic Sleep Stage Scoring based on Raw Single-Channel EEG, Supratak et al., IEEE TNSRE 2017, DOI 10.1109/TNSRE.2017.2721116. SeqSleepNet: End-to-End Hierarchical Recurrent Neural Network for Sequence-to-Sequence Automatic Sleep Staging, Phan et al., IEEE TNSRE 2019, DOI 10.1109/TNSRE.2019.2896659. U-Sleep: resilient high-frequency sleep staging, Perslev et al., npj Digital Medicine 2021, DOI 10.1038/s41746-021-00440-5. RobustSleepNet: Transfer learning for automated sleep staging at scale, Guillot and Thorey, 2021. SLEEPYLAND: trust begins with fair evaluation of automatic sleep staging models, Dei Rossi et al., 2025 arXiv preprint. These papers motivate context, robust evaluation and soft fusion. Our proposed coarse/NREM hierarchy is an engineering hypothesis, not an implementation attributed to any of these papers. Different data, channels and evaluation protocols prevent score comparison.',Object.values(refs).filter(v=>v!==refs.hmc&&v!==refs.long));
}
// 4: Dataset and explicit epoch explanation.
{
 const s=base(4,'Dataset and 30-second EEG epochs','PhysioNet HMC v1.1; verified split_summary.json');
 text(s,'HMC v1.1: 151 clinical PSG recordings; project subset: 24 recordings',64,166,1148,40,25,true);
 table(s,[['Partition','Recordings','EEG epochs'],['Training','16','15,216'],['Validation','4','3,619'],['Test','4','3,109'],['Total','24','21,944']],64,240,570,300,[235,150,185],23);
 text(s,'One EEG epoch = one 30 s segment',686,241,520,40,26,true,C.teal);
 ['0–30 s','30–60 s','60–90 s'].forEach((v,i)=>block(s,v,686+i*175,312,158,66,false,23));
 text(s,'At 100 Hz: 30 × 100 = 3,000 samples\nFour channels → input shape 4 × 3,000',686,412,520,100,25);
 text(s,'F4-M1 · C4-M1 · O2-M1 · C3-M2',686,532,520,40,21,false,C.muted);
 text(s,'Split by recording ID. SN001 covers only 190 epochs (95 min); whole-night claims are unsupported.',64,614,1148,54,20,false,C.muted);
 note(s,'PSG means polysomnography. HMC is a heterogeneous clinical population, not a healthy normative database. Four EEG derivations and original 256 Hz sampling are documented. We use a 24-recording subset, separated by recording ID into 16/4/4. IDs identify recordings; a repeated-person mapping is not provided, so person-level separation is not proven. Test IDs: SN001, SN004, SN009, SN022. EEG epoch is a temporal segment, whereas training epoch means one pass through the training data. Stored SN001 is a 95-minute segment. Dataset total is 15,216+3,619+3,109=21,944.',[refs.hmc]);
}
// 5: Actual order and reused signal visuals.
{
 const s=base(5,'EEG preprocessing','Notebook preprocessing lineage; archived matched SN009 signal example');
 ['Select 4\nchannels','50 Hz notch\nat 256 Hz','Bandpass\n0.3–35 Hz','Resample\nto 100 Hz','30 s epochs\n+ normalize'].forEach((v,i)=>{block(s,v,64+i*235,177,204,88,false,23);if(i<4)arrow(s,273+i*235,213,23,18);});
 text(s,'Raw EEG · SN009, F4-M1',64,313,545,32,22,true);
 text(s,'Filtered and normalized EEG · same interval',665,313,545,32,22,true);
 await image(s,path.join(ROOT,'ppt_artifacts/raw_eeg_example.png'),64,357,545,237);
 await image(s,path.join(ROOT,'ppt_artifacts/preprocessed_eeg_example.png'),665,357,545,237);
 text(s,'Per-epoch, per-channel normalization. Apply the 50 Hz notch before resampling.',64,612,1140,33,23,true,C.teal);
 text(s,'Archived 300–330 s signal illustration only; all performance results use the current 3,109-epoch run.',64,650,1140,27,16,false,C.muted);
 note(s,'Source pipeline order from preprocessing_config.json: selected four channels, notch 50 Hz at original sampling rate, bandpass 0.3–35 Hz, resample 100 Hz, epoch and channel normalization. The current refinement notebook loads stored preprocessed NPZ EEG and normalizes each epoch again for neural inference; spectral extraction uses stored EEG before that second normalization. Automatic artifact rejection was not established in the source preprocessing; explicit quality gates are future work. Existing example metadata: SN009, F4-M1, index 10, 300–330 seconds, raw 256 Hz, processed 100 Hz; saved/reprocessed difference 0.0. These figures are retained as explanatory signal evidence from ppt_artifacts, not as evidence for the current numerical comparison.');
}
// 6: Editable implemented system block diagram.
{
 const s=base(6,'Implemented system block diagram');
 text(s,'Main implementation: Biomarker_N1_N2_Refinement.ipynb',64,163,1140,40,25,true,C.teal);
 block(s,'Stored EEG\n4 × 3,000',64,239,210,90);arrow(s,283,274,34,20);
 block(s,'Fast SCFormer-U\n5-stage output',327,239,260,90,true);arrow(s,596,274,34,20);
 block(s,'Predicted N1/N2?\nSpectral refiner',640,239,280,90);arrow(s,929,274,34,20);
 block(s,'Final stage\nper epoch',973,239,235,90,true);
 arrow(s,150,340,25,72,true);block(s,'Welch spectral\nfeatures',64,425,210,90);
 arrow(s,283,461,34,22);block(s,'Mean EEG features\nper recording',327,425,260,90);
 arrow(s,1077,340,25,72,true);block(s,'Hypnogram +\nsleep architecture',973,425,235,90,false,22);
 arrow(s,596,461,34,22);block(s,'Recording profile\n+ reference comparison',640,425,280,90,false,22);
 shape(s,'leftArrow',929,461,34,22,C.teal,C.teal);
 // Spectral features also feed the targeted refiner through the upper branch.
 line(s,274,444,21);line(s,295,368,0,76);line(s,295,368,484);shape(s,'upArrow',767,341,24,27,C.teal,C.teal);
 text(s,'Architecture + spectral features → z-scores / P10–P90 → four-domain profile → dashboard',64,570,1145,65,24,true,C.teal);
 text(s,'The 16-recording training reference provides dataset-relative descriptions.',64,646,1145,27,19,false,C.muted);
 note(s,'Read the top path left to right: stored input, retained five-stage model, targeted N1/N2 refinement, final labels. Welch features support the refiner (shown explicitly on slide 8) and recording EEG means. Final labels produce architecture metrics. Both architecture and spectral means join the recording profile; the lower connector carries architecture into that profile. Ten architecture metrics determine four domain flags; EEG deviations are displayed separately. The training reference uses only 16 training recordings. The resulting profile is descriptive, not a diagnosis.');
}
// 7: Existing neural architecture plus native training chart.
{
 const s=base(7,'Existing model and training epochs');
 ['Conv1D encoder\n64 → 128 filters','Self-attention\n4 heads, key dim 16','BiLSTM\n64 units / direction','Pooling + dense\n5 evidence outputs'].forEach((v,i)=>{block(s,v,64+i*295,174,260,92,i===3,22);if(i<3)arrow(s,332+i*295,210,24,20);});
 text(s,'226,309 parameters · Attention and BiLSTM operate within each 30-second EEG epoch',64,292,1140,40,23,true,C.teal);
 text(s,'Training / validation accuracy',64,341,690,31,22,true);
 const ch=s.charts.add('line',{position:{left:64,top:379,width:690,height:244},categories:history.map(r=>String(r[5])),series:[{name:'Training',values:history.map(r=>r[1]),line:{fill:C.ink,width:3}},{name:'Validation',values:history.map(r=>r[3]),line:{fill:C.teal,width:3}}],lineOptions:{smooth:false},hasLegend:true,legend:{position:'bottom',overlay:false},xAxis:{title:'Training epoch',textStyle:{fontSize:17}},yAxis:{numberFormatCode:'0%',min:0,max:1,majorUnit:0.25,textStyle:{fontSize:17}},chartFill:C.bg,plotAreaFill:C.bg});chartFont(ch);
 text(s,'A training epoch = one full\npass through training data',797,351,410,70,25,true);
 text(s,`Adam · learning rate 0.0001\nBatch size: ${hparams.batch_size}\n10 training epochs\nSelected checkpoint: epoch 9`,797,449,410,126,24);
 text(s,'Current notebook loads this checkpoint; it trains the spectral refiner separately.',64,643,1140,31,21,false,C.muted);
 note(s,'Architecture verified against model_layers.csv and saved checkpoint: first convolution kernel 7/stride 4, second kernel 5/stride 4, 64 and 128 filters; 4-head attention with key dimension 16, residual normalization/feed-forward layers; within-epoch bidirectional LSTM, 64 units in each direction; pooling, dense and five softplus evidence outputs. 226,309 total parameters. Dirichlet alpha=evidence+1; probability alpha/sum(alpha); original uncertainty=5/sum(alpha). Training chart is the saved historical training log for this retained model, not a new run. Ten maximum and actual training epochs, checkpoint selected at 9 by validation evidential accuracy (67.97%). No automatic scheduler in final training cell. The biomarker notebook loads the checkpoint and fits the refiner without retraining this neural model.');
}
// 8: Actual inference branching and spectral features.
{
 const s=base(8,'N1/N2 refinement flowchart');
 block(s,'Initial stage\nprediction',64,192,210,82,true);arrow(s,286,223,33,20);
 block(s,'N1 or N2?',337,181,212,105,false,24,'diamond');
 text(s,'YES',573,204,60,30,18,true,C.teal);arrow(s,564,243,64,19);
 block(s,'9 spectral features\n+ StandardScaler',644,192,258,82);arrow(s,914,223,32,20);
 block(s,'Balanced logistic\nregression → N1 / N2',961,192,247,82,true,22);
 arrow(s,431,301,25,65,true);text(s,'NO',473,320,55,28,18,true,C.teal);
 block(s,'Retain original Wake / N3 / REM prediction',278,382,475,59,false,23);
 table(s,[['Feature group','Input to the refiner'],['Relative powers','Delta, Theta, Alpha, Sigma, Beta'],['Band / Delta ratios','Theta, Alpha, Sigma, Beta']],64,486,708,143,[245,463],22);
 text(s,'Fit on training data only',818,469,390,37,25,true,C.teal);
 text(s,'True AND predicted N1/N2:\n1,278 N1 + 4,588 N2 epochs\nTest gate uses predictions only.',818,520,390,105,22);
 text(s,'Welch: 4 s windows, 2 s overlap; average channel powers before computing ratios.',64,649,1145,27,18,false,C.muted);
 note(s,'Exact training gate from notebook cells 20–21: true labels AND baseline predictions in {N1,N2}. This produces 5,866 training candidates. Pipeline: StandardScaler then LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42). At inference, ONLY the initial predicted label routes the epoch. Ground truth is never an inference input. Nine features: relative Delta/Theta/Alpha/Sigma/Beta plus Sigma/Delta, Theta/Delta, Alpha/Delta, Beta/Delta. Bands: [0.5,4), [4,8), [8,12), [12,16), [16,30) Hz. Welch at 100 Hz uses 400 samples/window and 200 overlap; total power [0.5,30). Four channel powers are averaged first. Sigma power does not measure spindle density. Original predicted Wake/N3/REM labels are kept; original neural probabilities and uncertainty are not recalibrated to the refined labels.');
}
// 9: Native editable data chart.
{
 const s=base(9,'Results and measured gains');
 const raw=results.raw_metrics,ref=results.refined_metrics;
 const chart=s.charts.add('bar',{position:{left:64,top:179,width:785,height:389},categories:['Accuracy','Macro F1','N1 F1','N2 F1'],series:[{name:'Existing model',values:[raw.accuracy,raw.macro_f1,0.3660403618649965,0.571173583221776],fill:C.ink,valuesFormatCode:'0.00%'},{name:'N1/N2 refined',values:[ref.accuracy,ref.macro_f1,0.4063241106719368,0.6357231661831745],fill:C.teal,valuesFormatCode:'0.00%'}],barOptions:{direction:'column',grouping:'clustered',gapWidth:80},hasLegend:true,legend:{position:'bottom',overlay:false},dataLabels:{showValue:true,position:'outEnd',textStyle:{fontSize:18}},xAxis:{textStyle:{fontSize:21}},yAxis:{min:0,max:0.8,majorUnit:0.2,numberFormatCode:'0%',textStyle:{fontSize:18}},chartFill:C.bg,plotAreaFill:C.bg});chartFont(chart);
 text(s,'+3.89 pp',903,207,307,67,43,true,C.teal);text(s,'Accuracy: 55.45% → 59.34%',903,280,305,74,23);
 text(s,'+2.10 pp',903,389,307,67,43,true,C.teal);text(s,'Macro F1:\n57.42% → 59.51%',903,462,305,76,23);
 text(s,'154 corrected − 33 degraded = 121 net additional correct epochs',64,603,1140,37,26,true);
 text(s,'Same 3,109 test epochs across 4 recordings · 238 labels changed · pp = percentage points',64,648,1140,31,19,false,C.muted);
 note(s,'Current experiment HMC-N1N2-20261007 only. Raw/refined accuracy: 0.5545191379864909 / 0.5934384046317144; macro F1 0.5741553020766511 / 0.5951219684303188. N1 F1 0.3660403618649965 / 0.4063241106719368; N2 F1 0.571173583221776 / 0.6357231661831745. Accuracy gain 3.8919267 percentage points; macro F1 gain 2.0966666 percentage points, rounded once to 3.89/2.10. Corrections 154, degradations 33, wrong-to-wrong 51, unchanged 2,871, total 3,109. Of 238 changes, 121 are net additional correct. N2-to-N1 errors 506 to 379. N1 F1 gain 4.03 pp; N2 F1 gain 6.45 pp. Kappa 0.4253 to 0.4647. Per-stage Wake/N3/REM F1 remain unchanged because predictions of these stages are retained. Results are modest and limited to this small subset; not a comparison against the literature datasets.');
}
// 10: Reuse verified output images and explain profiling.
{
 const s=base(10,'Project outputs: hypnogram and sleep profile');
 text(s,'SN009 · verified stage sequence',64,162,720,36,25,true,C.teal);
 await image(s,path.join(D,'hypnogram_SN009.png'),64,207,720,350);
 text(s,'Sleep Studio · current GUI',822,162,388,36,25,true,C.teal);
 await image(s,path.join(D,'dashboard.png'),822,210,388,254);
 text(s,'Architecture, spectral features,\nreference deviations and exports',822,494,388,64,23);
 text(s,'Stage labels → architecture metrics → training-reference comparison → four-domain profile',64,590,1140,65,25,true,C.teal);
 text(s,'Duration · Continuity · Initiation · Architecture | Descriptive research profiles, not diagnoses',64,651,1140,28,18,false,C.muted);
 note(s,'Hypnogram is the verified SN009 plot showing original and refined labels versus ground truth. SN009 has 901 epochs. Dashboard screenshot is from the current verified GUI; it demonstrates implemented outputs rather than a mockup. Master features have recording ID + 22 numeric fields; compare 21 fields after excluding recording_minutes. Architecture metrics include TST, efficiency, SOL, WASO, stage percentages, awakenings and project-defined fragmentation. Efficiency uses evaluated duration; stage percentages use TST. Reference mean/sample SD and P10/P90 derive from 16 training recordings; any out-of-interval architecture metric flags the corresponding domain. Four domains are Duration, Continuity, Initiation, Architecture. SN009: one deviated domain, descriptive Mild Deviation. EEG deviations do not contribute additional domains. HMC is clinical, not healthy normative data; in-sample architecture reference and unknown whole-night timing limit interpretation. Current GUI has PDF/JSON/CSV/ZIP exports and a Colab worker; live SN009 predictions were already independently reproduced.');
}
// 11: Soft hierarchy avoids irreversible hard gating.
{
 const s=base(11,'Future plan: multistage, multimodel architecture','Proposed research design; inspired by SeqSleepNet, RobustSleepNet and SLEEPYLAND');
 text(s,'Proposed • not yet implemented or evaluated',64,161,1140,33,23,true,C.teal);
 block(s,'Aligned EEG\n+ quality checks',64,247,187,85);
 block(s,'Model A: coarse CNN\nWake / REM / NREM',304,216,307,85,true,22);
 block(s,'Model B: NREM expert\nN1 / N2 / N3',304,349,307,85,true,22);
 line(s,264,289,21);line(s,285,258,0,133);arrow(s,285,252,19,13);arrow(s,285,385,19,13);
 block(s,'Soft probability\ncomposition +\noptional baseline fusion',680,276,245,116,false,22);
 line(s,621,258,24);line(s,645,258,0,64);arrow(s,645,314,26,16);
 line(s,621,391,24);line(s,645,350,0,41);arrow(s,645,342,26,16);
 arrow(s,939,323,32,20);block(s,'Model C: TCN\nTemporal CNN\nacross epochs',983,276,225,116,true,22);
 text(s,'Conditional NREM probabilities preserve five-class normalization',64,461,1140,33,22,true,C.teal);
 text(s,'1  Experts',64,526,350,40,26,true);
 text(s,'Test coarse + NREM models\nagainst the current baseline.',64,578,350,68,23);
 text(s,'2  Context + confidence',455,526,350,40,26,true);
 text(s,'Train TCN on out-of-fold outputs.\nCalibrate final probabilities.',455,578,350,68,23);
 text(s,'3  Broader validation',850,526,350,40,26,true);
 text(s,'New locked cohort, then external\ndata and optional EOG / EMG.',850,578,350,68,23);
 note(s,'Proposed engineering design, not current implementation. Train compact Model A with Wake/REM/NREM targets, Model B on true training NREM epochs. Evaluate B on each inference epoch. Let g be coarse probabilities and h be conditional NREM probabilities: q=[gW,gNREM*hN1,gNREM*hN2,gNREM*hN3,gREM]. This sums to 1. Optional soft fusion r=lambda*q+(1-lambda)*p with the retained five-stage model p; choose lambda on development data only. Avoid hard gating because coarse mistakes could otherwise become irreversible. Model C is a small temporal convolutional network operating across consecutive epochs, unlike current within-epoch BiLSTM. Train it on out-of-fold expert predictions, preserve recording boundaries/gaps, then calibrate final output on a held-out validation partition. TCN and Viterbi are alternatives to compare by ablation, not refiners to stack automatically. Add EOG/EMG specialists only if aligned data and missing-modality tests are available. Start small with 24 recordings to limit overfitting. Current four test recordings have already been examined; reserve genuinely new recordings/person cohort before new tuning. Person-level grouping requires a verified mapping. Sequence context motivated by SeqSleepNet and L-SeqSleepNet; heterogeneous cohort testing by RobustSleepNet; soft voting and fair evaluation by SLEEPYLAND. Benefits are hypotheses, not guaranteed gains.',[refs.seq,refs.long,refs.robust,refs.sleepy]);
}
// 12: Conclusion and concrete future experiment gates.
{
 const s=base(12,'Conclusion and next milestones');
 text(s,'What is demonstrated',64,178,520,44,29,true,C.teal);
 text(s,'Spectral features improve\nN1/N2 discrimination\nin the current experiment.',64,251,533,116,29,true);
 text(s,'59.34% test accuracy; 59.51% macro F1.\nA complete notebook-to-GUI pipeline\nproduces stage labels and profiles.',64,381,533,119,25);
 text(s,'Limits: 4 test recordings, partial SN001,\nN1 F1 40.63%, no clinical validation.',64,557,533,76,23,false,C.muted);
 text(s,'Next milestones',692,178,516,44,29,true,C.teal);
 text(s,'01  Audit full EDF alignment and quality;\n       reserve a new locked test cohort.',692,251,516,77,25);
 text(s,'02  Compare experts, soft fusion and TCN\n       through controlled ablations.',692,358,516,77,25);
 text(s,'03  Evaluate calibration, external data\n       and biomarker errors; add modalities.',692,465,516,77,25);
 text(s,'Evaluate macro F1, N1/N2 F1, calibration,\nlatency and errors in sleep biomarkers.',692,581,516,68,22,true,C.teal);
 note(s,'Conclusion: the current reproducible experiment supports complementary spectral features for N1/N2. Net correction is 121 epochs and the gains are modest. The project also implements recording architecture and spectral features, descriptive reference profiles, a Windows Electron GUI and reports. It does not establish clinical diagnosis or superior performance versus the literature. Roadmap: verify original EDF alignment, retain timestamp continuity and quality checks, expand HMC data and reserve untouched recordings/person cohort; compare flat baseline, coarse/NREM composition, optional soft fusion, temporal model, and decoder alternatives on identical locked epochs. Fit scalers, class weights and transitions on training data only; use grouped development folds and out-of-fold base predictions for stacking. Report accuracy, macro F1, per-stage F1, kappa, ECE, error-detection AUROC, risk-coverage, latency and model size. Include recording/person bootstrap confidence intervals, stage distribution and individual recording variability. Validate TST/WASO/SOL/stage fractions against label-derived ground truth using verified denominators. Test external dataset/channel compatibility and optional aligned EOG/EMG specialists. No accuracy target or delivery date is promised without experiments.',[refs.hmc,refs.robust,refs.sleepy]);
}

const cand=path.join(BUILD,'candidate.pptx');
await (await PresentationFile.exportPptx(pres)).save(cand);
 const final=path.join(OUT,'EEG_Sleep_Mid_Viva_12_Slides_Reviewed.pptx');
await finalizePresentation({workspaceDir:ROOT,candidatePath:cand,finalPath:final,pythonExecutable:R+'/python/python.exe',integrityValidatorPath:SK+'/container_tools/inspect_presentation_package_integrity.py',layoutValidatorPath:SK+'/container_tools/inspect_presentation_layout_geometry.py',layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--require-native-table-slide','3','--require-native-table-slide','4','--require-native-table-slide','8'],explicitTotalSlideCount:12,requiredNativeTableOwnerSlides:[3,4,8],requiredNativeChartOwnerSlides:[7,9],materializeLiteralChartWorkbooks:true,fontPolicy:{basis:'design',families:['Arial']},verifyArtifactToolImport:true,receiptPath:path.join(BUILD,'validation-reviewed.json')});
await fs.writeFile(path.join(BUILD,'output-inspection.ndjson'),(await pres.inspect({kind:'slide,textbox,table,chart,notes',maxChars:100000})).ndjson);
console.log('Final deck: '+final);
