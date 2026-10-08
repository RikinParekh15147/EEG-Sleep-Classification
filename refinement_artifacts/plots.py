from pathlib import Path
import json,csv
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
D=Path('/content/eeg_refinement_audit') if Path('/content/eeg_refinement_audit').exists() else Path(__file__).resolve().parent/'verified'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':14,'axes.titlesize':19,'axes.labelsize':15})
stages=['Wake','N1','N2','N3','REM']
def rows(name):
    with (D/name).open(encoding='utf8') as f:return list(csv.DictReader(f))
for source,prefix in [('raw',''),('refined','refined_')]:
    cm=np.array([[int(r[s]) for s in stages] for r in rows(prefix+'confusion_matrix_counts.csv')]);fig,ax=plt.subplots(figsize=(10,5.6));ax.imshow(cm,cmap='Blues')
    ax.set_xticks(range(5),stages);ax.set_yticks(range(5),stages);ax.set_xlabel('Predicted stage');ax.set_ylabel('True stage');ax.set_title(('Original Transformer' if source=='raw' else 'Transformer + N1/N2 spectral refinement')+' · 3,109 epochs')
    for i in range(5):
        for j in range(5):ax.text(j,i,str(cm[i,j]),ha='center',va='center',color='white' if cm[i,j]>cm.max()*.5 else '#102E49')
    fig.tight_layout();fig.savefig(D/(source+'_confusion_matrix.png'),dpi=180,bbox_inches='tight');plt.close(fig)
metrics=json.loads((D/'overall_metrics.json').read_text());reports=[{r['stage']:float(r['f1-score']) for r in rows(p+'classification_report.csv')} for p in ['','refined_']]
values=[['Accuracy','Macro F1','N1 F1','N2 F1'],[metrics['raw']['accuracy'],metrics['raw']['macro_f1'],reports[0]['N1'],reports[0]['N2']],[metrics['refined']['accuracy'],metrics['refined']['macro_f1'],reports[1]['N1'],reports[1]['N2']]]
fig,ax=plt.subplots(figsize=(12,5.5));x=np.arange(4)
for offset,v,label,color in [(-.18,values[1],'Original Transformer','#102E49'),(.18,values[2],'N1/N2 refined','#18A69B')]:
    bars=ax.bar(x+offset,np.array(v)*100,.34,label=label,color=color);ax.bar_label(bars,labels=[f'{a*100:.2f}%' for a in v],padding=6,fontsize=13)
ax.set_xticks(x,values[0]);ax.set_ylim(0,80);ax.set_ylabel('Percent');ax.legend(loc='upper left');ax.spines[['top','right']].set_visible(False);fig.tight_layout();fig.savefig(D/'performance_comparison.png',dpi=180,bbox_inches='tight');plt.close(fig)
pred=rows('test_epoch_predictions.csv')
for sid in dict.fromkeys(r['subject_id'] for r in pred):
    sub=[r for r in pred if r['subject_id']==sid];fig,axes=plt.subplots(3,1,figsize=(13,5.4),sharex=True)
    for ax,col,label,color in zip(axes,['true_label','raw_prediction','refined_prediction'],['Ground truth','Original Transformer','N1/N2 refined'],['#526977','#102E49','#18A69B']):
        ax.step([int(r['epoch_index'])/120 for r in sub],[int(r[col]) for r in sub],where='post',color=color,linewidth=1.1);ax.set_yticks(range(5),stages);ax.invert_yaxis();ax.set_title(label,loc='left',fontsize=13);ax.grid(axis='y',alpha=.15)
    axes[-1].set_xlabel('Evaluated sequence time (hours; continuity assumed)');fig.suptitle(sid+(' · 95-minute segment' if sid=='SN001' else ' · stored notebook sequence'),fontsize=18);fig.tight_layout();fig.savefig(D/('hypnogram_'+sid+'.png'),dpi=180,bbox_inches='tight');plt.close(fig)
print('Generated current confusion matrices, comparison chart, and all four hypnograms.')
if str(D).startswith('/content/'):
    import zipfile
    with zipfile.ZipFile('/content/eeg_refinement_audit.zip','w',zipfile.ZIP_DEFLATED) as z:
        for p in D.iterdir():z.write(p,p.name)
