"""Independent reproduction of cells 8-45; no Transformer training or source writes."""
import csv, hashlib, json, os, sys, zipfile
from pathlib import Path
import numpy as np
import pandas as pd
import tensorflow as tf
from scipy.signal import welch
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score

BASE=Path('/content/drive/MyDrive/Sleep_Health_Profiling')
OUT=Path('/content/eeg_refinement_audit');OUT.mkdir(exist_ok=True)
PRE=BASE/'processed/HMC_preprocessed'
MODEL=BASE/'models/HMC_CHECKPOINTS/best_objective1_model.keras'
SPLIT=json.loads((PRE/'subject_split.json').read_text())
BANDS={'delta':(.5,4),'theta':(4,8),'alpha':(8,12),'sigma':(12,16),'beta':(16,30)}
FEATURES=[b+'_relative' for b in BANDS]+[b+'_delta_ratio' for b in ['sigma','theta','alpha','beta']]
DOMAINS={'Sleep_Duration':['TST_minutes'],'Sleep_Continuity':['sleep_efficiency_percent','WASO_minutes','awakenings','fragmentation_index'],'Sleep_Initiation':['sleep_onset_latency_min'],'Sleep_Architecture':['N1_percent','N2_percent','N3_percent','REM_percent']}
STAGES=['Wake','N1','N2','N3','REM']
def clean(v):
    if isinstance(v,dict):return {k:clean(x) for k,x in v.items()}
    if isinstance(v,list):return [clean(x) for x in v]
    if isinstance(v,(float,np.floating)):return float(v) if np.isfinite(v) else None
    if isinstance(v,(np.integer,)):return int(v)
    return v
def dump(name,value):(OUT/name).write_text(json.dumps(clean(value),indent=2,allow_nan=False))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
import importlib.metadata as package_metadata
dump('evaluation_environment.json',{'python':sys.version,'versions':{name:package_metadata.version(name) for name in ['numpy','pandas','tensorflow','keras','scipy','scikit-learn']},'gpu':[str(x) for x in tf.config.list_physical_devices('GPU')]})
def spectral(x):
    freq,psd=welch(x,fs=100,nperseg=400,noverlap=200,axis=-1)
    def power(low,high):
        m=(freq>=low)&(freq<high)
        return np.trapezoid(psd[...,m],freq[m],axis=-1).mean(axis=1)
    total=power(.5,30);p={b:power(*bounds) for b,bounds in BANDS.items()}
    return np.stack([p[b]/(total+1e-12) for b in BANDS]+[p[b]/(p['delta']+1e-12) for b in ['sigma','theta','alpha','beta']],axis=1)
def architecture(stages):
    s=np.asarray(stages);sleep=np.flatnonzero(s!=0);tst=len(sleep)/2
    onset=int(sleep[0]) if len(sleep) else None
    rem=np.flatnonzero(s[onset:]==4) if onset is not None else []
    transitions=int(np.count_nonzero(s[1:]!=s[:-1]))
    return {'recording_minutes':len(s)/2,'TST_minutes':tst,'sleep_efficiency_percent':len(sleep)/len(s)*100,
      'sleep_onset_latency_min':onset/2 if onset is not None else None,
      'WASO_minutes':np.count_nonzero(s[onset:]==0)/2 if onset is not None else None,
      'REM_latency_min':float(rem[0])/2 if len(rem) else None,
      **{STAGES[i]+'_percent':np.count_nonzero(s==i)/len(sleep)*100 if len(sleep) else None for i in range(1,5)},
      'awakenings':int(np.count_nonzero((s[1:]==0)&(s[:-1]!=0))),
      'stage_transitions':transitions,'fragmentation_index':transitions/(tst/60) if tst else None}
print('Loading existing checkpoint',flush=True)
model=tf.keras.models.load_model(MODEL,compile=False)
tables={};inputs=[]
for split,key in [('train','train_subjects'),('val','val_subjects'),('test','test_subjects')]:
    rows=[]
    for sid in SPLIT[key]:
        file=PRE/(sid+'.npz')
        with np.load(file,allow_pickle=False) as d:x=d['X'];y=d['Y']
        if len(x)!=len(y):raise ValueError('X/Y mismatch '+sid)
        x_normalized=((x-x.mean(axis=2,keepdims=True))/(x.std(axis=2,keepdims=True)+1e-6)).astype(np.float32)
        e=model.predict(x_normalized,batch_size=128,verbose=0)
        alpha=e+1;prob=alpha/alpha.sum(axis=1,keepdims=True);pred=prob.argmax(axis=1)
        features=np.concatenate([spectral(x[i:i+128]) for i in range(0,len(x),128)])
        for i in range(len(x)):
            rows.append({'subject_id':sid,'epoch_index':i,'timestamp_seconds':i*30,'true_label':int(y[i]),'raw_prediction':int(pred[i]),
             'uncertainty':float(5/alpha[i].sum()),'confidence':float(prob[i].max()),
             **{f'prob_{n}':float(prob[i,j]) for j,n in enumerate(STAGES)},
             **{f'evidence_{n}':float(e[i,j]) for j,n in enumerate(STAGES)},
             **dict(zip(FEATURES,features[i].astype(float)))})
        inputs.append({'subject_id':sid,'split':split,'epochs':len(x),'stage_counts':np.bincount(y,minlength=5).tolist(),'sha256':sha(file),'shape':list(x.shape)})
        print(split,sid,len(x),flush=True)
    tables[split]=pd.DataFrame(rows)
train=tables['train'];selected=train.raw_prediction.isin([1,2])&train.true_label.isin([1,2])
X=train.loc[selected,FEATURES].values.astype(np.float32);y=(train.loc[selected,'true_label']==2).astype(np.int32)
ref=Pipeline([('scaler',StandardScaler()),('classifier',LogisticRegression(class_weight='balanced',max_iter=2000,random_state=42))]);ref.fit(X,y)
scaler=ref.named_steps['scaler'];lr=ref.named_steps['classifier']
params={'feature_order':FEATURES,'mean':scaler.mean_.tolist(),'scale':scaler.scale_.tolist(),'coefficients':lr.coef_[0].tolist(),'intercept':float(lr.intercept_[0]),'classes':[1,2],'training_subjects':SPLIT['train_subjects'],'training_counts':{'N1':int((y==0).sum()),'N2':int((y==1).sum())},'checkpoint_sha256':sha(MODEL),'training_filter':'Transformer predicts N1/N2 AND true stage is N1/N2','welch':{'fs':100,'nperseg':400,'noverlap':200,'total_power_hz':[.5,30],'upper_bound_exclusive':True}}
dump('refinement_model.json',params)
night={};profiles=[]
for split,df in tables.items():
    df['refined_prediction']=df.raw_prediction
    mask=df.raw_prediction.isin([1,2]);df.loc[mask,'refined_prediction']=ref.predict(df.loc[mask,FEATURES].values.astype(np.float32))+1
    df.to_csv(OUT/(split+'_epoch_predictions.csv'),index=False)
    nights=[]
    for sid,sub in df.groupby('subject_id',sort=True):
        for source,column in [('ground_truth','true_label'),('raw','raw_prediction'),('refined','refined_prediction')]:
            v={'subject_id':sid,'source':source,**architecture(sub[column]),**sub[FEATURES].mean().to_dict()}
            if split=='test':profiles.append(v)
            if source=='refined':nights.append({'subject':sid,**{k:v for k,v in v.items() if k not in ['subject_id','source']}})
    night[split]=pd.DataFrame(nights)
    night[split].to_csv(OUT/(('train_reference_features' if split=='train' else 'master_sleep_health_features' if split=='test' else 'validation_night_features')+'.csv'),index=False)
reference=night['train'];numeric=[c for c in reference if c!='subject']
stats=pd.DataFrame([{'feature':c,'mean':reference[c].mean(),'std':reference[c].std(ddof=1),'median':reference[c].median(),'p10':reference[c].quantile(.1),'p90':reference[c].quantile(.9)} for c in numeric])
stats.to_csv(OUT/'reference_stats.csv',index=False);dump('reference_stats.json',stats.to_dict('records'))
lookup=stats.set_index('feature').to_dict('index')
for v in profiles:
    deviations={}
    for k in numeric:
        if k=='recording_minutes':continue
        r=lookup[k];value=v[k]
        deviations[k]={'value':clean(value),'z':(value-r['mean'])/r['std'] if value is not None and np.isfinite(r['std']) and r['std']>0 else None,'flag':'UNAVAILABLE' if value is None else 'LOW' if value<r['p10'] else 'HIGH' if value>r['p90'] else 'NORMAL',**r}
    domains={d:('UNAVAILABLE' if any(deviations[k]['flag']=='UNAVAILABLE' for k in keys) else 'DEVIATED' if any(deviations[k]['flag']!='NORMAL' for k in keys) else 'WITHIN_REFERENCE') for d,keys in DOMAINS.items()}
    count=sum(s=='DEVIATED' for s in domains.values())
    v.update({**{k+'_status':s for k,s in domains.items()},'deviated_domain_count':count,'sleep_health_deviation_profile':['Within Reference','Mild Deviation','Moderate Deviation','High Deviation','High Deviation'][count],'scope':'stored evaluated epochs; whole-night continuity unverified','deviations':deviations})
dump('subject_profiles.json',profiles)
pd.DataFrame([{k:v for k,v in p.items() if k!='deviations'} for p in profiles]).to_csv(OUT/'subject_biomarkers.csv',index=False)
test=tables['test'];baseline=test.raw_prediction;refined=test.refined_prediction;truth=test.true_label
metrics={}
for condition,pred in [('raw',baseline),('refined',refined)]:
    report=classification_report(truth,pred,labels=list(range(5)),target_names=STAGES,output_dict=True,zero_division=0)
    metrics[condition]={'accuracy':accuracy_score(truth,pred),'macro_f1':f1_score(truth,pred,average='macro'),'test_epochs':len(test),'test_subjects':4,'weighted_f1':report['weighted avg']['f1-score']}
    prefix='' if condition=='raw' else 'refined_'
    pd.DataFrame([{'stage':s,**report[s]} for s in STAGES]).to_csv(OUT/(prefix+'classification_report.csv'),index=False)
    cm=confusion_matrix(truth,pred,labels=list(range(5)))
    pd.DataFrame(cm,columns=STAGES).assign(true_stage=STAGES).to_csv(OUT/(prefix+'confusion_matrix_counts.csv'),index=False)
changed=baseline!=refined;bc=baseline==truth;rc=refined==truth
changes={'unchanged':int((~changed).sum()),'corrected':int((changed&~bc&rc).sum()),'degraded':int((changed&bc&~rc).sum()),'wrong_to_wrong':int((changed&~bc&~rc).sum()),'changed':int(changed.sum())}
n1n2=truth.isin([1,2]);only={'raw_accuracy':accuracy_score(truth[n1n2],baseline[n1n2]),'refined_accuracy':accuracy_score(truth[n1n2],refined[n1n2]),'denominator':int(n1n2.sum()),'definition':'All true N1/N2 epochs, including predictions outside N1/N2'}
test.to_csv(OUT/'test_epoch_predictions.csv',index=False)
dump('overall_metrics.json',{'run_id':'HMC-N1N2-20261007','raw':metrics['raw'],'refined':metrics['refined']})
dump('data_manifest.json',inputs)
dump('final_results.json',{'run_id':'HMC-N1N2-20261007','source_notebook':'Biomarker_N1_N2_Refinement.ipynb','checkpoint':str(MODEL),'checkpoint_sha256':sha(MODEL),'raw_metrics':metrics['raw'],'refined_metrics':metrics['refined'],'changes':changes,'n1n2_only':only,'split':SPLIT,'domains':DOMAINS,'matrix_shape':list(night['test'].shape),'reference_shape':list(reference.shape),'numeric_fields':len(numeric),'deviation_fields':len(numeric)-1,'clinical_validation':False,'limitations':['HMC is a heterogeneous clinical cohort, not a healthy normative population.','Deviation levels count domains, not clinical severity or disease risk.','Stored SN001 has 190 epochs (95 minutes); whole-night interpretation is unsupported.','Epoch-index timing assumes continuity; original EDF alignment needs separate verification.','Reference architecture is estimated in sample on training recordings.','Transformer uncertainty applies to the original five-stage output, not refined classification confidence.']})
with zipfile.ZipFile('/content/eeg_refinement_audit.zip','w',zipfile.ZIP_DEFLATED) as z:
    for p in OUT.iterdir():z.write(p,p.name)
import shutil
durable=BASE/'Features/biomarker_n1_n2_refinement/independent_audit'
durable.mkdir(parents=True,exist_ok=True)
shutil.copy2('/content/eeg_refinement_audit.zip',durable/'reproduction_verified.zip')
print('RESULT:'+json.dumps(clean({'metrics':metrics,'changes':changes,'n1n2_only':only,'training':params['training_counts'],'matrix':list(night['test'].shape),'profiles':[{k:v[k] for k in ['subject_id','sleep_health_deviation_profile','deviated_domain_count']} for v in profiles if v['source']=='refined']})),flush=True)
