"""Run-scoped Colab worker. Launched as an independent process, never the notebook."""
import csv
import hashlib
import json
import math
import os
import signal
import sys
import time
import traceback
import zipfile
from datetime import datetime, timezone
from pathlib import Path

from core import CHANNELS, STAGES, biomarkers, boundaries, calibration, classification, evidence_distribution, risk_profile, viterbi

CANCELLED=False

def cancel_signal(_sig,_frame):
    global CANCELLED
    CANCELLED=True

signal.signal(signal.SIGTERM,cancel_signal)
signal.signal(signal.SIGINT,cancel_signal)

class Cancelled(Exception):pass

def check_cancel():
    if CANCELLED:raise Cancelled('Cancelled by user')

def sha(file):
    with open(file,'rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def dump(file,value):
    file=Path(file);file.parent.mkdir(parents=True,exist_ok=True)
    temp=file.with_suffix(file.suffix+'.tmp')
    temp.write_text(json.dumps(value,indent=2,allow_nan=False),encoding='utf8');temp.replace(file)

def write_csv(file,rows,columns=None):
    if not rows and not columns:return
    with Path(file).open('w',newline='',encoding='utf8') as f:
        writer=csv.DictWriter(f,fieldnames=columns or list(rows[0]),extrasaction='ignore');writer.writeheader();writer.writerows(rows)

def load_edf(signal_path,scoring_path=None,legacy_labels=None):
    import numpy as np
    import mne
    raw=mne.io.read_raw_edf(str(signal_path),preload=True,verbose=False)
    original_hz=float(raw.info['sfreq'])
    missing=[c for c in CHANNELS if c not in raw.ch_names]
    if missing:raise ValueError('Missing required channels: '+', '.join(missing))
    if scoring_path:
        raw.set_annotations(mne.read_annotations(str(scoring_path)))
    raw.pick(CHANNELS)
    raw.notch_filter(50,verbose=False);raw.filter(0.3,35,verbose=False);raw.resample(100,verbose=False)
    events=None; labels=None
    if scoring_path:
        event_id={'Sleep stage W':0,'Sleep stage N1':1,'Sleep stage N2':2,'Sleep stage N3':3,'Sleep stage R':4}
        onsets,_=mne.events_from_annotations(raw,event_id=event_id,verbose=False)
        chunks,_=mne.events_from_annotations(raw,event_id=event_id,chunk_duration=30.,verbose=False)
        if legacy_labels is not None:
            for candidate in [onsets,chunks]:
                if len(candidate)==len(legacy_labels) and np.array_equal(candidate[:,-1],legacy_labels):events=candidate;break
        if events is None:events=chunks
        if len(events)==0:raise ValueError('No complete scored 30-second epochs were found')
        epochs=mne.Epochs(raw,events,event_id=event_id,tmin=0,tmax=30-1/100,baseline=None,preload=True,reject_by_annotation=False,on_missing='ignore',verbose=False)
        x=epochs.get_data().astype(np.float32);timestamps=(epochs.events[:,0]/100).tolist();labels=epochs.events[:,-1].astype(int)
        sample_start=int(epochs.events[0,0]-raw.first_samp)
    else:
        count=raw.n_times//3000
        if not count:raise ValueError('Recording is shorter than 30 seconds')
        x=raw.get_data()[:,:count*3000].reshape(4,count,3000).transpose(1,0,2).astype(np.float32)
        timestamps=[i*30. for i in range(count)];sample_start=0
    raw_signal=raw.get_data(start=sample_start,stop=sample_start+3000)*1e6
    x=(x-x.mean(axis=2,keepdims=True))/(x.std(axis=2,keepdims=True)+1e-6)
    preview={'channels':CHANNELS,'recording_id':Path(signal_path).stem,'epoch_index':0,'start_seconds':timestamps[0],
      'processed':x[0,:,::3].tolist(),'processed_sampling_hz':100/3,'raw':raw_signal[:,::3].tolist(),
      'raw_sampling_hz':100/3,'raw_unit':'µV (filtered and resampled)','processed_unit':'normalized amplitude'}
    raw.close()
    return x,labels,timestamps,preview,{'original_sampling_hz':original_hz,'timing':'verified EDF event/sample offsets','preprocessing':'project-v1','labels_available':labels is not None}

def find_edf(root,sid):
    signals=sorted(Path(root).rglob(sid+'.edf'));scores=sorted(Path(root).rglob(sid+'_sleepscoring.edf'))
    return (signals[0] if signals else None,scores[0] if scores else None)

def load_input(item,settings,output):
    import numpy as np
    sid=item['id'];file=Path(item['path']);scoring=Path(item['scoringPath']) if item.get('scoringPath') else None
    metadata={'recording_id':sid,'path':str(file),'sha256':sha(file),'bytes':file.stat().st_size,'source':item.get('source','drive')}
    if file.suffix.lower()=='.edf':
        x,y,times,preview,extra=load_edf(file,scoring);metadata.update(extra);return x,y,times,preview,metadata,True
    if file.suffix.lower()!='.npz':raise ValueError('Only EDF and compatible NPZ inputs are supported')
    with np.load(file,allow_pickle=False) as d:
        if 'X' not in d:raise ValueError('NPZ must contain X with shape (epochs, 4, 3000)')
        x=d['X'].astype(np.float32);y=d['Y'] if 'Y' in d else None
        times=d['timestamps'].astype(float).tolist() if 'timestamps' in d else None
    if x.ndim!=3 or x.shape[1:]!=(4,3000) or len(x)==0 or not np.isfinite(x).all():raise ValueError('Invalid X: expected finite, nonempty (epochs, 4, 3000) data')
    if y is not None:
        if y.ndim!=1 or len(y)!=len(x) or not np.isfinite(y).all() or not np.all(y==y.astype(int)) or not np.all((y>=0)&(y<5)):raise ValueError('Invalid labels: Y must match X and contain integer stages 0–4')
        y=y.astype(int)
    timing_known=times is not None or settings.get('assumeContiguous',False)
    repaired=False
    original_epochs=len(x)
    if item.get('source')=='project':
        signal_path,score=find_edf(settings['rawPath'],sid)
        if not signal_path or not score:raise ValueError('Project verification requires original EDF and scoring files for '+sid)
        import mne
        raw=mne.io.read_raw_edf(str(signal_path),preload=False,verbose=False);raw.set_annotations(mne.read_annotations(str(score)))
        event_id={'Sleep stage W':0,'Sleep stage N1':1,'Sleep stage N2':2,'Sleep stage N3':3,'Sleep stage R':4}
        candidates=[mne.events_from_annotations(raw,event_id=event_id,verbose=False)[0],mne.events_from_annotations(raw,event_id=event_id,chunk_duration=30.,verbose=False)[0]]
        matched=next((ev for ev in candidates if y is not None and len(ev)==len(y) and np.array_equal(ev[:,-1],y)),None)
        if matched is not None:times=(matched[:,0]/raw.info['sfreq']).tolist()
        raw.close()
        if matched is None:
            if sid not in settings.get('testIds',[]):raise ValueError('Training/validation input mismatch: '+sid+'. Inspect it before using this checkpoint.')
            x,y,times,preview,extra=load_edf(signal_path,score)
            repaired=True;corrected=output/(sid+'_corrected.npz');np.savez_compressed(corrected,X=x,Y=y,timestamps=times)
            metadata.update(extra);metadata.update({'repair':'Reconstructed complete scored epochs from original EDF; original file preserved','original_epochs':original_epochs,'corrected_epochs':len(x),'corrected_sha256':sha(corrected)})
        timing_known=True
    elif not settings.get('preprocessedAcknowledged',False):
        raise ValueError('Confirm that imported NPZ data uses the required channel order and project preprocessing')
    if times is None:times=[i*30. for i in range(len(x))]
    boundaries(times,len(x))
    if not repaired:preview={'channels':CHANNELS,'recording_id':sid,'epoch_index':0,'start_seconds':times[0],
      'processed':x[0,:,::3].tolist(),'processed_sampling_hz':100/3,'processed_unit':'normalized amplitude'}
    metadata.update({'epochs':len(x),'timing_known':timing_known,'timing':'verified project EDF alignment' if item.get('source')=='project' else 'NPZ timestamps' if timing_known and not settings.get('assumeContiguous') else 'user assumes contiguous 30s epochs' if timing_known else 'relative index only; continuity unverified',
      'labels_available':y is not None,'gap_boundaries':len(boundaries(times,len(x)))-2,'input_shape':list(x.shape)})
    return x,y,times,preview,metadata,timing_known

def inference(config,out,progress):
    import numpy as np
    import tensorflow as tf
    import importlib.metadata as md
    settings=config['settings'];checkpoint=Path(settings['checkpointPath'])
    if not checkpoint.is_file():raise FileNotFoundError('Checkpoint is missing: '+str(checkpoint))
    progress('Loading checkpoint',5)
    model=tf.keras.models.load_model(checkpoint,compile=False)
    if model.input_shape!=(None,4,3000) or model.output_shape!=(None,5) or model.layers[-1].get_config().get('activation')!='softplus':raise ValueError('Checkpoint must be a four-channel, five-stage evidential model')
    checkpoint_hash=sha(checkpoint)
    dump(out/'checkpoint_metadata.json',{'path':str(checkpoint),'sha256':checkpoint_hash,'parameters':model.count_params()})
    dump(out/'evaluation_environment.json',{'python':sys.version,'versions':{p:md.version(p) for p in ['numpy','tensorflow','keras','mne']},'gpu':[str(x) for x in tf.config.list_physical_devices('GPU')]})
    rows=[];profiles=[];inputs=[];per_recording=[];signals={};evidence_rows=[];bounds_all=[]
    initial=config['transition']['initial_probabilities'];transition=config['transition']['matrix']
    for index,item in enumerate(config['inputs']):
        check_cancel();sid=item['id'];progress('Validating '+sid,8+index/len(config['inputs'])*70)
        x,y,times,preview,metadata,timing_known=load_input(item,settings,out);inputs.append(metadata);signals[sid]=preview
        evidence=[];batch=settings.get('batchSize',128)
        for start in range(0,len(x),batch):
            check_cancel()
            values=model(x[start:start+batch],training=False).numpy()
            if not np.isfinite(values).all() or np.any(values<0):raise ValueError('Model produced invalid evidence')
            evidence.extend(values.astype(float).tolist())
            progress('Predicting '+sid,10+(index+(start+batch)/len(x))/len(config['inputs'])*68)
        distributions=[evidence_distribution(e) for e in evidence];probabilities=[d[0] for d in distributions]
        rawpred=[max(range(5),key=lambda j:p[j]) for p in probabilities]
        smoothing=settings.get('smoothing',True) and timing_known
        smooth=viterbi(probabilities,initial,transition,settings.get('emissionWeight',0.9),times) if smoothing else None
        true=y.astype(int).tolist() if y is not None else None
        for i,p in enumerate(probabilities):
            rows.append({'subject_id':sid,'recording_id':sid,'epoch_index':i,'timestamp_seconds':times[i],
              'true_label':true[i] if true is not None else None,'raw_prediction':rawpred[i],
              'soft_viterbi_prediction':smooth[i] if smooth is not None else None,'uncertainty':distributions[i][1],'confidence':max(p),
              **{f'prob_{name}':p[j] for j,name in enumerate(STAGES)},**{f'evidence_{name}':evidence[i][j] for j,name in enumerate(STAGES)},
              **{f'alpha_{name}':distributions[i][2][j] for j,name in enumerate(STAGES)}})
        for source,stages in [('ground_truth',true),('raw',rawpred),('soft_viterbi',smooth)]:
            if stages is None:continue
            values=biomarkers(stages,times,timing_known);category,reasons=risk_profile(values)
            profiles.append({'subject_id':sid,'source':source,**values,'risk_category':category,'reasons':reasons,
              'complete_contiguous_record':timing_known and len(boundaries(times,len(x)))==2,
              'interpretation':'research evaluated-epoch proxy; time in bed not directly verified; '+metadata['timing']})
        evidence_rows.extend(evidence)
        result={'subject_id':sid,'epochs':len(x),'gaps':len(boundaries(times,len(x)))-2,'timing_known':timing_known,'smoothed':smoothing,'labels_available':true is not None}
        if true is not None:
            result['raw_accuracy']=classification(true,rawpred)[0]['accuracy']
            if smooth is not None:result['smoothed_accuracy']=classification(true,smooth)[0]['accuracy']
        per_recording.append(result);del x
    check_cancel();progress('Calculating evaluation and sleep profiles',82)
    write_csv(out/'test_epoch_predictions.csv',rows);write_csv(out/'subject_biomarkers.csv',profiles)
    write_csv(out/'subject_risk_profiles.csv',[p for p in profiles if p['source']=='soft_viterbi'])
    np.save(out/'test_evidence.npy',np.asarray(evidence_rows))
    np.save(out/'test_dirichlet_alpha.npy',np.asarray(evidence_rows)+1)
    np.save(out/'test_probabilities.npy',np.asarray([[r['prob_'+n] for n in STAGES] for r in rows]))
    dump(out/'signals.json',signals);dump(out/'data_manifest.json',inputs)
    metrics={'run_id':config['id']};labeled=[r for r in rows if r['true_label'] is not None]
    if labeled:
        for condition,column,prefix in [('raw','raw_prediction',''),('soft_viterbi','soft_viterbi_prediction','smoothed_')]:
            subset=[r for r in labeled if r[column] is not None]
            if not subset:continue
            values,report,cm=classification([r['true_label'] for r in subset],[r[column] for r in subset]);values['test_subjects']=len(set(r['subject_id'] for r in subset))
            metrics[condition]=values;write_csv(out/(prefix+'classification_report.csv'),report)
            write_csv(out/(prefix+'confusion_matrix_counts.csv'),[{'true_stage':n,**dict(zip(STAGES,cm[i]))} for i,n in enumerate(STAGES)])
            write_csv(out/(prefix+'confusion_matrix_normalized.csv'),[{'true_stage':n,**{name:v/sum(cm[i]) if sum(cm[i]) else 0 for name,v in zip(STAGES,cm[i])}} for i,n in enumerate(STAGES)])
        cal,bins,coverage=calibration([r['true_label'] for r in labeled],[[r['prob_'+n] for n in STAGES] for r in labeled],[r['uncertainty'] for r in labeled])
        dump(out/'calibration_metrics.json',cal);write_csv(out/'calibration_bins.csv',bins);write_csv(out/'risk_coverage_data.csv',coverage)
    dump(out/'overall_metrics.json',metrics);dump(out/'transition_config.json',config['transition'])
    result={'run_id':config['id'],'checkpoint':str(checkpoint),'checkpoint_sha256':checkpoint_hash,'class_order':STAGES,
      'raw_metrics':metrics.get('raw'),'smoothed_metrics':metrics.get('soft_viterbi'),'per_subject':per_recording,
      'evaluation_complete':True,'clinical_validation':False,'model_parameters':model.count_params(),
      'input_repairs':[x for x in inputs if 'repair' in x],
      'limitations':['Rule-based research profiles; thresholds not clinically validated.','Probabilities are not separately calibrated.','Performance applies only to labeled evaluated inputs.'],
      'settings':settings}
    dump(out/'final_results.json',result)
    generate_plots(out,rows,metrics)
    return result

def generate_plots(out,rows,metrics):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    for sid in dict.fromkeys(r['subject_id'] for r in rows):
        sub=[r for r in rows if r['subject_id']==sid]
        fig,ax=plt.subplots(figsize=(14,4))
        for name,key in [('Ground truth','true_label'),('Raw','raw_prediction'),('Soft-Viterbi','soft_viterbi_prediction')]:
            if any(r[key] is None for r in sub):continue
            ax.step([r['timestamp_seconds']/3600 for r in sub],[r[key] for r in sub],where='post',label=name,alpha=.8)
        ax.set_yticks(range(5),STAGES);ax.invert_yaxis();ax.set_xlabel('Recording time (hours)');ax.set_title(sid+' · sleep stages');ax.legend();fig.tight_layout();fig.savefig(out/f'hypnogram_{sid}.png',dpi=160);plt.close(fig)
    for condition,column in [('raw','raw_prediction'),('soft_viterbi','soft_viterbi_prediction')]:
        sub=[r for r in rows if r['true_label'] is not None and r[column] is not None]
        if not sub:continue
        _,_,cm=classification([r['true_label'] for r in sub],[r[column] for r in sub]);fig,ax=plt.subplots(figsize=(6,5));ax.imshow(cm,cmap='Blues');ax.set_xticks(range(5),STAGES);ax.set_yticks(range(5),STAGES);ax.set_xlabel('Predicted');ax.set_ylabel('True');ax.set_title(condition+' confusion matrix')
        for i in range(5):
            for j in range(5):ax.text(j,i,str(cm[i][j]),ha='center',va='center')
        fig.tight_layout();fig.savefig(out/f'{condition}_confusion_matrix.png',dpi=160);plt.close(fig)

def preprocess(config,out,progress):
    import numpy as np
    completed=[]
    for index,item in enumerate(config['inputs']):
        check_cancel();progress('Preprocessing '+item['id'],5+85*index/max(1,len(config['inputs'])))
        if not item['path'].lower().endswith('.edf'):raise ValueError('Preprocessing requires EDF input')
        x,y,times,preview,meta=load_edf(item['path'],item.get('scoringPath'))
        target=out/(item['id']+'.npz');values={'X':x,'timestamps':np.asarray(times)}
        if y is not None:values['Y']=y
        np.savez_compressed(target,**values)
        completed.append({'id':item['id'],'file':target.name,'sha256':sha(target),'epochs':len(x),'labels_available':y is not None,**meta});del x
    dump(out/'preprocessing_manifest.json',completed);dump(out/'final_results.json',{'run_id':config['id'],'kind':'preprocess','recordings':completed})
    return {'recordings':completed}

def build_model(tf):
    layers=tf.keras.layers;inp=layers.Input(shape=(4,3000));x=layers.Permute((2,1))(inp)
    for filters,kernel in [(64,7),(128,5)]:
        x=layers.Conv1D(filters,kernel,strides=4,padding='same')(x);x=layers.BatchNormalization()(x);x=layers.ReLU()(x)
    attention=layers.MultiHeadAttention(num_heads=4,key_dim=16)(x,x);x=layers.LayerNormalization()(x+attention)
    ffn=layers.Dense(128,activation='gelu')(x);ffn=layers.Dense(128)(ffn);x=layers.LayerNormalization()(x+ffn)
    x=layers.Bidirectional(layers.LSTM(64,return_sequences=True))(x);x=layers.GlobalAveragePooling1D()(x);x=layers.Dropout(.2)(x)
    x=layers.Dense(128,activation='relu')(x);x=layers.Dropout(.1)(x);evidence=layers.Dense(5,activation='softplus')(x)
    return tf.keras.Model(inp,evidence)

def fit_transitions(config,out):
    import numpy as np
    import mne
    settings=config['settings'];counts=np.ones((5,5),dtype=float);initial=np.ones(5,dtype=float)
    for sid in config['split']['train']:
        check_cancel();file=Path(settings['processedPath'])/(sid+'.npz')
        with np.load(file,allow_pickle=False) as d:
            y=d['Y'].astype(int);times=d['timestamps'].astype(float).tolist() if 'timestamps' in d else None
        if times is None:
            signal_file,score=find_edf(settings['rawPath'],sid)
            if not signal_file or not score:raise ValueError('Training transition verification needs EDF/scoring files for '+sid)
            raw=mne.io.read_raw_edf(str(signal_file),preload=False,verbose=False);raw.set_annotations(mne.read_annotations(str(score)))
            ids={'Sleep stage W':0,'Sleep stage N1':1,'Sleep stage N2':2,'Sleep stage N3':3,'Sleep stage R':4}
            candidates=[mne.events_from_annotations(raw,event_id=ids,verbose=False)[0],mne.events_from_annotations(raw,event_id=ids,chunk_duration=30.,verbose=False)[0]]
            matched=next((ev for ev in candidates if len(ev)==len(y) and np.array_equal(ev[:,-1],y)),None)
            if matched is None:raise ValueError('Training input alignment mismatch: '+sid)
            times=(matched[:,0]/raw.info['sfreq']).tolist();raw.close()
        bounds=set(boundaries(times,len(y))[1:-1]);initial+=np.bincount(y,minlength=5)
        for i,(a,b) in enumerate(zip(y,y[1:])):
            if i+1 not in bounds:counts[a,b]+=1
    matrix=counts/counts.sum(axis=1,keepdims=True);initial=initial/initial.sum()
    result={'pseudocount':1.,'epsilon':1e-12,'emission_weight':.9,'class_order':STAGES,'initial_probabilities':initial.tolist(),'matrix':matrix.tolist(),'training_subjects':config['split']['train'],'sequence_boundary':'recording and any gap != 30 seconds','initialization':'training label prevalence with pseudocount 1 per class'}
    dump(out/'transition_config.json',result);write_csv(out/'transition_matrix.csv',[{'from_stage':n,**dict(zip(STAGES,matrix[i].tolist()))} for i,n in enumerate(STAGES)])
    return result

def training(config,out,progress):
    import numpy as np
    import tensorflow as tf
    settings=config['settings'];tf.keras.utils.set_random_seed(42)
    groups=config['split'];all_ids=[s for ids in groups.values() for s in ids]
    if len(all_ids)!=len(set(all_ids)):raise ValueError('Recording IDs overlap between splits')
    if not groups.get('train') or not groups.get('val'):raise ValueError('Training and validation groups must be nonempty')
    counts=np.zeros(5,dtype=np.int64)
    for sid in groups['train']:
        with np.load(Path(settings['processedPath'])/(sid+'.npz'),allow_pickle=False) as d:
            y=d['Y'];
            if y.ndim!=1 or not np.all(y==y.astype(int)) or not np.all((y>=0)&(y<5)):raise ValueError('Invalid training labels: '+sid)
            counts+=np.bincount(y.astype(int),minlength=5)
    if np.any(counts==0):raise ValueError('All five stages must occur in training data')
    transition=fit_transitions(config,out)
    weights=counts.sum()/(5*counts)
    def generator(ids,weighted):
        for sid in ids:
            check_cancel()
            with np.load(Path(settings['processedPath'])/(sid+'.npz'),allow_pickle=False) as d:x=d['X'].astype(np.float32);y=d['Y'].astype(np.int32)
            if x.shape!=(len(y),4,3000) or not np.isfinite(x).all() or not np.all((y>=0)&(y<5)):raise ValueError('Invalid training input: '+sid)
            for start in range(0,len(y),settings['batchSize']):
                check_cancel()
                for i in range(start,min(start+settings['batchSize'],len(y))):
                    if weighted:yield x[i],y[i],np.float32(weights[y[i]])
                    else:yield x[i],y[i]
            del x,y
    signature=(tf.TensorSpec((4,3000),tf.float32),tf.TensorSpec((),tf.int32))
    train=tf.data.Dataset.from_generator(lambda:generator(groups['train'],True),output_signature=signature+(tf.TensorSpec((),tf.float32),)).shuffle(512,seed=42,reshuffle_each_iteration=True).batch(settings['batchSize']).prefetch(1)
    val=tf.data.Dataset.from_generator(lambda:generator(groups['val'],False),output_signature=signature).batch(settings['batchSize']).prefetch(1)
    model=build_model(tf)
    def evidential_loss(y_true,evidence):
        onehot=.95*tf.one_hot(tf.cast(y_true,tf.int32),5)+.05/5;alpha=evidence+1.;p=alpha/tf.reduce_sum(alpha,axis=-1,keepdims=True)
        return -tf.reduce_sum(onehot*tf.math.log(p+1e-8),axis=-1)+.003*tf.reduce_sum(evidence*(1-onehot),axis=-1)/5
    def evidential_accuracy(y_true,evidence):
        alpha=evidence+1.;return tf.keras.metrics.sparse_categorical_accuracy(y_true,alpha/tf.reduce_sum(alpha,axis=-1,keepdims=True))
    model.compile(optimizer=tf.keras.optimizers.Adam(settings['learningRate']),loss=evidential_loss,metrics=[evidential_accuracy])
    class Progress(tf.keras.callbacks.Callback):
        def on_train_batch_end(self,batch,logs=None):
            if CANCELLED:self.model.stop_training=True
        def on_epoch_end(self,epoch,logs=None):
            progress('Training epoch '+str(epoch+1),5+85*(epoch+1)/settings['epochs'],{k:float(v) for k,v in (logs or {}).items()})
    checkpoint=out/'best_objective1_model.keras'
    callbacks=[tf.keras.callbacks.ModelCheckpoint(str(checkpoint),monitor='val_evidential_accuracy',mode='max',save_best_only=True),tf.keras.callbacks.CSVLogger(str(out/'training_history.csv')),tf.keras.callbacks.EarlyStopping(monitor='val_evidential_accuracy',mode='max',patience=5,restore_best_weights=True),Progress()]
    progress('Training Fast SCFormer-U',5)
    model.fit(train,validation_data=val,epochs=settings['epochs'],callbacks=callbacks,verbose=2)
    check_cancel()
    dump(out/'subject_split.json',groups);write_csv(out/'class_weights.csv',[{'stage':n,'training_count':int(counts[i]),'weight':float(weights[i])} for i,n in enumerate(STAGES)])
    result={'run_id':config['id'],'kind':'training','checkpoint_sha256':sha(checkpoint),'model_parameters':model.count_params(),'checkpoint':str(checkpoint),'settings':settings,'split':groups,'transition':transition,'training_seed':42,'clinical_validation':False,'limitations':['New training experiment; test evaluation has not run.','Model architecture matches baseline; streaming data and an explicit seed make this a separate experiment.']}
    dump(out/'final_results.json',result)
    return result

def main():
    config_path=Path(sys.argv[1]);config=json.loads(config_path.read_text());run_dir=config_path.parent;out=run_dir/'artifacts';out.mkdir(exist_ok=True)
    status_path=run_dir/'status.json';status={'id':config['id'],'status':'running','step':'Starting worker','progress':1,'pid':os.getpid(),'createdAt':datetime.now(timezone.utc).isoformat()}
    def progress(step,percent,extra=None):
        check_cancel();status.update({'step':step,'progress':min(95,round(percent,1)),'updatedAt':datetime.now(timezone.utc).isoformat()})
        if extra:status['epochMetrics']=extra
        dump(status_path,status);print(step,flush=True)
    exit_status='completed'
    try:
        dump(out/'run_config.json',config)
        result={'inference':inference,'preprocess':preprocess,'training':training}[config['kind']](config,out,progress)
        status['result']=result
    except Cancelled:
        exit_status='cancelled';status['error']='Cancelled by user'
    except Exception as e:
        exit_status='cancelled' if CANCELLED else 'failed';status['error']='Cancelled by user' if CANCELLED else str(e);(out/'error.txt').write_text(traceback.format_exc());traceback.print_exc()
    finally:
        status.update({'status':exit_status,'step':exit_status.capitalize(),'progress':100 if exit_status=='completed' else status['progress'],'finishedAt':datetime.now(timezone.utc).isoformat()})
        try:
            log=run_dir/'worker.log'
            if log.exists():
                import shutil;shutil.copy2(log,out/'worker.log')
            manifest=[{'path':str(f.relative_to(out)),'bytes':f.stat().st_size,'sha256':sha(f)} for f in out.rglob('*') if f.is_file()]
            dump(out/'artifact_manifest.json',{'run_id':config['id'],'artifacts':manifest});dump(out/'worker_status.json',status)
            with zipfile.ZipFile(run_dir/'results.zip','w',zipfile.ZIP_DEFLATED) as z:
                for file in out.rglob('*'):
                    if file.is_file():z.write(file,str(file.relative_to(out)))
            status['bundle']=str(run_dir/'results.zip')
            if config['settings'].get('persistDrive'):
                import shutil
                destination=Path(config['settings']['driveOutputs'])/config['id'];destination.mkdir(parents=True,exist_ok=True)
                shutil.copy2(run_dir/'results.zip',destination/'results.zip');status['driveBundle']=str(destination/'results.zip')
        except Exception as e:
            status['transferError']='Result packaging or Drive persistence failed: '+str(e)
        dump(status_path,status)

if __name__=='__main__':main()
