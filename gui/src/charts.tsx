import {useState} from 'react';
import type {Row,SignalData} from './types';
export const STAGES=['Wake','N1','N2','N3','REM'];
export const COLORS=['#efb17a','#a3a6f6','#71b7eb','#6fdbbd','#df8fc1'];
export const numeric=(x:unknown)=>typeof x==='number'?x:Number(x)||0;
export const pct=(x:unknown,digits=1)=>x===null||x===undefined?'—':(numeric(x)*100).toFixed(digits)+'%';
export const fmt=(x:unknown,digits=1)=>x===null||x===undefined?'—':numeric(x).toLocaleString(undefined,{maximumFractionDigits:digits});
export const bytes=(n:number)=>n<1024?`${n} B`:n<1024**2?`${(n/1024).toFixed(1)} KB`:`${(n/1024**2).toFixed(1)} MB`;
export function Legend(){return <div className="legend">{STAGES.map((stage,i)=><span key={stage}><i style={{background:COLORS[i]}}/>{stage}</span>)}</div>}
export function Spark({values,color='#6fdbbd'}:{values:number[];color?:string}){
 if(!values.length)return null;const min=Math.min(...values),max=Math.max(...values);const points=values.map((v,i)=>`${i/Math.max(1,values.length-1)*140},${36-(v-min)/Math.max(.001,max-min)*28}`).join(' ');
 return <svg viewBox="0 0 140 40" className="spark" aria-hidden="true"><polyline points={points} fill="none" stroke={color} strokeWidth="2"/></svg>
}
export function Hypnogram({rows,selected=0,onSelect,compact=false}:{rows:Row[];selected?:number;onSelect?:(index:number)=>void;compact?:boolean}){
 const [show,setShow]=useState({raw:false,smoothed:true,truth:true});
 if(!rows.length)return <div className="empty-chart">Predictions will appear here after a run.</div>;
 const left=58,right=960,top=20,bottom=compact?150:215,height=compact?188:260;
 const first=numeric(rows[0].timestamp_seconds),last=numeric(rows.at(-1)?.timestamp_seconds)+30,span=Math.max(30,last-first);
 const x=(time:number)=>left+(time-first)/span*(right-left),y=(stage:number)=>top+stage*(bottom-top)/4;
 const line=(key:string)=>{let d='';let previous:Row|undefined;for(const row of rows){if(row[key]===null||row[key]===undefined){previous=undefined;continue;}const a=x(numeric(row.timestamp_seconds)),b=y(numeric(row[key]));const gap=previous&&Math.abs(numeric(row.timestamp_seconds)-numeric(previous.timestamp_seconds)-30)>.01;d+=!previous||gap?` M${a},${b}`:` H${a} V${b}`;previous=row;}return d;};
 return <div><svg viewBox={`0 0 1000 ${height}`} className={`hypnogram ${onSelect?'interactive':''}`} role="img" aria-label="Sleep stage timeline" onClick={e=>{if(!onSelect)return;const rect=e.currentTarget.getBoundingClientRect();const time=first+Math.max(0,Math.min(1,((e.clientX-rect.left)/rect.width*1000-left)/(right-left)))*span;let nearest=0;for(let i=1;i<rows.length;i++)if(Math.abs(numeric(rows[i].timestamp_seconds)-time)<Math.abs(numeric(rows[nearest].timestamp_seconds)-time))nearest=i;onSelect(nearest);}}>
 {STAGES.map((stage,i)=><g key={stage}><line x1={left} y1={y(i)} x2={right} y2={y(i)} className="grid-line"/><text x={left-13} y={y(i)+4} textAnchor="end" className="chart-label">{stage}</text></g>)}
 {Array.from({length:7},(_,i)=><g key={i}><line x1={left+(right-left)*i/6} y1={top} x2={left+(right-left)*i/6} y2={bottom} className="grid-line vertical"/><text x={left+(right-left)*i/6} y={height-10} textAnchor="middle" className="chart-label">{((first+span*i/6)/3600).toFixed(1)}h</text></g>)}
 {show.truth&&rows.some(r=>r.true_label!==null)&&<path d={line('true_label')} fill="none" stroke="var(--text-dim)" strokeWidth="1.4" strokeDasharray="5 4" opacity=".5"/>}
 {show.raw&&<path d={line('raw_prediction')} fill="none" stroke="#a3a6f6" strokeWidth="1.5" opacity=".7"/>}
 {show.smoothed&&<path d={line(rows.some(r=>r.refined_prediction!=null)?'refined_prediction':'raw_prediction')} fill="none" stroke="#6fdbbd" strokeWidth="2.2" strokeLinejoin="round"/>}
 {onSelect&&rows[selected]&&<g><line x1={x(numeric(rows[selected].timestamp_seconds))} y1={top-8} x2={x(numeric(rows[selected].timestamp_seconds))} y2={bottom+8} stroke="var(--text)" strokeWidth="1" opacity=".7"/><circle cx={x(numeric(rows[selected].timestamp_seconds))} cy={y(numeric(rows[selected].refined_prediction??rows[selected].raw_prediction))} r="4" fill="#6fdbbd" stroke="var(--surface)" strokeWidth="2"/></g>}
 </svg>{!compact&&<div className="chart-toggles">{([['smoothed','N1/N2 refined / available prediction','#6fdbbd'],['raw','Raw prediction','#a3a6f6'],['truth','Ground truth','var(--text-dim)']] as const).map(([key,label,color])=><label key={key}><input type="checkbox" checked={show[key]} onChange={e=>setShow({...show,[key]:e.target.checked})}/><i style={{background:color}}/>{label}</label>)}<span>Click the timeline to inspect an epoch</span></div>}</div>
}
export function LineChart({series,labels,yPercent=false,aria='Line chart'}:{series:{name:string;values:(number|null)[];color:string}[];labels:string[];yPercent?:boolean;aria?:string}){
 const values=series.flatMap(s=>s.values.filter((v):v is number=>v!==null&&Number.isFinite(v)));if(!values.length)return <div className="empty-chart">No data available</div>;
 const min=yPercent?0:Math.min(0,...values),max=yPercent?1:Math.max(.001,...values)*1.1;const left=50,right=940,top=20,bottom=190;
 const x=(i:number)=>left+i/Math.max(1,labels.length-1)*(right-left),y=(v:number)=>bottom-(v-min)/(max-min)*(bottom-top);
 return <div><svg viewBox="0 0 1000 230" className="line-chart" role="img" aria-label={aria}>{Array.from({length:5},(_,i)=><g key={i}><line x1={left} x2={right} y1={top+(bottom-top)*i/4} y2={top+(bottom-top)*i/4} className="grid-line"/><text x={left-10} y={top+(bottom-top)*i/4+4} className="chart-label" textAnchor="end">{yPercent?((max-(max-min)*i/4)*100).toFixed(0)+'%':(max-(max-min)*i/4).toFixed(2)}</text></g>)}{labels.map((label,i)=>i%Math.max(1,Math.ceil(labels.length/7))===0?<text key={i} x={x(i)} y={218} className="chart-label" textAnchor="middle">{label}</text>:null)}{series.map(s=><path key={s.name} d={s.values.reduce((d,v,i)=>v===null?d:d+`${i===0||s.values[i-1]===null?'M':'L'}${x(i)},${y(v)} `,'')} fill="none" stroke={s.color} strokeWidth="2.5"/>)}</svg><div className="legend">{series.map(s=><span key={s.name}><i style={{background:s.color}}/>{s.name}</span>)}</div></div>
}
export function Confusion({rows,normalized=false}:{rows:Row[];normalized?:boolean}){
 if(!rows.length)return <div className="empty-chart">Aligned ground-truth labels are required.</div>;
 const max=Math.max(1,...rows.flatMap(r=>STAGES.map(n=>numeric(r[n]))));
 return <div className="confusion"><div className="axis-title">PREDICTED STAGE</div><div className="matrix-grid"><div/>{STAGES.map(n=><div className="matrix-label" key={n}>{n}</div>)}{rows.slice(0,5).flatMap((row,i)=>{const total=STAGES.reduce((s,n)=>s+numeric(row[n]),0);return [<div className="matrix-label row-label" key={'r'+i}>{STAGES[i]}</div>,...STAGES.map((n,j)=><div key={i+'-'+j} className="matrix-cell" style={{background:`rgba(111,219,189,${.04+(normalized?numeric(row[n])/Math.max(1,total):numeric(row[n])/max)*.78})`}}><strong>{normalized?pct(numeric(row[n])/Math.max(1,total),0):fmt(row[n],0)}</strong>{!normalized&&<span>{pct(numeric(row[n])/Math.max(1,total),0)}</span>}</div>)];})}</div><div className="matrix-foot">Rows: true stage · {normalized?'Row-normalized percentages':'Epoch counts and row percentages'}</div></div>
}
export function Distribution({counts,total,large=false,sleepOnly=false}:{counts:number[];total:number;large?:boolean;sleepOnly?:boolean}){
 if(sleepOnly)counts=[0,...counts.slice(1)];const circumference=2*Math.PI*72;let offset=0;
 return <div className={`distribution ${large?'large':''}`}><div className="donut"><svg viewBox="0 0 180 180" role="img" aria-label="Sleep stage distribution"><circle cx="90" cy="90" r="72" fill="none" stroke="var(--border)" strokeWidth="15"/>{counts.map((count,i)=>{const length=count/Math.max(1,total)*circumference;const start=offset;offset+=length;return <circle key={i} cx="90" cy="90" r="72" fill="none" stroke={COLORS[i]} strokeWidth="15" strokeDasharray={`${Math.max(0,length-2)} ${circumference}`} strokeDashoffset={-start} transform="rotate(-90 90 90)"/>;})}</svg><div className="donut-center"><strong>{fmt(total,0)}</strong><span>epochs</span></div></div><div className="distribution-list">{STAGES.map((n,i)=>sleepOnly&&i===0?null:<div key={n}><span><i style={{background:COLORS[i]}}/>{n}</span><strong>{pct(counts[i]/Math.max(1,total))}</strong><span>{fmt(counts[i]/2)} min</span></div>)}</div></div>
}
export function Waveform({signal,raw=false}:{signal:SignalData|null;raw?:boolean}){
 const arrays=raw?signal?.raw:signal?.processed;
 if(!arrays?.length)return <div className="empty-chart"><span>No EEG samples cached for this epoch.</span><small>The hypnogram and probabilities remain available. Load this epoch from Colab or inspect a saved preview.</small></div>;
 const height=arrays.length*100+40,width=1000;const sampleHz=raw?signal?.raw_sampling_hz:signal?.processed_sampling_hz;
 return <svg viewBox={`0 0 ${width} ${height}`} className="waveform" role="img" aria-label={raw?'EEG waveform in microvolts':'Normalized EEG waveform'}>{arrays.map((values,channel)=>{const middle=35+channel*100,scale=Math.max(.00001,...values.map(Math.abs));return <g key={channel}><text x="12" y={middle-14} className="chart-label">{signal?.channels[channel]?.replace('EEG ','')}</text><line x1="135" x2="970" y1={middle} y2={middle} className="grid-line"/><polyline points={values.map((v,i)=>`${135+i/Math.max(1,values.length-1)*835},${middle-v/scale*32}`).join(' ')} fill="none" stroke={channel%2===0?'#6fdbbd':'#71b7eb'} strokeWidth="1"/><text x="970" y={middle-36} className="chart-label" textAnchor="end">±{fmt(scale,2)} {raw?signal?.raw_unit:signal?.processed_unit}</text></g>})}{[0,10,20,30].map(n=><text key={n} x={135+n/30*835} y={height-5} textAnchor="middle" className="chart-label">{n}s</text>)}<text x="12" y={height-5} className="chart-label">{fmt(sampleHz,1)} Hz preview</text></svg>
}
