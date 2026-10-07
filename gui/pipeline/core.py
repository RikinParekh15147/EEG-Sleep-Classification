"""Numerical operations shared by inference, reports and regression checks.

This module deliberately uses the Python standard library, so its checks can run
without installing TensorFlow or downloading the dataset.
"""
import math

STAGES = ['Wake', 'N1', 'N2', 'N3', 'REM']
CHANNELS = ['EEG F4-M1', 'EEG C4-M1', 'EEG O2-M1', 'EEG C3-M2']

def evidence_distribution(evidence):
    if len(evidence) != 5 or any(not math.isfinite(float(x)) or x < 0 for x in evidence):
        raise ValueError('Expected five finite, nonnegative evidence values')
    alpha = [float(x) + 1 for x in evidence]
    strength = sum(alpha)
    return [x / strength for x in alpha], 5 / strength, alpha

def validate_stages(stages):
    if not stages or any(isinstance(x,bool) or int(x)!=x or x not in range(5) for x in stages):
        raise ValueError('Expected a nonempty stage sequence with labels 0–4')

def boundaries(timestamps, count):
    if timestamps is None:
        return [0,count]
    if len(timestamps)!=count or any(not math.isfinite(float(x)) for x in timestamps):
        raise ValueError('Timestamp count or values do not match epochs')
    if any(b<=a for a,b in zip(timestamps,timestamps[1:])):
        raise ValueError('Epoch timestamps must increase')
    return [0,*[i+1 for i,(a,b) in enumerate(zip(timestamps,timestamps[1:])) if abs(b-a-30)>0.01],count]

def viterbi(probabilities, initial, transition, emission_weight=0.9, timestamps=None):
    if not probabilities:return []
    if not 0<=emission_weight<=2:raise ValueError('Emission weight must be between 0 and 2')
    if len(initial)!=5 or len(transition)!=5 or any(len(row)!=5 for row in transition):raise ValueError('Invalid transition matrix')
    for row in [initial,*transition,*probabilities]:
        if len(row)!=5 or any(not math.isfinite(float(x)) or x<0 for x in row) or abs(sum(row)-1)>1e-5:
            raise ValueError('Probabilities must be finite, nonnegative and sum to one')
    logt=[[math.log(x+1e-12) for x in row] for row in transition]
    result=[];bounds=boundaries(timestamps,len(probabilities))
    for start,end in zip(bounds,bounds[1:]):
        segment=probabilities[start:end]
        dp=[math.log(initial[j]+1e-12)+emission_weight*math.log(segment[0][j]+1e-12) for j in range(5)]
        back=[]
        for row in segment[1:]:
            best=[max(range(5),key=lambda k:dp[k]+logt[k][j]) for j in range(5)]
            dp=[dp[best[j]]+logt[best[j]][j]+emission_weight*math.log(row[j]+1e-12) for j in range(5)]
            back.append(best)
        path=[max(range(5),key=lambda j:dp[j])]
        for row in reversed(back):path.append(row[path[-1]])
        result.extend(reversed(path))
    return result

def biomarkers(stages,timestamps=None,timing_known=True):
    validate_stages(stages);n=len(stages);sleep=[i for i,x in enumerate(stages) if x!=0]
    breaks=set(boundaries(timestamps,n)[1:-1])
    hours=len(sleep)/120
    waso=sum(stages[i]==0 for i in range(sleep[0],sleep[-1]+1))*0.5 if sleep else 0.
    count=sum(i+1 not in breaks and a in [2,3,4] and b in [0,1] for i,(a,b) in enumerate(zip(stages,stages[1:])))
    return {'Sleep_Efficiency_Pct':100*len(sleep)/n,'WASO_Minutes':waso if timing_known else None,
      'N3_Deep_Pct':100*stages.count(3)/n,'SFI':(count/hours if hours else 0.) if timing_known else None,
      'sleep_minutes':len(sleep)/2,'evaluated_duration_minutes':n/2,
      'N1_Pct':100*stages.count(1)/n,'N2_Pct':100*stages.count(2)/n,'REM_Pct':100*stages.count(4)/n}

def risk_profile(values):
    keys=['Sleep_Efficiency_Pct','WASO_Minutes','N3_Deep_Pct','SFI']
    if any(values.get(k) is None or not math.isfinite(float(values[k])) for k in keys):return 'Unclassified','Timing or biomarker values are unavailable'
    if values.get('sleep_minutes',1)==0:return 'Unclassified','No scored sleep; source zero-WASO/SFI values are not a healthy profile'
    flags=[values[keys[0]]<75,values[keys[1]]>60,values[keys[2]]<10,values[keys[3]]>10]
    risk='High Risk' if sum(flags)>=3 or values[keys[0]]<65 or values[keys[3]]>15 else 'Mild Risk' if any(flags) else 'Healthy'
    return risk,'; '.join(name for name,flag in zip(['SE <75%','WASO >60 min','N3 <10%','SFI >10/h'],flags) if flag)

def classification(truth,predictions):
    validate_stages(truth);validate_stages(predictions)
    if len(truth)!=len(predictions):raise ValueError('Prediction and ground truth lengths differ')
    cm=[[0]*5 for _ in range(5)]
    for t,p in zip(truth,predictions):cm[t][p]+=1
    n=len(truth);supports=[sum(row) for row in cm];predicted=[sum(row[j] for row in cm) for j in range(5)]
    rows=[]
    for j,name in enumerate(STAGES):
        precision=cm[j][j]/predicted[j] if predicted[j] else 0
        recall=cm[j][j]/supports[j] if supports[j] else 0
        rows.append({'stage':name,'precision':precision,'recall':recall,'f1-score':2*precision*recall/(precision+recall) if precision+recall else 0,'support':supports[j]})
    accuracy=sum(cm[j][j] for j in range(5))/n
    expected=sum(a*b for a,b in zip(supports,predicted))/n**2
    present=[row['recall'] for row in rows if row['support']]
    metrics={'accuracy':accuracy,'balanced_accuracy':sum(present)/len(present),
      'macro_precision':sum(r['precision'] for r in rows)/5,'macro_recall':sum(r['recall'] for r in rows)/5,
      'macro_f1':sum(r['f1-score'] for r in rows)/5,'weighted_f1':sum(r['f1-score']*r['support'] for r in rows)/n,
      'cohen_kappa':(accuracy-expected)/(1-expected) if expected!=1 else None,'test_epochs':n}
    return metrics,rows,cm

def calibration(truth,probabilities,uncertainties):
    if not truth or len(truth)!=len(probabilities) or len(truth)!=len(uncertainties):raise ValueError('Calibration inputs differ in length')
    confidence=[max(p) for p in probabilities];correct=[max(range(5),key=lambda j:p[j])==t for t,p in zip(truth,probabilities)]
    n=len(truth);bins=[];ece=0
    for index in range(10):
        positions=[i for i,c in enumerate(confidence) if index/10<=c and (c<(index+1)/10 or index==9 and c<=1)]
        count=len(positions);acc=sum(correct[i] for i in positions)/count if count else None;conf=sum(confidence[i] for i in positions)/count if count else None
        bins.append({'lower':index/10,'upper':(index+1)/10,'count':count,'accuracy':acc,'mean_confidence':conf})
        if count:ece+=count/n*abs(acc-conf)
    order=sorted(range(n),key=lambda i:uncertainties[i]);errors=0;coverage=[]
    for j,i in enumerate(order,1):
        errors+=not correct[i];coverage.append({'coverage':j/n,'risk':errors/j,'uncertainty_threshold':uncertainties[i]})
    positives=sum(not x for x in correct);negatives=n-positives;rank_sum=0.;j=0
    while j<n:
        end=j+1
        while end<n and uncertainties[order[end]]==uncertainties[order[j]]:end+=1
        rank=(j+1+end)/2
        rank_sum+=rank*sum(not correct[order[k]] for k in range(j,end));j=end
    auc=(rank_sum-positives*(positives+1)/2)/(positives*negatives) if positives and negatives else None
    values={'ECE_10_equal_width_bins':ece,'multiclass_brier_sum':sum(sum((p[j]-(j==t))**2 for j in range(5)) for t,p in zip(truth,probabilities))/n,
      'negative_log_likelihood':-sum(math.log(max(p[t],1e-15)) for t,p in zip(truth,probabilities))/n,
      'error_detection_AUROC':auc,'AURC_discrete_mean':sum(x['risk'] for x in coverage)/n,
      'probabilities_calibrated':False,'uncertainty_definition':'5 / sum(evidence + 1)'}
    return values,bins,coverage
