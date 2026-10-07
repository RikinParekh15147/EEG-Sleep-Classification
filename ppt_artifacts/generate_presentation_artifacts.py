"""Create plots and explanatory artifacts from the one executed evaluation."""
from pathlib import Path
import json, shutil, csv, hashlib
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parent
R=json.loads((ROOT/'final_results.json').read_text())
HP=json.loads((ROOT/'hyperparameters.json').read_text())
RUN=R['run_id']
NAVY='#0B2E4F'; TEAL='#13A6A1'; BLUE='#2F6FED'; GRAY='#60788A'
STAGES=['Wake','N1','N2','N3','REM']
COLORS=[NAVY,'#4BBDB7',BLUE,'#176C83','#9C79B8']
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':17,'axes.titlesize':22,
    'axes.labelsize':18,'xtick.labelsize':16,'ytick.labelsize':16,'legend.fontsize':15,
    'axes.spines.top':False,'axes.spines.right':False,'axes.labelcolor':NAVY,
    'text.color':NAVY,'xtick.color':NAVY,'ytick.color':NAVY,'figure.facecolor':'white'})
def save(fig,name):
    fig.savefig(ROOT/name,dpi=180,facecolor='white',bbox_inches=None)
    plt.close(fig)
def note(fig,text):
    fig.text(.08,.025,text,fontsize=12,color=GRAY)
def grid(ax):
    ax.grid(axis='y',alpha=.16);ax.set_axisbelow(True)

H=pd.read_csv(ROOT/'training_history.csv')
for kind,train,val,ylabel in [('accuracy','evidential_accuracy','val_evidential_accuracy','Accuracy (%)'),
                            ('loss','loss','val_loss','Evidential loss')]:
    fig,ax=plt.subplots(figsize=(12,6));fig.subplots_adjust(bottom=.20,left=.10,right=.96,top=.88)
    scale=100 if kind=='accuracy' else 1
    ax.plot(H.epoch_number,H[train]*scale,'o-',color=TEAL,label='Training',lw=2.6)
    ax.plot(H.epoch_number,H[val]*scale,'o-',color=BLUE,label='Validation',lw=2.6)
    ax.axvline(HP['selected_checkpoint_epoch'],ls='--',color=NAVY,lw=1.7,label=f"Selected epoch {HP['selected_checkpoint_epoch']}")
    ax.set(xlabel='Epoch',ylabel=ylabel,title=f'Training and validation {kind}',xticks=H.epoch_number)
    ax.tick_params(labelsize=24);ax.xaxis.label.set_size(28);ax.yaxis.label.set_size(28);ax.title.set_size(28)
    ax.legend(fontsize=23);grid(ax)
    note(fig,'Saved training_log.csv; epoch 9 selected. Train loss uses class weights; validation loss is unweighted.')
    save(fig,f'training_{kind}.png')

D=pd.read_csv(ROOT/'stage_distribution.csv'); d=D[D.split=='train'].set_index('stage').loc[STAGES]
fig,ax=plt.subplots(figsize=(12,6));fig.subplots_adjust(bottom=.15,left=.10,right=.96,top=.84)
bars=ax.bar(STAGES,d['count'],color=COLORS,width=.65)
for b,(_,row) in zip(bars,d.iterrows()):
    ax.text(b.get_x()+b.get_width()/2,b.get_height()+60,f"{int(row['count']):,}\n{row.percentage:.2f}%",ha='center',fontsize=17)
ax.set(ylabel='Training epochs',title='Verified training-set sleep-stage distribution',ylim=(0,d['count'].max()*1.25));grid(ax)
save(fig,'stage_distribution.png')

def matrix_plot(csvname,png,title,percent=True):
    df=pd.read_csv(ROOT/csvname,index_col=0).loc[STAGES,STAGES]
    fig,ax=plt.subplots(figsize=(10,7.6));fig.subplots_adjust(left=.17,bottom=.18,right=.88,top=.90)
    arr=df.to_numpy(); im=ax.imshow(arr,cmap='Blues',vmin=0,vmax=1 if percent else None)
    for i in range(5):
        for j in range(5):
            text=f'{arr[i,j]*100:.1f}%' if percent else f'{int(arr[i,j]):,}'
            ax.text(j,i,text,ha='center',va='center',fontsize=20,color='white' if arr[i,j]>(.5 if percent else arr.max()*.55) else NAVY)
    ax.set(xticks=range(5),yticks=range(5),xticklabels=STAGES,yticklabels=STAGES,
           xlabel='Predicted stage' if 'transition' not in csvname else 'Next stage',
           ylabel='True stage' if 'transition' not in csvname else 'Current stage',title=title)
    cb=fig.colorbar(im,ax=ax,fraction=.045,pad=.035);cb.set_label('Row probability' if percent else 'Epoch count')
    note(fig,'Class order: Wake, N1, N2, N3, REM. '+('Training labels only; pseudocount 1.' if 'transition' in csvname else RUN))
    save(fig,png)
matrix_plot('confusion_matrix_normalized.csv','confusion_matrix_normalized.png','Raw evidential model: row-normalized confusion matrix')
matrix_plot('confusion_matrix_counts.csv','confusion_matrix_counts.png','Raw evidential model: confusion counts',False)
matrix_plot('smoothed_confusion_matrix_normalized.csv','smoothed_confusion_matrix_normalized.png','Soft-Viterbi: row-normalized confusion matrix')
matrix_plot('transition_matrix.csv','transition_matrix.png','Training-label transition probabilities')

C=pd.read_csv(ROOT/'classification_report.csv',index_col=0).loc[STAGES]
fig,ax=plt.subplots(figsize=(12,6));fig.subplots_adjust(bottom=.15,left=.10,right=.96,top=.85)
bars=ax.bar(STAGES,C['f1-score']*100,color=COLORS,width=.65)
for b,v in zip(bars,C['f1-score']):ax.text(b.get_x()+b.get_width()/2,b.get_height()+2,f'{v*100:.2f}%',ha='center')
ax.set(ylabel='F1 score (%)',ylim=(0,105),title='Raw-model F1 score by sleep stage');grid(ax);save(fig,'class_f1.png')

P=pd.read_csv(ROOT/'test_epoch_predictions.csv');cal=json.loads((ROOT/'calibration_metrics.json').read_text())
correct=P.true_label==P.raw_prediction
fig,ax=plt.subplots(figsize=(12,6));fig.subplots_adjust(bottom=.20,left=.10,right=.96,top=.85)
bins=np.linspace(0,1,41)
ax.hist(P.loc[correct,'uncertainty'],bins=bins,density=True,alpha=.66,color=TEAL,label=f'Correct (n={correct.sum():,})')
ax.hist(P.loc[~correct,'uncertainty'],bins=bins,density=True,alpha=.60,color=BLUE,label=f'Incorrect (n={(~correct).sum():,})')
ax.set(xlabel='Dirichlet uncertainty: u = 5 / Σ(evidence + 1)',ylabel='Density',title='Evidential uncertainty: correct versus incorrect');ax.legend();grid(ax)
note(fig,f"Mean uncertainty: correct {cal['correct_uncertainty_mean']:.3f}; incorrect {cal['incorrect_uncertainty_mean']:.3f}. Error AUROC {cal['error_detection_AUROC']:.3f}.")
save(fig,'uncertainty_correct_incorrect.png')

B=pd.read_csv(ROOT/'calibration_bins.csv');nonempty=B[B['count']>0]
fig,(ax,bx)=plt.subplots(2,1,figsize=(10,7),gridspec_kw={'height_ratios':[3,1]},sharex=True)
fig.subplots_adjust(left=.12,bottom=.18,right=.94,top=.90,hspace=.12)
ax.plot([0,1],[0,1],ls='--',color=GRAY,label='Perfect calibration')
ax.bar((nonempty.lower+nonempty.upper)/2,nonempty.accuracy,width=.075,color=TEAL,alpha=.85,label='Observed accuracy')
ax.plot(nonempty.mean_confidence,nonempty.accuracy,'o-',color=BLUE,label='Occupied bins')
ax.set(ylabel='Observed accuracy',ylim=(0,1),title='Reliability diagram — raw Dirichlet mean probabilities');ax.legend(fontsize=12);grid(ax)
bx.bar((B.lower+B.upper)/2,B['count'],width=.08,color=BLUE);bx.set(xlabel='Confidence (maximum class probability)',ylabel='Epochs',xlim=(0,1));grid(bx)
note(fig,f"10 equal-width bins; ECE {cal['ECE_10_equal_width_bins']:.4f}. No temperature scaling or separately fitted calibrator.")
save(fig,'reliability_diagram.png')
RC=pd.read_csv(ROOT/'risk_coverage_data.csv')
fig,ax=plt.subplots(figsize=(12,6));fig.subplots_adjust(bottom=.20,left=.10,right=.96,top=.85)
ax.plot(RC.coverage*100,RC.risk*100,color=BLUE,lw=2.6,label='Retain least uncertain epochs')
ax.axhline(100*(1-R['raw_metrics']['accuracy']),color=GRAY,ls='--',label='All-epoch error rate')
ax.set(xlabel='Coverage: retained test epochs (%)',ylabel='Risk: retained-set error (%)',title='Selective prediction risk–coverage curve',xlim=(0,100));ax.legend();grid(ax)
note(fig,f"Sort by u = 5 / Σα, ascending. AURC = discrete mean risk = {cal['AURC_discrete_mean']:.4f}. No clinical risk interpretation.")
save(fig,'risk_coverage_curve.png')

E=np.load(ROOT/'eeg_example_data.npz');EM=json.loads((ROOT/'eeg_example_metadata.json').read_text())
for raw in [True,False]:
    fig,ax=plt.subplots(figsize=(12,5.4));fig.subplots_adjust(left=.12,bottom=.22,right=.96,top=.84)
    t=E['raw_time' if raw else 'processed_time'];s=E['raw_volts' if raw else 'processed']*(1e6 if raw else 1)
    ax.plot(t,s,color=BLUE if raw else TEAL,lw=.8)
    ax.set(xlabel='Seconds within the same 30-second interval',ylabel='Amplitude (µV)' if raw else 'Normalized amplitude',xlim=(0,30),
           title=f"{'Raw' if raw else 'Preprocessed'} EEG — {EM['subject_id']}, {EM['channel']}")
    grid(ax);note(fig,f"Recording interval {EM['start_seconds']:.0f}–{EM['end_seconds']:.0f} s. "+('Original EDF at 256 Hz.' if raw else '50 Hz notch → 0.3–35 Hz bandpass → 100 Hz; per-channel epoch normalization.'))
    save(fig,'raw_eeg_example.png' if raw else 'preprocessed_eeg_example.png')

stage_map=np.array([0,2,3,4,1]);vertical=['Wake','REM','N1','N2','N3']
def draw_sequence(ax,sub,column,color,label):
    times=sub.timestamp_seconds.to_numpy()/3600;ys=stage_map[sub[column].to_numpy()]
    gaps=np.flatnonzero(np.abs(np.diff(times)*3600-30)>.01)
    bounds=np.r_[0,gaps+1,len(sub)]
    for start,end in zip(bounds[:-1],bounds[1:]):
        tx=np.r_[times[start:end],times[end-1]+1/120];yx=np.r_[ys[start:end],ys[end-1]]
        ax.step(tx,yx,where='post',color=color,lw=1.2,label=label if start==0 else None)
    ax.set(yticks=range(5),yticklabels=vertical,ylim=(4.35,-.35));ax.grid(alpha=.15)
for idx,sid in enumerate(R['test_subjects'],1):
    sub=P[P.subject_id==sid]
    fig,axes=plt.subplots(3,1,figsize=(16,7),sharex=True);fig.subplots_adjust(left=.085,right=.97,bottom=.12,top=.90,hspace=.38)
    for ax,column,color,label in zip(axes,['true_label','raw_prediction','soft_viterbi_prediction'],[NAVY,BLUE,TEAL],['Ground truth','Raw evidential model','Soft-Viterbi']):
        draw_sequence(ax,sub,column,color,label);ax.set_title(label,loc='left',fontsize=16,pad=5)
    axes[-1].set_xlabel('Hours from recording start');fig.suptitle(f"Test recording {sid} — {len(sub):,} real EEG epochs",fontsize=23)
    note(fig,RUN+'; shared stage order and time axis; no synthetic sequences.')
    save(fig,f'hypnogram_subject_{idx}.png');shutil.copy2(ROOT/f'hypnogram_subject_{idx}.png',ROOT/f'hypnogram_subject_{sid}.png')

fig,axes=plt.subplots(3,1,figsize=(16,7.6),sharex=False);fig.subplots_adjust(left=.085,right=.97,bottom=.14,top=.90,hspace=.48)
for ax,sid in zip(axes,R['test_subjects'][1:]):
    sub=P[P.subject_id==sid]
    for col,color,label in [('true_label',NAVY,'Ground truth'),('raw_prediction',BLUE,'Raw'),('soft_viterbi_prediction',TEAL,'Soft-Viterbi')]:draw_sequence(ax,sub,col,color,label)
    ax.set_title(sid,loc='left',fontsize=18);ax.set_xlabel('Hours from recording start',fontsize=13)
axes[0].legend(loc='upper right',ncol=3,fontsize=12)
fig.suptitle('Additional test recordings — overlaid genuine hypnograms',fontsize=22)
note(fig,'Overlay legend applies to all panels; stage order Wake, REM, N1, N2, N3. '+RUN)
save(fig,'additional_hypnograms.png')

rules={'scope':'Rule-based research profile; not a medical diagnosis; thresholds not clinically validated here',
       'source_notebook_cell_zero_based':215,'inputs':{'SE':'percent of evaluated duration','WASO':'minutes between first and last sleep epoch','N3':'percent of evaluated epochs','SFI':'N2/N3/REM to Wake/N1 transitions per hour of scored sleep'},
       'flags':[{'name':'Low SE','condition':'SE < 75','unit':'%'},{'name':'High WASO','condition':'WASO > 60','unit':'min'},
                {'name':'Low N3','condition':'N3 < 10','unit':'%'},{'name':'High SFI','condition':'SFI > 10','unit':'transitions / sleep hour'}],
       'precedence':[{'category':'High Risk','logic':'flag_count >= 3 OR SE < 65 OR SFI > 15'},
                     {'category':'Mild Risk','logic':'otherwise flag_count >= 1'},{'category':'Healthy','logic':'otherwise no flags'}],
       'missing_values':'Original function has no guard. New evaluation returns Unclassified for missing/nonfinite inputs; no such test cases occurred.'}
(ROOT/'risk_rules.json').write_text(json.dumps(rules,indent=2))
pd.DataFrame([{'rule_type':'flag','category':r['name'],'condition':r['condition'],'units':r['unit'],'precedence':''} for r in rules['flags']]+
             [{'rule_type':'assignment','category':r['category'],'condition':r['logic'],'units':'SE %, SFI transitions/sleep hour','precedence':i+1} for i,r in enumerate(rules['precedence'])]).to_csv(ROOT/'risk_rules_table.csv',index=False)
(ROOT/'biomarker_equations.md').write_text('''# Exact implemented research biomarkers

Source: original notebook cell 215 (zero-based); reproduced in evaluate_authoritative_run.py.
Let N be evaluated 30-second epochs, z_t the stage (0=Wake,1=N1,2=N2,3=N3,4=REM).
Let n_sleep = sum(1[z_t != 0]), T_sleep_min = n_sleep / 2, and T_eval_min = N / 2.

- SE (%) = 100 * n_sleep / N. This is evaluated-recording efficiency, not verified time-in-bed efficiency.
- WASO (min) = 0.5 * sum(1[z_t = 0], t from first to last non-Wake epoch inclusive).
  Trailing Wake after the final sleep epoch is excluded by this source definition.
  If no sleep occurs, the source returns 0 minutes; this should not be interpreted as good sleep.
- N3 (%) = 100 * sum(1[z_t = 3]) / N. The denominator is all evaluated epochs, not total sleep time.
- SFI (transitions/sleep hour) = count(z_t in {N2,N3,REM} AND z_(t+1) in {Wake,N1}) / (n_sleep / 120).
  This is a coarse stage-transition proxy, not EEG micro-arousal scoring. The source returns 0 if no sleep.
  New evaluation guards missing/nonfinite risk inputs; no zero-sleep subject occurs in this run.

Raw, smoothed and ground-truth values are in separate source rows. No mixing of label sources.
All authoritative test sequences were reconstructed/verified as contiguous before biomarkers were used.
Lights-off/on annotations provide a lights interval (lights_interval_audit.json), but source biomarkers
use evaluated-epoch duration. NPZ arrays have no time-in-bed field or independently verified bed-entry log.
''')
(ROOT/'soft_viterbi_pseudocode.txt').write_text('''Class order: Wake, N1, N2, N3, REM.
Training only: C[i,j]=1+number of adjacent training labels i->j.
A[i,j]=C[i,j]/sum_j C[i,j]. Never join recordings or missing-epoch gaps.
Initial prior pi[j]=(1+training prevalence[j])/(5+number of training epochs).
Evidence e>=0; alpha=e+1; p[t,j]=alpha[t,j]/sum_j alpha[t,j].
For each independent recording/contiguous interval:
  D[0,j]=log(pi[j]+1e-12)+0.9*log(p[0,j]+1e-12)
  For t=1..T-1 and j=0..4:
    q[i]=D[t-1,i]+log(A[i,j]+1e-12)
    back[t,j]=argmax_i q[i]
    D[t,j]=max_i q[i]+0.9*log(p[t,j]+1e-12)
  z[T-1]=argmax_j D[T-1,j]
  Backtrack z[t]=back[t+1,z[t+1]].
This is weighted log-space MAP Viterbi, not differentiable soft-DP.
Laplace smoothing permits every transition; no transition is forbidden.
Emission weight 0.9 comes from source cell 213; no test-set retuning.
''')
lit=[{'study':'SeqSleepNet-30 (Phan et al.)','year':2019,'dataset':'MASS, 200 subjects','modality':'EEG C4-A1 + EOG + EMG',
      'protocol':'20-fold subject CV; 180/10/10 train/validation/test per fold','accuracy':.871,'macro_f1':.833,'kappa':.815,
      'doi':'10.1109/TNSRE.2019.2896659','source':'https://arxiv.org/html/1809.10932','comparison_note':'Different dataset, modalities and CV protocol; contextual comparison only.'},
     {'study':'DeepSleepNet (Supratak et al.)','year':2017,'dataset':'Sleep-EDF, 20 subjects','modality':'Single-channel EEG Fpz-Cz',
      'protocol':'20-fold subject cross-validation','accuracy':.82,'macro_f1':.769,'kappa':.76,
      'doi':'10.1109/TNSRE.2017.2721116','source':'https://arxiv.org/pdf/1703.04046','comparison_note':'Different dataset, EEG montage and CV protocol; contextual comparison only.'},
     {'study':'Current Fast SCFormer-U (raw)','year':2026,'dataset':'HMC subset, 24 recordings','modality':'Four EEG channels',
      'protocol':'Fixed subject/recording split 16/4/4; corrected SN001 test input','accuracy':R['raw_metrics']['accuracy'],
      'macro_f1':R['raw_metrics']['macro_f1'],'kappa':R['raw_metrics']['cohen_kappa'],'doi':'','source':RUN,
      'comparison_note':'Not a like-for-like benchmark or state-of-the-art claim.'}]
pd.DataFrame(lit).to_csv(ROOT/'literature_comparison.csv',index=False)
(ROOT/'references.txt').write_text('''[1] Phan H et al. SeqSleepNet. IEEE TNSRE 27(3), 400–410 (2019). DOI: 10.1109/TNSRE.2019.2896659.
    https://arxiv.org/html/1809.10932 ; Sections II, V-A, V-D/Table II.
[2] Supratak A et al. DeepSleepNet. IEEE TNSRE 25(11), 1998–2007 (2017). DOI: 10.1109/TNSRE.2017.2721116.
    https://arxiv.org/pdf/1703.04046 ; Tables III and IV and experimental protocol.
[3] Alvarez-Estevez D, Rijsman RM. HMC sleep staging database v1.1 (2022). DOI: 10.13026/t79q-fr32.
    https://physionet.org/content/hmc-sleep-staging/1.1/ ; four EEG channels, 256Hz, dataset description.
[4] Alvarez-Estevez D, Rijsman RM. Inter-database validation of a deep learning approach for automatic sleep scoring.
    PLoS ONE 16(8), e0256111 (2021). DOI: 10.1371/journal.pone.0256111.
External metrics are contextual: dataset, modality and protocol differ from the current project.
No clinical validation or state-of-the-art claim is made.
''')
summary=f"""Run: {RUN}
Checkpoint: {R['checkpoint']}
Checkpoint SHA256: {R['checkpoint_sha256']}
Evaluation: Colab CLI --auth oauth2 exec -f ppt_artifacts/evaluate_authoritative_run.py
Test recordings: {', '.join(R['test_subjects'])}
Test epochs: {R['raw_metrics']['test_epochs']}
Raw results: {json.dumps(R['raw_metrics'],indent=2)}
Soft-Viterbi results: {json.dumps(R['smoothed_metrics'],indent=2)}
Input corrections: {json.dumps(R['input_repairs'],indent=2)}
Limitations: {'; '.join(R['limitations'])}
"""
(ROOT.parent/'sleep_stage_verified_results.txt').write_text(summary)
print('Generated plots, equations, risk rules, cited literature and result text from',RUN)
