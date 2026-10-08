"""Prepare current GUI artifacts and independently verify reproduced calculations."""
from pathlib import Path
import json,csv,sys,zipfile,shutil,math
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'refinement_artifacts';D=OUT/'verified';D.mkdir(exist_ok=True)
with zipfile.ZipFile(OUT/'reproduction_verified.zip') as z:
    for info in z.infolist():
        if Path(info.filename).name!=info.filename:raise ValueError('Unexpected bundle path')
        (D/info.filename).write_bytes(z.read(info))
sys.path.insert(0,str(ROOT/'gui/pipeline'))
from core import classification,calibration,evidence_distribution,STAGES
from refinement import FEATURES,sleep_architecture,refine_predictions,deviation_profile
def read_csv(name):
    with (D/name).open(encoding='utf8') as f:return list(csv.DictReader(f))
def write(name,rows):
    with (D/name).open('w',newline='',encoding='utf8') as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
def dump(name,value):(D/name).write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf8')
r=json.loads((D/'final_results.json').read_text());model=json.loads((D/'refinement_model.json').read_text());refs=json.loads((D/'reference_stats.json').read_text());profiles=json.loads((D/'subject_profiles.json').read_text())
rows=read_csv('test_epoch_predictions.csv');truth=[int(x['true_label']) for x in rows];metrics={'run_id':r['run_id']};checks=[]
for row in rows:
    p,u,_=evidence_distribution([float(row['evidence_'+stage]) for stage in STAGES])
    assert abs(u-float(row['uncertainty']))<1e-7
    # Source adds/sums alpha in float32; desktop arithmetic uses Python doubles.
    assert all(abs(v-float(row['prob_'+stage]))<2e-7 for v,stage in zip(p,STAGES))
    assert max(range(5),key=lambda j:p[j])==int(row['raw_prediction'])
checks.append('All 3,109 evidential probability and uncertainty formulas checked against source float32 output')
for source,col,prefix in [('raw','raw_prediction',''),('refined','refined_prediction','refined_')]:
    values,report,cm=classification(truth,[int(x[col]) for x in rows]);values['test_subjects']=4;metrics[source]=values
    write(prefix+'classification_report.csv',report)
    write(prefix+'confusion_matrix_counts.csv',[{'true_stage':n,**dict(zip(STAGES,cm[i]))} for i,n in enumerate(STAGES)])
    write(prefix+'confusion_matrix_normalized.csv',[{'true_stage':n,**{s:cm[i][j]/sum(cm[i]) if sum(cm[i]) else 0 for j,s in enumerate(STAGES)}} for i,n in enumerate(STAGES)])
    checks.append(source+' confusion matrix and aggregate metrics independently recomputed')
    assert math.isclose(values['accuracy'],r[source+'_metrics']['accuracy'],abs_tol=1e-12)
dump('overall_metrics.json',metrics)
for sid in dict.fromkeys(x['subject_id'] for x in rows):
    sub=[x for x in rows if x['subject_id']==sid]
    predictions=refine_predictions([int(x['raw_prediction']) for x in sub],[[float(x[f]) for f in FEATURES] for x in sub],model)
    assert predictions==[int(x['refined_prediction']) for x in sub],sid
    for p in [p for p in profiles if p['subject_id']==sid]:
        col={'raw':'raw_prediction','refined':'refined_prediction','ground_truth':'true_label'}[p['source']]
        values=sleep_architecture([int(x[col]) for x in sub])
        for k,v in values.items():assert v is None and p[k] is None or v is not None and math.isclose(v,p[k],abs_tol=1e-9),(sid,k,v,p[k])
        profile=deviation_profile(p,refs)
        assert profile['sleep_health_deviation_profile']==p['sleep_health_deviation_profile']
    checks.append(sid+' exact N1/N2 sequence, all architecture values, domains and profile reproduced by desktop code')
assert len(rows)==3109
assert model['training_counts']=={'N1':1278,'N2':4588},model['training_counts']
assert r['changes']=={'unchanged':2871,'corrected':154,'degraded':33,'wrong_to_wrong':51,'changed':238},r['changes']
assert round(metrics['raw']['accuracy']*100,2)==55.45
assert round(metrics['refined']['accuracy']*100,2)==59.34
assert round(metrics['refined']['macro_f1']*100,2)==59.51
lookup={row['feature']:row for row in refs}
for row in json.loads((OUT/'reference_stats.json').read_text(encoding='utf8')):
    for field in ['mean','std','median','p10','p90']:
        assert abs(lookup[row['feature']][field]-float(row[field]))<0.000051,(row['feature'],field)
for row in json.loads((OUT/'refinement_coefficients.json').read_text(encoding='utf8')):
    assert abs(model['coefficients'][FEATURES.index(row['feature'])]-float(row['coefficient']))<0.00000051,row
checks.append('All 22 complete reference rows and nine coefficients match saved notebook display precision')
from statistics import mean,stdev
training=read_csv('train_reference_features.csv')
for ref in refs:
    values=sorted(float(row[ref['feature']]) for row in training)
    assert math.isclose(mean(values),ref['mean'],abs_tol=1e-10)
    assert math.isclose(stdev(values),ref['std'],abs_tol=1e-10)
    for field,q in [('median',.5),('p10',.1),('p90',.9)]:
        pos=(len(values)-1)*q;i=int(pos);v=values[i]+(values[min(i+1,len(values)-1)]-values[i])*(pos-i)
        assert math.isclose(v,ref[field],abs_tol=1e-10)
checks.append('Reference means, sample SDs, medians and linear P10/P90 independently recomputed for all 22 fields')
cal,bins,coverage=calibration(truth,[[float(x['prob_'+s]) for s in STAGES] for x in rows],[float(x['uncertainty']) for x in rows])
dump('calibration_metrics.json',cal);write('calibration_bins.csv',bins);write('risk_coverage_data.csv',coverage)
inputs=json.loads((D/'data_manifest.json').read_text());split={s:[x['subject_id'] for x in inputs if x['split']==s] for s in ['train','val','test']}
summary={'recordings':24,'total_usable_epochs':sum(x['epochs'] for x in inputs),'split_subject_ids':split,'splits':{s:{'subjects':len(split[s]),'epochs':sum(x['epochs'] for x in inputs if x['split']==s)} for s in split},'dataset_name':'HMC v1.1','full_database_recordings':151,'scope':'Stored NPZ inputs used in the N1/N2 notebook; SN001 is a 190-epoch segment'}
dump('split_summary.json',summary)
write('split_subjects.csv',[{'subject_id':x['subject_id'],'split':x['split'],'usable_epochs':x['epochs'],**dict(zip(STAGES,x['stage_counts']))} for x in inputs])
write('stage_distribution.csv',[{'split':s,'stage':stage,'epochs':sum(x['stage_counts'][i] for x in inputs if x['split']==s)} for s in split for i,stage in enumerate(STAGES)])
for name in ['hyperparameters.json','model_layers.csv','preprocessing_config.json','transition_config.json','transition_matrix.csv','training_history.csv']:
    shutil.copy2(ROOT/'ppt_artifacts'/name,D/name)
environment=ROOT/'gui/.runtime/worker-check/artifacts/evaluation_environment.json'
if environment.exists():
    env=json.loads(environment.read_text(encoding='utf8'));env['scope']='Shared CPU runtime used for notebook reproduction and live SN009 GUI worker'
    dump('evaluation_environment.json',env)
    hyper=json.loads((D/'hyperparameters.json').read_text());hyper['archived_evaluation_environment']=hyper.pop('evaluation_environment',{})
    hyper['evaluation_environment']=env['versions'];hyper['source_notebook_cells_scope']='Historical Transformer training cells; unchanged checkpoint, current refinement is separate'
    dump('hyperparameters.json',hyper)
pre=json.loads((D/'preprocessing_config.json').read_text());pre['archived_edf_epoch_mapping']=pre.pop('epoch_mapping')
pre['epoch_mapping']='Current stored NPZ sequences, original index order; timing assumes contiguous 30-second epochs'
pre['lights_interval_available_in_archived_edf_audit']=pre.pop('lights_interval_available_for_test_recordings')
pre['current_lights_out_alignment_verified']=False;pre['spectral_features_input']='Stored EEG before the second inference normalization'
dump('preprocessing_config.json',pre)
r['model_parameters']=226309;r['verification']='Independent Colab reproduction matched saved notebook metrics, coefficients, training counts and domain profiles.'
r['raw_metrics']=metrics['raw'];r['refined_metrics']=metrics['refined'];dump('final_results.json',r)
dump('numerical_validation.json',{'passed':True,'checks':checks,'epochs_checked':3109,'profile_sources_checked':12,'matrix_shape':[4,23],'reference_shape':[16,23],'numeric_fields':22,'deviation_fields':21,'saved_notebook_metrics_match':True})
dump('profile_rules.json',{'reference_recordings':16,'domains':r['domains'],'regions':{'LOW':'x < P10','NORMAL':'P10 <= x <= P90','HIGH':'x > P90'},'profile_levels':{'0':'Within Reference','1':'Mild Deviation','2':'Moderate Deviation','3-4':'High Deviation'},'clinical_validation':False,'scope':'Descriptive comparison to HMC training reference'})
print(json.dumps({'passed':True,'metrics':metrics,'checks':len(checks),'total_epochs':summary['total_usable_epochs']},indent=2))
