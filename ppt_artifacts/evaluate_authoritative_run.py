"""New evaluation only. Never executes or edits original notebook cells.

Run with the authenticated Colab CLI; artifacts are written under /content.
"""
def _ppt_authoritative_evaluation():
    import os, sys, json, hashlib, shutil, zipfile, tarfile, platform, csv
    from pathlib import Path
    import importlib.metadata as md
    import numpy as np
    import pandas as pd
    import tensorflow as tf
    import mne
    from sklearn.metrics import (accuracy_score, balanced_accuracy_score, precision_score,
        recall_score, f1_score, cohen_kappa_score, confusion_matrix, classification_report,
        roc_auc_score, log_loss)

    run_id = 'HMC-PPT-20261007-01'
    base = Path('/content/drive/MyDrive/Sleep_Health_Profiling')
    pre = base/'processed/HMC_preprocessed'
    ckpt = base/'models/HMC_CHECKPOINTS/best_objective1_model.keras'
    out = Path('/content/ppt_authoritative_artifacts'); out.mkdir(exist_ok=True)
    names = ['Wake','N1','N2','N3','REM']
    channels = ['EEG F4-M1','EEG C4-M1','EEG O2-M1','EEG C3-M2']
    event_id = {'Sleep stage W':0,'Sleep stage N1':1,'Sleep stage N2':2,'Sleep stage N3':3,'Sleep stage R':4}
    def dump(name, value):
        (out/name).write_text(json.dumps(value, indent=2, allow_nan=False, default=lambda x: x.item() if hasattr(x,'item') else str(x)))
    def sha(path):
        h=hashlib.sha256()
        with open(path,'rb') as f:
            for block in iter(lambda:f.read(1024*1024),b''): h.update(block)
        return h.hexdigest()
    split = json.loads((pre/'subject_split.json').read_text())
    groups = {k.replace('_subjects',''):v for k,v in split.items()}
    all_ids = [s for v in groups.values() for s in v]
    assert len(all_ids)==len(set(all_ids)), 'SUBJECT LEAKAGE: evaluation stopped'
    assert set(all_ids)=={p.stem for p in pre.glob('*.npz')}
    dump('subject_split_source.json',split)
    shutil.copy2(ckpt,out/'authoritative_checkpoint.keras')
    shutil.copy2(ckpt.parent/'training_log.csv',out/'training_history_source.csv')
    with zipfile.ZipFile(ckpt) as z:
        config=json.loads(z.read('config.json')); meta=json.loads(z.read('metadata.json'))
    dump('checkpoint_config.json',config); dump('checkpoint_metadata.json',meta)
    model=tf.keras.models.load_model(ckpt,compile=False)
    assert model.input_shape==(None,4,3000) and model.output_shape==(None,5)
    assert model.layers[-1].get_config()['activation']=='softplus'
    with (out/'model_summary.txt').open('w') as f:
        model.summary(print_fn=lambda s:f.write(s+'\n'))
    layer_rows=[]
    for layer in model.layers:
        layer_rows.append({'name':layer.name,'type':type(layer).__name__,'output_shape':str(layer.output.shape),
                           'parameters':layer.count_params(),'settings':json.dumps(layer.get_config(),default=str)})
    pd.DataFrame(layer_rows).to_csv(out/'model_layers.csv',index=False)
    versions={p:md.version(p) for p in ['numpy','pandas','tensorflow','keras','scikit-learn','mne']}
    dump('evaluation_environment.json',{'versions':versions,'python':platform.python_version(),
        'platform':platform.platform(),'GPU':[str(x) for x in tf.config.list_physical_devices('GPU')]})
    header_rows=[]; subject_rows=[]; data_manifest=[]; sequences={}; repairs=[]
    for group, ids in groups.items():
        for sid in ids:
            file=pre/(sid+'.npz')
            with np.load(file,allow_pickle=False) as d:
                y=d['Y'].astype(np.int32)
                # Read .npy shape without decompressing the large EEG array.
                with zipfile.ZipFile(file) as z:
                    with z.open('X.npy') as f:
                        version=np.lib.format.read_magic(f)
                        shape,fortran,dtype=np.lib.format._read_array_header(f,version)
                assert shape==(len(y),4,3000) and np.all((y>=0)&(y<5))
            raw_paths=sorted((base/'Data/HMC').rglob(sid+'.edf'))
            score_paths=sorted((base/'Data/HMC').rglob(sid+'_sleepscoring.edf'))
            assert raw_paths and score_paths, f'Missing raw or scoring file: {sid}'
            raw=mne.io.read_raw_edf(str(raw_paths[0]),preload=False,verbose=False)
            raw.set_annotations(mne.read_annotations(str(score_paths[0])))
            assert all(c in raw.ch_names for c in channels)
            events,_=mne.events_from_annotations(raw,event_id=event_id,verbose=False)
            chunks,_=mne.events_from_annotations(raw,event_id=event_id,chunk_duration=30.,verbose=False)
            candidates=[ev for ev in [events,chunks] if len(ev)==len(y) and np.array_equal(ev[:,-1],y)]
            original_epochs=len(y); original_hash=sha(file)
            if not candidates:
                assert group=='test', f'Training/validation input mismatch: {sid}; retraining required'
                # A shortened test array is not a full recording. Reconstruct from
                # the untouched EDF with the exact training-source preprocessing.
                raw.load_data(); raw.pick(channels)
                raw.notch_filter(50,verbose=False);raw.filter(0.3,35,verbose=False);raw.resample(100,verbose=False)
                new_events,_=mne.events_from_annotations(raw,event_id=event_id,chunk_duration=30.,verbose=False)
                epochs=mne.Epochs(raw,new_events,event_id=event_id,tmin=0,tmax=30-1/100,baseline=None,
                    preload=True,reject_by_annotation=False,on_missing='ignore',verbose=False)
                x=epochs.get_data().astype(np.float32);y=epochs.events[:,-1].astype(np.int32)
                x=(x-x.mean(axis=2,keepdims=True))/(x.std(axis=2,keepdims=True)+1e-6)
                repaired_dir=Path('/content/ppt_corrected_test_inputs');repaired_dir.mkdir(exist_ok=True)
                file=repaired_dir/(sid+'.npz');np.savez_compressed(file,X=x,Y=y)
                ev=epochs.events.copy();times=ev[:,0]/100
                repairs.append({'subject_id':sid,'original_path':str(pre/(sid+'.npz')),'original_sha256':original_hash,
                    'original_epochs':original_epochs,'corrected_path':str(file),'corrected_epochs':len(y),
                    'reason':'saved label sequence could not be matched to complete EDF annotations',
                    'original_data_preserved':True,'requires_retraining':False,'test_only_reconstruction':True})
                print('CORRECTED_TEST_INPUT',sid,original_epochs,'->',len(y),flush=True)
                del x,epochs
            else:
                ev=candidates[0]; times=ev[:,0]/raw.info['sfreq']
            gaps=np.flatnonzero(np.abs(np.diff(times)-30)>0.01)
            header_rows.append({'subject_id':sid,'raw_path':str(raw_paths[0]),'scoring_path':str(score_paths[0]),
                'original_sampling_hz':256.0,'recording_seconds':raw.n_times/raw.info['sfreq'],
                'selected_channels':channels,'saved_epochs':len(y),'complete_30s_annotation_epochs':len(chunks),
                'gaps':len(gaps),'annotation_durations':np.unique(raw.annotations.duration).tolist(),
                'lights_markers':[{'onset':float(o),'duration':float(d),'description':str(a)} for o,d,a in zip(raw.annotations.onset,raw.annotations.duration,raw.annotations.description) if 'light' in str(a).lower()]})
            # Preserve trained-input evaluation. Gapped records are explicitly marked;
            # split sequence decoder at real gaps instead of pretending adjacency.
            sequences[sid]={'y':y,'times':times,'gaps':gaps,'path':file,'raw_path':raw_paths[0],'score_path':score_paths[0]}
            subject_rows.append({'split':group,'subject_id':sid,'recording_id':sid,'usable_epochs':len(y),
                **{n:int(np.sum(y==i)) for i,n in enumerate(names)},'gap_boundaries':len(gaps)})
            data_manifest.append({'subject_id':sid,'path':str(file),'bytes':file.stat().st_size,'sha256':sha(file)})
            print('AUDITED',group,sid,len(y),'gaps',len(gaps),flush=True)
            raw.close()
    dump('raw_recording_audit.json',header_rows); dump('data_manifest.json',data_manifest);dump('input_repairs.json',repairs)
    pd.DataFrame(subject_rows).to_csv(out/'split_subjects.csv',index=False)
    summary={'subjects':len(all_ids),'recordings':len(all_ids),'leakage_free':True,'split_subject_ids':groups,
        'splits':{g:{'subjects':len(ids),'epochs':int(sum(len(sequences[s]['y']) for s in ids))} for g,ids in groups.items()},
        'total_usable_epochs':int(sum(r['usable_epochs'] for r in subject_rows))}
    dump('split_summary.json',summary)
    pd.DataFrame([{'split':g,'stage':n,'count':sum(int(np.sum(sequences[s]['y']==i)) for s in ids),
                  'percentage':100*sum(int(np.sum(sequences[s]['y']==i)) for s in ids)/summary['splits'][g]['epochs']}
                 for g,ids in groups.items() for i,n in enumerate(names)]).to_csv(out/'stage_distribution.csv',index=False)
    train_y=np.concatenate([sequences[s]['y'] for s in groups['train']]); counts=np.bincount(train_y,minlength=5)
    weights=len(train_y)/(5*counts)
    pd.DataFrame({'stage':names,'training_count':counts,'weight':weights}).to_csv(out/'class_weights.csv',index=False)
    # Source decoder has Laplace pseudocount 1.0 and prevalence initialization.
    # Never join subjects or intervals separated by missing epochs.
    trans_count=np.ones((5,5),np.float64); init_count=np.ones(5,np.float64)
    for sid in groups['train']:
        seq=sequences[sid]; y=seq['y']; init_count+=np.bincount(y,minlength=5)
        valid=np.abs(np.diff(seq['times'])-30)<0.01
        np.add.at(trans_count,(y[:-1][valid],y[1:][valid]),1)
    init=init_count/init_count.sum(); trans=trans_count/trans_count.sum(axis=1,keepdims=True)
    pd.DataFrame(trans,index=names,columns=names).to_csv(out/'transition_matrix.csv',index_label='from_stage')
    dump('transition_config.json',{'pseudocount':1.0,'epsilon':1e-12,'emission_weight':0.9,'class_order':names,
        'initialization':'training label prevalence with pseudocount 1 per class','initial_probabilities':init.tolist(),
        'training_subjects':groups['train'],'sequence_boundary':'recording and any gap != 30 seconds'})
    def decode(p):
        logp=np.log(p+1e-12); logt=np.log(trans+1e-12)
        dp=np.zeros_like(logp,dtype=np.float64); back=np.zeros_like(logp,dtype=np.int32)
        dp[0]=np.log(init+1e-12)+0.9*logp[0]
        for t in range(1,len(p)):
            scores=dp[t-1][:,None]+logt
            back[t]=np.argmax(scores,axis=0); dp[t]=np.max(scores,axis=0)+0.9*logp[t]
        result=np.zeros(len(p),np.int32); result[-1]=np.argmax(dp[-1])
        for t in range(len(p)-2,-1,-1):result[t]=back[t+1,result[t+1]]
        return result
    records=[]; prob_all=[]; evidence_all=[]; per_subject=[]
    for sid in groups['test']:
        seq=sequences[sid]
        with np.load(seq['path'],allow_pickle=False) as d:x=d['X'].astype(np.float32)
        assert np.all(np.isfinite(x))
        evidence=model.predict(x,batch_size=128,verbose=0).astype(np.float64)
        assert np.all(np.isfinite(evidence)) and np.all(evidence>=0)
        alpha=evidence+1; p=alpha/alpha.sum(axis=1,keepdims=True); u=5/alpha.sum(axis=1)
        pred=p.argmax(axis=1); smooth=np.zeros(len(p),np.int32)
        bounds=np.r_[0,seq['gaps']+1,len(p)]
        for start,end in zip(bounds[:-1],bounds[1:]):smooth[start:end]=decode(p[start:end])
        for i in range(len(p)):
            records.append({'subject_id':sid,'recording_id':sid,'epoch_index':i,'timestamp_seconds':seq['times'][i],
                'true_label':int(seq['y'][i]),'raw_prediction':int(pred[i]),'soft_viterbi_prediction':int(smooth[i]),
                'uncertainty':u[i],'confidence':float(p[i].max()),**{f'prob_{n}':p[i,j] for j,n in enumerate(names)},
                **{f'evidence_{n}':evidence[i,j] for j,n in enumerate(names)},**{f'alpha_{n}':alpha[i,j] for j,n in enumerate(names)}})
        prob_all.append(p); evidence_all.append(evidence)
        per_subject.append({'subject_id':sid,'epochs':len(p),'raw_accuracy':accuracy_score(seq['y'],pred),
            'smoothed_accuracy':accuracy_score(seq['y'],smooth),'gaps':len(seq['gaps'])})
        print('INFERRED',sid,len(p),flush=True)
        del x
    frame=pd.DataFrame(records); frame.to_csv(out/'test_epoch_predictions.csv',index=False)
    p=np.concatenate(prob_all); evidence=np.concatenate(evidence_all)
    np.save(out/'test_probabilities.npy',p);np.save(out/'test_evidence.npy',evidence);np.save(out/'test_dirichlet_alpha.npy',evidence+1)
    frame[['subject_id','recording_id','epoch_index','timestamp_seconds','uncertainty','true_label','raw_prediction']].to_csv(out/'test_uncertainty.csv',index=False)
    yt=frame.true_label.to_numpy(); rawpred=frame.raw_prediction.to_numpy(); sm=frame.soft_viterbi_prediction.to_numpy()
    def metrics(pred):
        return {'accuracy':accuracy_score(yt,pred),'balanced_accuracy':balanced_accuracy_score(yt,pred),
            'macro_precision':precision_score(yt,pred,average='macro',zero_division=0),
            'macro_recall':recall_score(yt,pred,average='macro',zero_division=0),
            'macro_f1':f1_score(yt,pred,average='macro',zero_division=0),'weighted_f1':f1_score(yt,pred,average='weighted',zero_division=0),
            'cohen_kappa':cohen_kappa_score(yt,pred),'test_epochs':len(yt),'test_subjects':len(groups['test'])}
    raw_metrics=metrics(rawpred); smooth_metrics=metrics(sm)
    dump('overall_metrics.json',{'run_id':run_id,'raw':raw_metrics,'soft_viterbi':smooth_metrics})
    dump('smoothing_delta.json',{k:smooth_metrics[k]-raw_metrics[k] for k in ['accuracy','balanced_accuracy','macro_f1','weighted_f1','cohen_kappa']})
    pd.DataFrame([{'condition':'raw',**raw_metrics},{'condition':'soft_viterbi',**smooth_metrics}]).to_csv(out/'raw_vs_smoothed_metrics.csv',index=False)
    for key,pred in [('raw',rawpred),('smoothed',sm)]:
        cm=confusion_matrix(yt,pred,labels=range(5)); cmnorm=cm/cm.sum(axis=1,keepdims=True)
        prefix='' if key=='raw' else 'smoothed_'
        pd.DataFrame(cm,index=names,columns=names).to_csv(out/(prefix+'confusion_matrix_counts.csv'),index_label='true_stage')
        pd.DataFrame(cmnorm,index=names,columns=names).to_csv(out/(prefix+'confusion_matrix_normalized.csv'),index_label='true_stage')
        report=classification_report(yt,pred,labels=range(5),target_names=names,output_dict=True,zero_division=0)
        pd.DataFrame({k:v for k,v in report.items() if isinstance(v,dict)}).T.to_csv(out/(prefix+'classification_report.csv'),index_label='stage')
        assert cm.sum()==len(yt) and np.trace(cm)/len(yt)==metrics(pred)['accuracy']
    u=frame.uncertainty.to_numpy(); conf=p.max(axis=1); correct=(yt==rawpred)
    bins=[]; ece=0.
    edges=np.linspace(0,1,11)
    for i in range(10):
        mask=(conf>=edges[i])&((conf<edges[i+1]) if i<9 else (conf<=edges[i+1]))
        count=int(mask.sum()); a=float(correct[mask].mean()) if count else None; c=float(conf[mask].mean()) if count else None
        bins.append({'lower':edges[i],'upper':edges[i+1],'count':count,'accuracy':a,'mean_confidence':c})
        if count:ece+=count/len(yt)*abs(a-c)
    pd.DataFrame(bins).to_csv(out/'calibration_bins.csv',index=False)
    # Retain least uncertain epochs. Tie-breaking is stable original epoch order.
    order=np.argsort(u,kind='stable'); risk=np.cumsum(~correct[order])/np.arange(1,len(yt)+1);coverage=np.arange(1,len(yt)+1)/len(yt)
    pd.DataFrame({'coverage':coverage,'risk':risk,'uncertainty_threshold':u[order]}).to_csv(out/'risk_coverage_data.csv',index=False)
    calibration={'ECE_10_equal_width_bins':ece,'multiclass_brier_sum':float(np.mean(np.sum((p-np.eye(5)[yt])**2,axis=1))),
        'negative_log_likelihood':float(log_loss(yt,p,labels=range(5))),
        'error_detection_AUROC':float(roc_auc_score(~correct,u)),
        'AURC_discrete_mean':float(risk.mean()),'uncertainty_definition':'5 / sum(evidence + 1)',
        'correct_uncertainty_mean':float(u[correct].mean()),'incorrect_uncertainty_mean':float(u[~correct].mean()),
        'correct_uncertainty_median':float(np.median(u[correct])),'incorrect_uncertainty_median':float(np.median(u[~correct])),
        'correct_epochs':int(correct.sum()),'incorrect_epochs':int((~correct).sum()),'probabilities_calibrated':False}
    dump('calibration_metrics.json',calibration)
    # Exact source equations, clearly labeled evaluated-epoch proxies for records with gaps.
    def biomarkers(stages):
        n=len(stages); sleep=stages!=0; loc=np.flatnonzero(sleep)
        waso=int(np.sum(stages[loc[0]:loc[-1]+1]==0))*0.5 if len(loc) else 0.
        count=int(np.sum(np.isin(stages[:-1],[2,3,4])&np.isin(stages[1:],[0,1])))
        hours=sleep.sum()/120
        return {'Sleep_Efficiency_Pct':100*float(sleep.mean()),'WASO_Minutes':waso,'N3_Deep_Pct':100*float(np.mean(stages==3)),
            'SFI':float(count/hours) if hours>0 else 0.,'sleep_minutes':float(sleep.sum()/2),'evaluated_duration_minutes':n/2,
            'N1_Pct':100*float(np.mean(stages==1)),'N2_Pct':100*float(np.mean(stages==2)),'REM_Pct':100*float(np.mean(stages==4))}
    def risk_rule(m):
        if not all(np.isfinite(m[k]) for k in ['Sleep_Efficiency_Pct','WASO_Minutes','N3_Deep_Pct','SFI']):return 'Unclassified','Missing or nonfinite value'
        flags=[m['Sleep_Efficiency_Pct']<75,m['WASO_Minutes']>60,m['N3_Deep_Pct']<10,m['SFI']>10]
        return ('High Risk' if sum(flags)>=3 or m['Sleep_Efficiency_Pct']<65 or m['SFI']>15 else 'Mild Risk' if any(flags) else 'Healthy'),'; '.join(n for n,f in zip(['SE <75%','WASO >60 min','N3 <10%','SFI >10/h'],flags) if f)
    biom=[]
    for sid,sub in frame.groupby('subject_id',sort=False):
        for source,column in [('ground_truth','true_label'),('raw','raw_prediction'),('soft_viterbi','soft_viterbi_prediction')]:
            m=biomarkers(sub[column].to_numpy()); category,reasons=risk_rule(m)
            biom.append({'subject_id':sid,'source':source,**m,'risk_category':category,'reasons':reasons,
                'complete_contiguous_record':len(sequences[sid]['gaps'])==0,
                'interpretation':'research evaluated-epoch proxy; time in bed not directly verified'})
    bd=pd.DataFrame(biom); bd.to_csv(out/'subject_biomarkers.csv',index=False)
    bd[bd.source=='soft_viterbi'].to_csv(out/'subject_risk_profiles.csv',index=False)
    validation=[]
    for sid in groups['test']:
        a=bd[(bd.subject_id==sid)&(bd.source=='ground_truth')].iloc[0]
        for source in ['raw','soft_viterbi']:
            b=bd[(bd.subject_id==sid)&(bd.source==source)].iloc[0]
            validation.append({'subject_id':sid,'prediction_source':source,**{k+'_error':b[k]-a[k] for k in ['Sleep_Efficiency_Pct','WASO_Minutes','N3_Deep_Pct','SFI']},
                'true_risk':a.risk_category,'predicted_risk':b.risk_category,'risk_agreement':a.risk_category==b.risk_category})
    pd.DataFrame(validation).to_csv(out/'biomarker_validation.csv',index=False)
    history=pd.read_csv(out/'training_history_source.csv'); assert len(history)==10 and list(history.epoch)==list(range(10))
    history['epoch_number']=history.epoch+1; history.to_csv(out/'training_history.csv',index=False)
    selected=int(history.val_evidential_accuracy.idxmax()+1)
    hp={'model_name':'Fast SCFormer-U','architecture':'hybrid CNN–Transformer/self-attention–BiLSTM',
        'input_shape':[None,4,3000],'channels':channels,'parameters':model.count_params(),
        'trainable_parameters':int(sum(np.prod(w.shape) for w in model.trainable_weights)),
        'optimizer_saved':config['compile_config']['optimizer'],'learning_rate':config['compile_config']['optimizer']['config']['learning_rate'],
        'batch_size':128,'maximum_epochs':10,'actual_epochs':10,'selected_checkpoint_epoch':selected,
        'checkpoint_criterion':'maximum validation evidential accuracy','scheduler':'none in final training cell 207',
        'early_stopping':{'monitor':'val_evidential_accuracy','patience':5,'mode':'max','restore_best_weights':True,'triggered':False},
        'dropout':[0.2,0.1],'evidential_loss':'label smoothing 0.05; CE(alpha/sum(alpha)) + 0.003*sum(evidence*(1-smoothed_onehot))/5',
        'regularization':{'evidence_penalty':0.003,'weight_decay':None,'layer_regularizers':None},
        'split_seed':42,'training_seed':'not set in final training cells; earlier cell 90 sets 42 but execution state not recoverable',
        'training_hardware':'not recorded in final training log or checkpoint; cannot verify','checkpoint_keras_version':meta['keras_version'],
        'checkpoint_sha256':sha(ckpt),'evaluation_environment':versions,'class_weight_method':'N_train/(5*N_class)',
        'source_notebook_cells_zero_based':[203,205,206,207,211,212,213]}
    dump('hyperparameters.json',hp)
    dump('preprocessing_config.json',{'selected_channels':channels,'original_sampling_hz_verified':[256.0],
        'final_sampling_hz':100,'bandpass_hz':[0.3,35],'notch_hz':50,'filter_order':['channel selection','50Hz notch','0.3–35Hz bandpass','100Hz resampling'],
        'epoch_seconds':30,'normalization':'(X-mean_over_time)/(std_over_time+1e-6), float32, per epoch and channel',
        'reject_by_annotation':False,'amplitude_rejection':None,'source_notebook_cell_zero_based':201,
        'epoch_mapping':'annotation onsets; no chunk_duration in source; checked against saved labels',
        'original_artifact_rejection_claim_supported':False,'original_epoch_exclusion_counts':'not saved; gap/missing epoch count calculated from raw annotation mappings',
        'time_in_bed':'not directly recorded in npz; lights markers inspected in raw_recording_audit.json'})
    # Real EEG segment using the same verified recording, channel, and 30-second interval.
    sid=groups['test'][0]; seq=sequences[sid]
    raw=mne.io.read_raw_edf(str(seq['raw_path']),preload=True,verbose=False);raw.pick(channels)
    epoch_index=min(10,len(seq['y'])-1); start=float(seq['times'][epoch_index]); stop=start+30
    signal=raw.get_data(picks=[channels[0]],start=round(start*256),stop=round(stop*256))[0]
    raw.notch_filter(50,verbose=False);raw.filter(0.3,35,verbose=False);raw.resample(100,verbose=False)
    processed=raw.get_data(start=round(start*100),stop=round(stop*100)).astype(np.float32)
    processed=(processed-processed.mean(axis=1,keepdims=True))/(processed.std(axis=1,keepdims=True)+1e-6)
    np.savez(out/'eeg_example_data.npz',raw_volts=signal,raw_time=np.arange(len(signal))/256,
        processed=processed[0],processed_time=np.arange(processed.shape[1])/100)
    with np.load(seq['path'],allow_pickle=False) as d:saved=d['X'][epoch_index,0]
    dump('eeg_example_metadata.json',{'subject_id':sid,'channel':channels[0],'epoch_index':epoch_index,
        'start_seconds':start,'end_seconds':stop,'raw_sampling_hz':256,'processed_sampling_hz':100,
        'reprocessed_vs_saved_max_abs_difference':float(np.max(np.abs(saved-processed[0]))),
        'same_source_and_interval':True,'raw_unit':'volts','processed_unit':'normalized amplitude'})
    limitations=['Only four test recordings; no external validation.',
        'Final training hardware and global training RNG state not preserved.',
        'Notebook execution counts were cleared; saved outputs are historical evidence rather than complete execution provenance.',
        'Test records were evaluated repeatedly in notebook development; not a newly blinded clinical test.',
        'Rule thresholds have no clinical validation in this project.',
        'Evidential probabilities are not a separately fitted self-calibrated condition.']
    for r in header_rows:
        if r['gaps'] or r['saved_epochs']!=r['complete_30s_annotation_epochs']:
            limitations.append(f"{r['subject_id']}: saved epochs={r['saved_epochs']}, complete annotation epochs={r['complete_30s_annotation_epochs']}, gaps={r['gaps']}; profiles are evaluated-epoch proxies, not full-night clinical biomarkers.")
    result={'run_id':run_id,'checkpoint':str(ckpt),'checkpoint_sha256':sha(ckpt),'class_order':names,
        'raw_metrics':raw_metrics,'smoothed_metrics':smooth_metrics,'split':summary,'calibration':calibration,
        'selected_checkpoint_epoch':selected,'model_parameters':model.count_params(),'test_subjects':groups['test'],
        'per_subject':per_subject,'limitations':limitations,'evaluation_complete':True,'clinical_validation':False,
        'decoder_gap_boundary_correction':True,'input_repairs':repairs,
        'checkpoint_training_split_matches_saved_counts':bool(len(train_y)==15216 and summary['splits']['val']['epochs']==3619)}
    dump('final_results.json',result)
    with tarfile.open('/content/ppt_authoritative_artifacts.tar.gz','w:gz') as tar:
        for p in sorted(out.iterdir()):tar.add(p,arcname=p.name)
    print('FINAL_RESULTS',json.dumps(result),flush=True)
    print('ARTIFACT_ARCHIVE /content/ppt_authoritative_artifacts.tar.gz',flush=True)

try:
    _ppt_authoritative_evaluation()
finally:
    del _ppt_authoritative_evaluation
