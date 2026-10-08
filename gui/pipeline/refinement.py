"""Notebook-compatible spectral refinement and descriptive reference profiling."""
import math
from core import boundaries, validate_stages

FEATURES = ['delta_relative','theta_relative','alpha_relative','sigma_relative','beta_relative',
            'sigma_delta_ratio','theta_delta_ratio','alpha_delta_ratio','beta_delta_ratio']
BANDS = {'delta':(.5,4),'theta':(4,8),'alpha':(8,12),'sigma':(12,16),'beta':(16,30)}
DOMAINS = {'Sleep_Duration':['TST_minutes'],
 'Sleep_Continuity':['sleep_efficiency_percent','WASO_minutes','awakenings','fragmentation_index'],
 'Sleep_Initiation':['sleep_onset_latency_min'],
 'Sleep_Architecture':['N1_percent','N2_percent','N3_percent','REM_percent']}

def spectral_features(epochs):
    import numpy as np
    from scipy.signal import welch
    x=np.asarray(epochs)
    if x.ndim!=3 or x.shape[1:]!=(4,3000) or not np.isfinite(x).all():
        raise ValueError('Spectral extraction requires finite (epochs, 4, 3000) EEG')
    freq,psd=welch(x,fs=100,nperseg=400,noverlap=200,axis=-1)
    integrate=getattr(np,'trapezoid',np.trapz if hasattr(np,'trapz') else None)
    def power(low,high):
        mask=(freq>=low)&(freq<high)
        return integrate(psd[...,mask],freq[mask],axis=-1).mean(axis=1)
    total=power(.5,30)
    if np.any(total<=1e-12):raise ValueError('EEG has no measurable 0.5-30 Hz power')
    p={b:power(*limits) for b,limits in BANDS.items()}
    result=np.stack([p[b]/(total+1e-12) for b in BANDS]+[p[b]/(p['delta']+1e-12) for b in ['sigma','theta','alpha','beta']],axis=1)
    if not np.isfinite(result).all():raise ValueError('Nonfinite spectral features')
    return result

def refine_predictions(stages,features,model):
    """Positive logistic decision selects N2; original W/N3/REM are retained."""
    validate_stages(stages)
    if model.get('feature_order')!=FEATURES:raise ValueError('Refinement feature order mismatch')
    for key in ['mean','scale','coefficients']:
        if len(model[key])!=9 or any(not math.isfinite(float(v)) for v in model[key]):raise ValueError('Invalid refinement '+key)
    if any(s<=0 for s in model['scale']) or not math.isfinite(model['intercept']):raise ValueError('Invalid refinement scaling or intercept')
    if len(features)!=len(stages):raise ValueError('Feature and epoch counts differ')
    result=list(stages)
    for i,(stage,row) in enumerate(zip(stages,features)):
        if len(row)!=9 or any(not math.isfinite(float(v)) for v in row):raise ValueError('Expected nine finite EEG features')
        if stage not in (1,2):continue
        # The notebook passes float32 feature vectors into StandardScaler.
        import struct
        f32=lambda v:struct.unpack('f',struct.pack('f',float(v)))[0]
        standardized=[f32(f32(f32(v)-mu)/scale) for v,mu,scale in zip(row,model['mean'],model['scale'])]
        decision=model['intercept']+sum(v*c for v,c in zip(standardized,model['coefficients']))
        result[i]=2 if decision>0 else 1
    return result

def sleep_architecture(stages,timestamps=None,timing_known=True):
    validate_stages(stages)
    n=len(stages);sleep=[i for i,s in enumerate(stages) if s!=0];tst=len(sleep)/2
    continuous=timing_known and len(boundaries(timestamps,n))==2
    onset=sleep[0] if sleep else None
    rem=next((i for i in range(onset,n) if stages[i]==4),None) if onset is not None else None
    transitions=sum(a!=b for a,b in zip(stages,stages[1:]))
    return {'recording_minutes':n/2,'TST_minutes':tst,'sleep_efficiency_percent':100*len(sleep)/n,
     'sleep_onset_latency_min':onset/2 if continuous and onset is not None else None,
     'WASO_minutes':sum(s==0 for s in stages[onset:])/2 if continuous and onset is not None else None,
     'REM_latency_min':(rem-onset)/2 if continuous and rem is not None else None,
     **{name+'_percent':100*stages.count(s)/len(sleep) if sleep else None for s,name in enumerate(['N1','N2','N3','REM'],1)},
     'awakenings':sum(a!=0 and b==0 for a,b in zip(stages,stages[1:])) if continuous and sleep else None,
     'stage_transitions':transitions if continuous else None,
     'fragmentation_index':transitions/(tst/60) if continuous and tst else None}

def deviation_profile(values,reference):
    lookup={r['feature']:r for r in reference};deviations={}
    for feature,ref in lookup.items():
        if feature=='recording_minutes':continue
        x=values.get(feature);available=x is not None and math.isfinite(float(x))
        sd=ref.get('std');z=(x-ref['mean'])/sd if available and sd is not None and math.isfinite(sd) and sd>0 else None
        valid_bounds=all(ref.get(k) is not None and math.isfinite(ref[k]) for k in ['p10','p90'])
        flag='UNAVAILABLE' if not available or not valid_bounds else 'LOW' if x<ref['p10'] else 'HIGH' if x>ref['p90'] else 'NORMAL'
        deviations[feature]={'value':x if available else None,'z':z,'flag':flag,**ref}
    domains={}
    for domain,features in DOMAINS.items():
        flags=[deviations.get(f,{}).get('flag','UNAVAILABLE') for f in features]
        domains[domain]='UNAVAILABLE' if 'UNAVAILABLE' in flags else 'DEVIATED' if any(f!='NORMAL' for f in flags) else 'WITHIN_REFERENCE'
    count=sum(s=='DEVIATED' for s in domains.values());complete=all(s!='UNAVAILABLE' for s in domains.values())
    return {**{d+'_status':s for d,s in domains.items()},'deviated_domain_count':count if complete else None,
     'sleep_health_deviation_profile':['Within Reference','Mild Deviation','Moderate Deviation','High Deviation','High Deviation'][count] if complete else 'Unavailable',
     'deviations':deviations}
