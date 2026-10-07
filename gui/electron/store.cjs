const fs = require('node:fs');
const path = require('node:path');
const crypto = require('node:crypto');
const STAGES = ['Wake','N1','N2','N3','REM'];
function csv(text) {
  const rows = []; let row = [], value = '', quote = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (c === '"') { if (quote && text[i + 1] === '"') { value += '"'; i++; } else quote = !quote; }
    else if (c === ',' && !quote) { row.push(value); value = ''; }
    else if ((c === '\n' || c === '\r') && !quote) {
      if (c === '\r' && text[i + 1] === '\n') i++;
      row.push(value); if (row.some(x => x !== '')) rows.push(row); row = []; value = '';
    } else value += c;
  }
  if (value || row.length) { row.push(value); rows.push(row); }
  const headers = rows.shift() || [];
  return rows.map(values => Object.fromEntries(headers.map((h,i) => [h, scalar(values[i] ?? '')])));
}
function scalar(value) {
  if (value === '') return null;
  if (value === 'True' || value === 'true') return true;
  if (value === 'False' || value === 'false') return false;
  if (/^-?(?:\d+(?:\.\d*)?|\.\d+)(?:e[+-]?\d+)?$/i.test(value)) return Number(value);
  return value;
}
function safeId(id) { if (typeof id !== 'string' || !/^[A-Za-z0-9_-]{1,100}$/.test(id)) throw new Error('Invalid run ID'); return id; }
function inside(root, candidate) {
  const relative = path.relative(root, candidate);
  return relative === '' || (!relative.startsWith(`..${path.sep}`) && relative !== '..' && !path.isAbsolute(relative));
}
function confined(root, relative) {
  if (typeof relative !== 'string' || relative.includes('\0') || path.isAbsolute(relative)) throw new Error('Invalid artifact path');
  const full = path.resolve(root, relative);
  if (!inside(path.resolve(root), full)) throw new Error('Artifact path escapes the run');
  if (fs.existsSync(full) && !inside(fs.realpathSync(root), fs.realpathSync(full))) throw new Error('Artifact symlink escapes the run');
  return full;
}
function atomicJson(file, value) {
  fs.mkdirSync(path.dirname(file), { recursive: true });
  const temp = `${file}.${crypto.randomUUID()}.tmp`;
  fs.writeFileSync(temp, JSON.stringify(value, null, 2)); fs.renameSync(temp, file);
}
const defaults = {
  distro: 'Ubuntu', cliPath: '', session: 'eeg-sleep-studio', accelerator: 'T4',
  basePath: '/content/drive/MyDrive/Sleep_Health_Profiling',
  checkpointPath: '/content/drive/MyDrive/Sleep_Health_Profiling/models/HMC_CHECKPOINTS/best_objective1_model.keras',
  processedPath: '/content/drive/MyDrive/Sleep_Health_Profiling/processed/HMC_preprocessed',
  rawPath: '/content/drive/MyDrive/Sleep_Health_Profiling/Data/HMC',
  driveOutputs: '/content/drive/MyDrive/Sleep_Health_Profiling/gui_runs',
  persistDrive: true, theme: 'dark',
};
function validateSettings(input) {
  const output = {};
  for (const key of Object.keys(defaults)) {
    const value = input[key]; if (value === undefined) continue;
    if (typeof defaults[key] === 'boolean') { if (typeof value !== 'boolean') throw new Error(`Invalid ${key}`); }
    else if (typeof value !== 'string' || value.length > 1000 || /[\0\r\n]/.test(value)) throw new Error(`Invalid ${key}`);
    output[key] = value;
  }
  if (output.theme && !['dark','light'].includes(output.theme)) throw new Error('Invalid theme');
  if (output.accelerator && !['CPU','T4','L4','A100','H100','G4'].includes(output.accelerator)) throw new Error('Invalid accelerator');
  if (output.session && !/^[A-Za-z0-9_-]{1,60}$/.test(output.session)) throw new Error('Use letters, digits, underscores or hyphens for session names');
  for (const key of ['basePath','checkpointPath','processedPath','rawPath','driveOutputs']) {
    if (output[key] && (!output[key].startsWith('/content/') || output[key].split('/').includes('..'))) throw new Error(`${key} must be an absolute /content/ path`);
  }
  return output;
}
class Store {
  constructor(projectRoot, dataRoot) { this.projectRoot = projectRoot; this.dataRoot = dataRoot; this.baseline = path.join(projectRoot, 'ppt_artifacts'); this.runsRoot = path.join(dataRoot, 'runs'); }
  init() { fs.mkdirSync(this.runsRoot, { recursive: true }); }
  settings() { return { ...defaults, ...this.json(path.join(this.dataRoot, 'settings.json'), {}) }; }
  saveSettings(value) { const result = { ...this.settings(), ...validateSettings(value) }; atomicJson(path.join(this.dataRoot,'settings.json'),result); return result; }
  json(file, fallback = null) { try { return JSON.parse(fs.readFileSync(file,'utf8')); } catch (e) { if (e.code === 'ENOENT') return fallback; throw e; } }
  read(dir, name, fallback = null) { const file = confined(dir,name); if (!fs.existsSync(file)) return fallback; return name.endsWith('.csv') ? csv(fs.readFileSync(file,'utf8')) : this.json(file,fallback); }
  directory(id) { return id === 'baseline' ? this.baseline : path.join(this.runsRoot, safeId(id), 'artifacts'); }
  manifest(id) { return id === 'baseline' ? { id:'baseline', name:'Verified HMC evaluation', kind:'baseline',status:'completed',createdAt:'2026-10-07T07:22:00Z',sourceRun:'HMC-PPT-20261007-01',recordings:['SN009','SN001','SN004','SN022'],step:'Verified results',progress:100 } : this.json(path.join(this.runsRoot, safeId(id),'run.json')); }
  runs() {
    const entries = fs.existsSync(this.runsRoot) ? fs.readdirSync(this.runsRoot).filter(x => /^[A-Za-z0-9_-]+$/.test(x)).map(id => this.manifest(id)).filter(Boolean) : [];
    return [...entries.sort((a,b) => b.createdAt.localeCompare(a.createdAt)), ...(fs.existsSync(this.baseline) ? [this.manifest('baseline')] : [])];
  }
  saveRun(manifest) { safeId(manifest.id); atomicJson(path.join(this.runsRoot,manifest.id,'run.json'),manifest); return manifest; }
  run(id) {
    const manifest = this.manifest(id); if (!manifest) throw new Error('Run not found');
    const dir = this.directory(id);
    const result = this.read(dir, 'final_results.json', {});
    const metrics = this.read(dir,'overall_metrics.json',{});
    return { manifest, result, metrics, predictions: this.read(dir,'test_epoch_predictions.csv',[]),
      biomarkers:this.read(dir,'subject_biomarkers.csv',[]), rawReport:this.read(dir,'classification_report.csv',[]),
      smoothedReport:this.read(dir,'smoothed_classification_report.csv',[]),
      confusion:this.read(dir,'confusion_matrix_counts.csv',[]),smoothedConfusion:this.read(dir,'smoothed_confusion_matrix_counts.csv',[]),
      calibration:this.read(dir,'calibration_metrics.json',{}),calibrationBins:this.read(dir,'calibration_bins.csv',[]),
      riskCoverage:this.read(dir,'risk_coverage_data.csv',[]), training:this.read(dir,'training_history.csv',[]),
      signals:this.read(dir,'signals.json',{}), artifacts:this.artifacts(id) };
  }
  bootstrap() {
    return { settings:this.settings(), runs:this.runs(), baseline:fs.existsSync(this.baseline) ? this.run('baseline') : null,
      model:this.read(this.baseline,'hyperparameters.json',{}),layers:this.read(this.baseline,'model_layers.csv',[]),
      dataset:this.read(this.baseline,'split_summary.json',{}),recordings:this.read(this.baseline,'split_subjects.csv',[]),
      distributions:this.read(this.baseline,'stage_distribution.csv',[]),preprocessing:this.read(this.baseline,'preprocessing_config.json',{}),
      transition:this.read(this.baseline,'transition_config.json',{}),rules:this.read(this.baseline,'risk_rules.json',{}),
      exampleSignal:this.json(path.join(this.projectRoot,'gui/data/eeg-example.json'),null), stages:STAGES };
  }
  artifacts(id) {
    const root = this.directory(id); if (!fs.existsSync(root)) return [];
    const output = [];
    function walk(dir) {
      for (const entry of fs.readdirSync(dir,{withFileTypes:true})) {
        if (entry.isSymbolicLink()) continue;
        const file = path.join(dir,entry.name);
        if (entry.isDirectory()) { if (!['rendered_slides','original_render','corrected_test_inputs'].includes(entry.name)) walk(file); }
        else if (entry.isFile()) output.push({path:path.relative(root,file).split(path.sep).join('/'),bytes:fs.statSync(file).size,type:path.extname(file).slice(1).toLowerCase()});
      }
    }
    walk(root); return output.sort((a,b) => a.path.localeCompare(b.path));
  }
  artifactFile(id, relative) { const file=confined(this.directory(id),relative); if (!fs.statSync(file).isFile()) throw new Error('Not a file'); return file; }
  artifactText(id, relative) {
    const file=this.artifactFile(id,relative); if (!/\.(csv|json|txt|md|log)$/i.test(file)) throw new Error('This artifact is binary; export it to open it');
    if (fs.statSync(file).size > 2*1024*1024) throw new Error('This file is too large to preview; export it');
    return fs.readFileSync(file,'utf8');
  }
}
module.exports = { Store, csv, confined, inside, atomicJson, validateSettings, STAGES, defaults };
