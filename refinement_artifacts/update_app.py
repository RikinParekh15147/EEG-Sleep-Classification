"""Integrate the reproduced notebook pipeline with the desktop worker and UI."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def edit(file,fn):
    p=ROOT/file;p.write_text(fn(p.read_text(encoding='utf8')),encoding='utf8')
def worker(s):
    s=s.replace('from core import CHANNELS', 'from refinement import FEATURES, spectral_features, refine_predictions, sleep_architecture, deviation_profile\nfrom core import CHANNELS')
    s=s.replace("if item.get('source')=='project':", "if item.get('source')=='project' and settings.get('reconstructFullEDF',False):",1)
    s=s.replace("elif not settings.get('preprocessedAcknowledged',False):", "elif item.get('source')=='project':\n        expected=settings.get('projectHashes',{}).get(sid)\n        if expected and metadata['sha256']!=expected:raise ValueError('Project input changed since refinement audit: '+sid)\n        timing_known=settings.get('assumeContiguous',False)\n    elif not settings.get('preprocessedAcknowledged',False):",1)
    s=s.replace("'verified project EDF alignment' if item.get('source')=='project'", "'stored notebook sequence; assumed contiguous epochs' if item.get('source')=='project'")
    s=s.replace("rows=[];profiles=[];inputs=[];", "refinement=config.get('refinement');reference=config.get('reference',[])\n    if settings.get('refinement',True) and (not refinement or refinement.get('checkpoint_sha256')!=checkpoint_hash):\n        raise ValueError('This checkpoint needs its own fitted N1/N2 refinement. Disable refinement for raw inference.')\n    rows=[];profiles=[];inputs=[];")
    start=s.index("        smoothing=settings.get('smoothing',True)")
    end=s.index("        true=y.astype(int).tolist()",start)
    s=s[:start]+"        feature_batches=[]\n        for start in range(0,len(x),batch):\n            check_cancel();feature_batches.extend(spectral_features(x[start:start+batch]).tolist())\n        refined=refine_predictions(rawpred,feature_batches,refinement) if settings.get('refinement',True) else None\n"+s[end:]
    s=s.replace("'soft_viterbi_prediction':smooth[i] if smooth is not None else None", "'refined_prediction':refined[i] if refined is not None else None,**dict(zip(FEATURES,feature_batches[i]))")
    start=s.index("        for source,stages in [('ground_truth',true)")
    end=s.index('        evidence_rows.extend(evidence)',start)
    s=s[:start]+"        for source,stages in [('ground_truth',true),('raw',rawpred),('refined',refined)]:\n            if stages is None:continue\n            values=sleep_architecture(stages,times,timing_known)\n            values.update(dict(zip(FEATURES,np.mean(feature_batches,axis=0).tolist())))\n            profile=deviation_profile(values,reference) if reference and refinement and refinement.get('checkpoint_sha256')==checkpoint_hash else {'sleep_health_deviation_profile':'Unavailable','deviations':{}}\n            profiles.append({'subject_id':sid,'source':source,**values,**profile,\n              'scope':'evaluated epochs; '+metadata['timing'],\n              'complete_contiguous_record':timing_known and len(boundaries(times,len(x)))==2})\n"+s[end:]
    s=s.replace("'smoothed':smoothing", "'refinement_applied':refined is not None")
    s=s.replace("if smooth is not None:result['smoothed_accuracy']=classification(true,smooth)[0]['accuracy']", "if refined is not None:result['refined_accuracy']=classification(true,refined)[0]['accuracy']")
    s=s.replace("write_csv(out/'test_epoch_predictions.csv',rows);write_csv(out/'subject_biomarkers.csv',profiles)", "write_csv(out/'test_epoch_predictions.csv',rows);write_csv(out/'subject_biomarkers.csv',[{k:v for k,v in p.items() if k!='deviations'} for p in profiles]);dump(out/'subject_profiles.json',profiles)")
    s=s.replace("write_csv(out/'subject_risk_profiles.csv',[p for p in profiles if p['source']=='soft_viterbi'])", "dump(out/'reference_stats.json',reference);dump(out/'refinement_model.json',refinement)")
    s=s.replace("('soft_viterbi','soft_viterbi_prediction','smoothed_')", "('refined','refined_prediction','refined_')")
    s=s.replace("'smoothed_metrics':metrics.get('soft_viterbi')", "'refined_metrics':metrics.get('refined')")
    s=s.replace("'Rule-based research profiles; thresholds not clinically validated.'", "'HMC training reference is a heterogeneous clinical population; domain counts are descriptive, not disease risk or clinical severity.'")
    s=s.replace("'Soft-Viterbi','soft_viterbi_prediction'", "'N1/N2 refined','refined_prediction'")
    s=s.replace("('soft_viterbi','soft_viterbi_prediction')", "('refined','refined_prediction')")
    return s
edit('gui/pipeline/worker.py',worker)
def store(s):
    s=s.replace("this.baseline = path.join(projectRoot, 'ppt_artifacts')", "this.baseline = path.join(projectRoot, 'refinement_artifacts', 'verified'); this.legacy = path.join(projectRoot, 'ppt_artifacts')")
    s=s.replace("name:'Verified HMC evaluation'", "name:'Verified N1/N2 biomarker refinement'").replace("sourceRun:'HMC-PPT-20261007-01'", "sourceRun:'HMC-N1N2-20261007'")
    s=s.replace("biomarkers:this.read(dir,'subject_biomarkers.csv',[])", "profiles:this.read(dir,'subject_profiles.json',[]),reference:this.read(dir,'reference_stats.json',[]),biomarkers:this.read(dir,'subject_biomarkers.csv',[])")
    s=s.replace('smoothedReport','refinedReport').replace('smoothedConfusion','refinedConfusion').replace('smoothed_classification','refined_classification').replace('smoothed_confusion','refined_confusion')
    for name in ['hyperparameters','model_layers','preprocessing_config','transition_config','transition_matrix','risk_rules']:
        s=s.replace("this.read(this.baseline,'"+name, "this.read(this.legacy,'"+name)
    return s
edit('gui/electron/store.cjs',store)
def service(s):
    s=s.replace("['smoothing','assumeContiguous'", "['refinement','assumeContiguous'")
    s=s.replace("smoothing:value.smoothing??true", "refinement:value.refinement??true")
    s=s.replace("['numpy','tensorflow','keras','mne','matplotlib']", "['numpy','tensorflow','keras','mne','matplotlib','scipy','scikit-learn']")
    s=s.replace("'matplotlib':'3.10.8'", "'matplotlib':'3.10.8','scipy':'1.16.3','scikit-learn':'1.8.0'")
    s=s.replace("const config={id,kind:valid.kind,settings,inputs,transition:selectedTransition,split};", "const refinement=this.store.read(this.store.baseline,'refinement_model.json',null);\n    const reference=this.store.read(this.store.baseline,'reference_stats.json',[]);\n    settings.projectHashes=Object.fromEntries(this.store.read(this.store.baseline,'data_manifest.json',[]).map(r=>[r.subject_id,r.sha256]));\n    const config={id,kind:valid.kind,settings,inputs,transition:selectedTransition,split,refinement,reference};")
    s=s.replace("this.store.read(this.store.baseline,'transition_matrix.csv'", "this.store.read(this.store.legacy,'transition_matrix.csv'")
    s=s.replace("['core.py','worker.py']", "['core.py','refinement.py','worker.py']")
    return s
edit('gui/electron/service.cjs',service)
edit('gui/src/types.ts',lambda s:s.replace('soft_viterbi?:Metrics','refined?:Metrics').replace('smoothedReport','refinedReport').replace('smoothedConfusion','refinedConfusion').replace('biomarkers:Row[]','profiles:Record<string,any>[];reference:Record<string,any>[];biomarkers:Row[]'))
def app(s):
    s=s.replace('soft_viterbi_prediction','refined_prediction').replace('soft_viterbi','refined').replace('smoothedReport','refinedReport').replace('smoothedConfusion','refinedConfusion')
    s=s.replace('Soft-Viterbi','N1/N2 refinement').replace('Smoothed accuracy','Refined accuracy').replace('Smoothed predictions','Refined predictions').replace('Smoothed','Refined').replace('smoothed predictions','refined predictions').replace('Raw versus smoothed','Raw versus refined').replace('HMC-PPT-20261007-01','HMC-N1N2-20261007')
    s=s.replace('Verified correction','95-minute segment').replace('7h 30m evaluated','7h 30.5m evaluated')
    s=s.replace("total={sn009.length}","total={counts.slice(1).reduce((a,b)=>a+b,0)}")
    s=s.replace("const [smoothing,setSmoothing]=useState(true)","const [refinement,setRefinement]=useState(true)")
    # State declaration shares a comma with other analysis settings.
    s=s.replace('[smoothing,setSmoothing]','[refinement,setRefinement]').replace('setSmoothing','setRefinement').replace('smoothing','refinement')
    s=s.replace('refinement,batchSize,emissionWeight:weight,assumeContiguous:assume',"refinement,batchSize,assumeContiguous:source==='project'||assume")
    s=s.replace('Use training transition priors','Nine EEG features · balanced logistic regression').replace('N1/N2 refinement refinement','N1/N2 spectral refinement')
    start=s.index('<Field label="Emission weight"')
    end=s.index('<div className="pipeline-mini">',start)
    s=s[:start]+s[end:]
    s=s.replace("refinement?'Smooth stage sequence':'Keep raw predictions'", "refinement?'Refine N1/N2 candidates':'Keep raw predictions'")
    s=s.replace('Project inputs are checked against the original EDF annotations before inference.', 'Project examples use the notebook NPZ sequences and assume contiguous epochs. SN001 covers 95 minutes.')
    s=s.replace('const biom=run.biomarkers.find', 'const biom=run.biomarkers.find')
    s=s.replace('biom?.sleep_minutes','biom?.TST_minutes').replace('biom?.risk_category','biom?.sleep_health_deviation_profile')
    s=s.replace('Rule-based · evaluated-epoch proxy','HMC reference · descriptive domain count')
    s=s.replace("source==='refined'?'N1/N2 refinement':'Raw model'", "source==='refined'?'N1/N2 spectral refinement':'Raw model'")
    s=s.replace('refinement changes the selected sequence, not these probabilities.', 'N1/N2 refinement changes the selected stage. These probabilities and uncertainty remain the original Transformer output.')
    s=s.replace('total={rows.length}', 'total={counts.slice(1).reduce((a,b)=>a+b,0)}')
    s=s.replace('Predicted time in each sleep stage','Sleep stages as a percentage of TST; Wake shown separately')
    start=s.index(" {selectedTab==='profile'&&")
    end=s.index(" {selectedTab==='training'&&",start)
    s=s[:start]+" {selectedTab==='profile'&&<SleepProfile run={run} recording={recording} source={source}/>}\n"+s[end:]
    start=s.index('<Card><CardHead title="Known data correction"')
    end=s.index('</Card>',start)+len('</Card>')
    s=s[:start]+'''<Card><CardHead title="Evaluation scope" subtitle="Notebook reproduction · 3,109 test epochs"/><p>The refinement notebook uses SN001’s stored 190 epochs (95 minutes). Its reported accuracy is 55.45% before refinement and 59.34% afterward. This segment does not establish whole-night sleep duration or sleep onset.</p><p className="muted">The earlier EDF alignment audit reconstructed 854 SN001 epochs and evaluated 3,773 test epochs. Those results belong to a separate experiment. The notebook’s training reference has 16 recordings and is a heterogeneous clinical reference.</p><button className="text-button" onClick={()=>api.openExternal('https://physionet.org/content/hmc-sleep-staging/1.1/')}>HMC dataset source<ArrowUpRight size={14}/></button></Card>'''+s[end:]
    s=s.replace('refinement and transition-based profile values', 'time-based profile values')
    s=s.replace("refined_prediction!==null", "refined_prediction!=null")
    return s
edit('gui/src/App.tsx',app)
edit('gui/src/charts.tsx',lambda s:s.replace('soft_viterbi_prediction','refined_prediction').replace("refined_prediction!==null", "refined_prediction!=null").replace('Smoothed / available prediction','N1/N2 refined / available prediction'))
print('Updated worker, bridge configuration, data store and UI pipeline.')
