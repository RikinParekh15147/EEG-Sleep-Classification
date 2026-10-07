const escape = value => String(value ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function table(rows,columns) { return `<table><thead><tr>${columns.map(c=>`<th>${escape(c)}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr>${columns.map(c=>`<td>${escape(typeof row[c]==='number'?Math.round(row[c]*10000)/10000:row[c])}</td>`).join('')}</tr>`).join('')}</tbody></table>`; }
function report(run) {
 const metrics=run.metrics || {}; const entries=['raw','soft_viterbi'].filter(x=>metrics[x]).map(condition=>({condition,...metrics[condition]}));
 return `<!doctype html><html><head><meta charset="utf-8"><title>Sleep Studio report</title><style>body{font:12px Arial,sans-serif;color:#162c30;margin:36px}h1{font-size:30px;color:#146b63}h2{margin-top:26px;font-size:17px}p{line-height:1.6}table{width:100%;border-collapse:collapse;margin:12px 0}th,td{text-align:left;border-bottom:1px solid #dae3e4;padding:8px;font-size:10px}th{background:#f1f6f5}.muted{color:#637779}pre{white-space:pre-wrap;overflow-wrap:anywhere;font-size:10px}.stage{display:inline-block;margin-right:12px;padding:5px;background:#edf5f3}</style></head><body>
 <p class="muted">SLEEP STUDIO / EEG ANALYSIS</p><h1>${escape(run.manifest.name||run.manifest.id)}</h1>
 <p>Run: ${escape(run.manifest.sourceRun||run.manifest.id)}<br>Created: ${escape(run.manifest.createdAt)}<br>Status: ${escape(run.manifest.status)}<br>Checkpoint SHA256: ${escape(run.result.checkpoint_sha256||run.manifest.checkpoint?.sha256||'Recorded in manifest')}</p>
 <h2>Classification performance</h2>${entries.length?table(entries,['condition','accuracy','balanced_accuracy','macro_f1','weighted_f1','cohen_kappa','test_epochs']):'<p>Ground-truth evaluation is unavailable for this run.</p>'}
 <h2>Sleep profiles</h2>${table(run.biomarkers,['subject_id','source','sleep_minutes','Sleep_Efficiency_Pct','WASO_Minutes','N3_Deep_Pct','SFI','risk_category'])}
 <p class="muted">Research profiles use evaluated-epoch duration, not verified time in bed. Rule thresholds have not been clinically validated. Stage uncertainty is not a calibrated diagnostic confidence score.</p>
 <h2>Configuration and provenance</h2><pre>${escape(JSON.stringify(run.manifest.settings||run.result,null,2))}</pre>
 <h2>Artifacts</h2>${table(run.artifacts,['path','bytes'])}</body></html>`;
}
module.exports={report,escape};
