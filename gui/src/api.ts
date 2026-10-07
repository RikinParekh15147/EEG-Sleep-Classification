import type { Api } from './types';
const unavailable=async()=>{throw new Error('This action is available in the desktop app. Launch it with npm start from Windows Terminal.');};
async function get<T>(route:string,params:Record<string,string>={}):Promise<T> {
 const response=await fetch('/api/'+route+'?'+new URLSearchParams(params));const value=await response.json();if(!response.ok)throw new Error(value.error||'Could not load project data');return value;
}
export const api:Api=window.sleep||{
 bootstrap:()=>get('bootstrap'),settings:async()=>(await get<any>('bootstrap')).settings,run:id=>get('run',{id}),runs:()=>get('runs'),artifacts:id=>get('artifacts',{id}),artifactText:(id,file)=>get('artifactText',{id,file}),
 saveSettings:unavailable,discover:unavailable,connect:unavailable,mountDrive:unavailable,prepareRuntime:unavailable,browseDrive:unavailable,startRun:unavailable,cancelRun:unavailable,recoverRun:unavailable,importFiles:unavailable,exportRun:unavailable,exportPdf:unavailable,openArtifact:unavailable,authReply:unavailable,signal:unavailable,
 openExternal:async(url)=>{const parsed=new URL(url);if(parsed.protocol!=='https:')throw new Error('Use an HTTPS URL');window.open(parsed.href,'_blank','noopener,noreferrer');},onEvent:()=>()=>{}
};
export const artifactUrl=(id:string,file:string)=>window.sleep?`sleep://artifact/${encodeURIComponent(id)}/${file.split('/').map(encodeURIComponent).join('/')}`:`/artifact/${encodeURIComponent(id)}/${file.split('/').map(encodeURIComponent).join('/')}`;
