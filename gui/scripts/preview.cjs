// Read-only browser preview of the real project artifacts. No Colab execution endpoint.
const http=require('node:http');const fs=require('node:fs');const path=require('node:path');const {Store,confined}=require('../electron/store.cjs');
const root=path.resolve(__dirname,'..'),store=new Store(path.dirname(root),path.join(root,'.runtime/preview'));
const types={'.html':'text/html','.js':'text/javascript','.css':'text/css','.json':'application/json','.png':'image/png','.jpg':'image/jpeg','.svg':'image/svg+xml'};
const server=http.createServer((request,response)=>{
 try {if(request.method!=='GET')throw new Error('Read-only preview');const url=new URL(request.url,'http://127.0.0.1');let value;
  if(url.pathname==='/api/bootstrap')value={...store.bootstrap(),desktop:false,connection:{state:'offline',message:'Browser preview · connect and run from the desktop app.'},logs:[],imports:[]};
  else if(url.pathname==='/api/run')value=store.run(url.searchParams.get('id')||'baseline');
  else if(url.pathname==='/api/runs')value=store.runs();
  else if(url.pathname==='/api/artifacts')value=store.artifacts(url.searchParams.get('id')||'baseline');
  else if(url.pathname==='/api/artifactText')value=store.artifactText(url.searchParams.get('id')||'baseline',url.searchParams.get('file'));
  if(value!==undefined){response.writeHead(200,{'Content-Type':'application/json'});response.end(JSON.stringify(value));return;}
  let file;if(url.pathname.startsWith('/artifact/')){const [id,...parts]=url.pathname.slice(10).split('/').map(decodeURIComponent);file=store.artifactFile(id,parts.join('/'));}
  else file=confined(path.join(root,'dist'),decodeURIComponent(url.pathname.slice(1)||'index.html'));
  response.writeHead(200,{'Content-Type':types[path.extname(file)]||'application/octet-stream'});fs.createReadStream(file).on('error',()=>response.destroy()).pipe(response);
 }catch(e){response.writeHead(400,{'Content-Type':'application/json'});response.end(JSON.stringify({error:e.message}));}
});server.listen(Number(process.env.PORT||4173),'127.0.0.1',()=>console.log('Read-only Sleep Studio preview: http://127.0.0.1:'+server.address().port));
