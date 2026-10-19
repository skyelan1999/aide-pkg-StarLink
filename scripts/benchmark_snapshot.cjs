'use strict';
// Run in the Aide container. Replay ONE captured snapshot over loopback HTTPS;
// compare the real Aide one-shot host against its persistent JSON-RPC host.
// No model calls, source edits, index-policy changes or public listeners.
const fs=require('node:fs'),os=require('node:os'),path=require('node:path'),https=require('node:https'),readline=require('node:readline');
const {spawn}=require('node:child_process');const assert=require('node:assert/strict');
const options={};for(let i=2;i<process.argv.length;i+=2)options[process.argv[i].replace(/^--/,'')]=process.argv[i+1];
const rounds=Number(options.rounds||9),port=Number(options.port||19483);
if(!options.legacy||!options.plugin||!options.host||!options.output||rounds<3||rounds>30)throw Error('Usage: --legacy old-index.js --plugin new-index.js --host plugin_host.js --output report.json [--rounds 9]');
const token=fs.readFileSync('/data/auth/access-token','utf8').trim(),ca=fs.readFileSync('/data/certs/cert.pem'),key=fs.readFileSync('/data/certs/key.pem');
function live(route){return new Promise((resolve,reject)=>{https.get({hostname:'127.0.0.1',servername:'localhost',port:8080,path:route,ca,headers:{Authorization:'Bearer '+token}},res=>{const chunks=[];let bytes=0;res.on('data',b=>{bytes+=b.length;if(bytes>96*1024*1024){res.destroy();reject(Error('snapshot limit'));}else chunks.push(b);});res.on('end',()=>{if(res.statusCode!==200)return reject(Error('HTTP '+res.statusCode));try{resolve(JSON.parse(Buffer.concat(chunks)));}catch(e){reject(e);}});res.on('error',reject);}).on('error',reject);});}
function canonical(value){if(Array.isArray(value))return value.map(canonical);if(value&&typeof value==='object'){const out={};for(const k of Object.keys(value).sort())if(k!=='fetchedAt')out[k]=canonical(value[k]);return out;}return value;}
const percentile=(a,p)=>a.slice().sort((x,y)=>x-y)[Math.min(a.length-1,Math.ceil(a.length*p)-1)];
(async()=>{
 const lock=await live('/api/lock-state'),identity=await live('/api/knowledge-map/identity?code=1'),config=await live('/api/config'),workspace=await live('/api/workspace-config'),graph=await live('/api/knowledge-map/updates?code=1');
 const after=await live('/api/knowledge-map/identity?code=1');assert.deepEqual(identity,after);assert.equal(graph.workspace,identity.workspace);assert.equal(lock.locked,false);assert.equal(graph.reset,true);
 const w=workspace.workspace;assert.equal(w.mode,'local');let root=w.path||'/workspace';
 if(!['/workspace','/context','/local'].some(x=>root===x||root.startsWith(x+'/')))root=path.isAbsolute(root)?path.join('/local',path.relative(config.hostLocal,root)):path.resolve('/workspace',root);
 root=fs.realpathSync(root);
 const payloads=new Map([['/api/lock-state',lock],['/api/config',config],['/api/workspace-config',workspace],['/api/knowledge-map/identity?code=1',identity]]);
 const full=Buffer.from(JSON.stringify(graph)),delta=Buffer.from(JSON.stringify({...graph,reset:false,nodes:[],edges:[],removedNodes:[],removedEdges:[]}));
 const counts={requests:0,bytes:0,full:0,delta:0};
 const server=https.createServer({cert:ca,key},(req,res)=>{
  if(req.headers.authorization!=='Bearer '+token){res.writeHead(401);return res.end();}
  let body;if(req.url==='/api/knowledge-map/updates?code=1'){body=full;counts.full++;}
  else if(req.url==='/api/knowledge-map/updates?code=1&cursor='+graph.revision){body=delta;counts.delta++;}
  else if(payloads.has(req.url))body=Buffer.from(JSON.stringify(payloads.get(req.url)));
  else{res.writeHead(404);return res.end();}
  counts.requests++;counts.bytes+=body.length;res.setHeader('content-type','application/json');res.end(body);
 });
 await new Promise((resolve,reject)=>{server.once('error',reject);server.listen(port,'127.0.0.1',resolve);});
 const directory=fs.mkdtempSync(path.join(os.tmpdir(),'starlink-query-bench-')),legacyRoot=path.join(directory,'legacy'),pluginDirectory=path.join(legacyRoot,'starlink');fs.mkdirSync(pluginDirectory,{recursive:true});
 fs.copyFileSync(options.legacy,path.join(pluginDirectory,'index.js'));fs.writeFileSync(path.join(pluginDirectory,'manifest.json'),JSON.stringify({id:'starlink',main:'index.js',version:'0.1.1'}));
 const host=fs.readFileSync(options.host,'utf8');let sequence=0,daemon;
 const old=async(tool,args)=>{const output=path.join(directory,'result-'+(++sequence)+'.json');await new Promise((resolve,reject)=>{const child=spawn(process.execPath,['-e',host,'call',legacyRoot,JSON.stringify({plugin:'starlink',tool,args,settings:{port},workspace:root}),output],{stdio:['ignore','ignore','pipe']});let error='';child.stderr.on('data',b=>error+=b);child.on('error',reject);child.on('exit',code=>code===0?resolve():reject(Error('legacy host failed '+code+' '+error.slice(0,200))));});const value=JSON.parse(fs.readFileSync(output));fs.unlinkSync(output);if(!value.ok)throw Error(value.error);return value.result;};
 const sample=graph.nodes.find(n=>n.name==='workflow.go')||graph.nodes.find(n=>graph.edges.some(e=>e.from===n.id||e.to===n.id));assert.ok(sample);
 const edge=graph.edges.find(e=>e.from===sample.id||e.to===sample.id),neighbor=edge.from===sample.id?edge.to:edge.from;
 const queries=[['starlink_status',{code:true}],['starlink_summary',{code:true}],['starlink_search',{query:'workflow',limit:3,code:true}],['starlink_node',{id:sample.id,limit:20,code:true}],['starlink_path',{from:sample.id,to:neighbor,undirected:true,includeStructure:true,code:true}]];
 const searchQueries=['workflow','插件','工作区','notfound-xyz','starlink','API','source','node','引用'];
 const variant=(tool,args,i)=>tool==='starlink_search'?{...args,query:searchQueries[i%searchQueries.length]}:args;
 const queryKey=(tool,args)=>tool+' '+JSON.stringify(args);
 const timings={},expected=new Map();let readyResolve,readyReject;const ready=new Promise((a,b)=>{readyResolve=a;readyReject=b;}),pending=new Map();let ipc=0;
 try{
  for(const [tool,args] of queries){timings[tool]={legacy:[],fast:[]};for(let i=0;i<rounds;i++){const input=variant(tool,args,i),id=queryKey(tool,input),start=performance.now(),value=await old(tool,input);timings[tool].legacy.push(performance.now()-start);const normalized=canonical(value);if(!expected.has(id))expected.set(id,normalized);else assert.deepEqual(normalized,expected.get(id));}}
  const legacyTransport={...counts};for(const k of Object.keys(counts))counts[k]=0;
  const started=performance.now();daemon=spawn(process.execPath,['-e',host,'daemon',path.resolve(options.plugin)],{env:{...process.env,AIDE_PLUGIN_SETTINGS:JSON.stringify({port})},stdio:['pipe','pipe','pipe']});
  daemon.on('error',readyReject);daemon.on('exit',code=>{const error=Error('daemon exited '+code);readyReject(error);for(const p of pending.values())p.reject(error);pending.clear();});
  const rl=readline.createInterface({input:daemon.stdout});rl.on('line',line=>{const m=JSON.parse(line);if(m.params?.subtype==='ready')readyResolve();const p=pending.get(m.id);if(p){pending.delete(m.id);m.error?p.reject(Error(m.error.message)):p.resolve(m.result);}});
  await ready;const startupMs=performance.now()-started;
  const fast=(tool,args)=>new Promise((resolve,reject)=>{const id=++ipc;pending.set(id,{resolve,reject});daemon.stdin.write(JSON.stringify({jsonrpc:'2.0',id,method:'tool.call',params:{tool,args,workspace:root}})+'\n');});
  let firstSnapshotMs;
  for(const [tool,args] of queries){const coldStart=performance.now(),warmup=await fast(tool,args);if(tool==='starlink_summary')firstSnapshotMs=performance.now()-coldStart;assert.deepEqual(canonical(warmup),expected.get(queryKey(tool,args)));for(let i=0;i<rounds;i++){const input=variant(tool,args,i),start=performance.now(),value=await fast(tool,input);timings[tool].fast.push(performance.now()-start);assert.deepEqual(canonical(value),expected.get(queryKey(tool,input)));}}
  const result={sourceHashes:{legacy:require('node:crypto').createHash('sha256').update(fs.readFileSync(options.legacy)).digest('hex'),candidate:require('node:crypto').createHash('sha256').update(fs.readFileSync(options.plugin)).digest('hex'),host:require('node:crypto').createHash('sha256').update(host).digest('hex')},method:'one fixed real snapshot over verified loopback HTTPS, actual Aide one-shot vs daemon host; excludes model/network-to-provider and Go admission',rounds,searchQueries,scale:{nodes:graph.nodes.length,edges:graph.edges.length,revision:graph.revision,fullBytes:full.length,deltaBytes:delta.length,partial:graph.truncated,stale:!!graph.stale},cold:{startupMs,firstSnapshotMs},transport:{legacyCalls:rounds*queries.length,fastCalls:(rounds+1)*queries.length,excludedFastWarmups:queries.length,legacy:legacyTransport,fast:{...counts}},tools:{}};
  for(const [name,values] of Object.entries(timings)){const before=percentile(values.legacy,.5),after=percentile(values.fast,.5);result.tools[name]={legacySamplesMs:values.legacy,fastSamplesMs:values.fast,legacyP50ms:before,fastP50ms:after,speedup:before/after,legacyP95ms:percentile(values.legacy,.95),fastP95ms:percentile(values.fast,.95)};}
  result.allResultsEqual=true;result.targetReached=['starlink_summary','starlink_search','starlink_node','starlink_path'].every(x=>result.tools[x].speedup>=10);
  fs.writeFileSync(options.output,JSON.stringify(result,null,2)+'\n',{mode:0o600});console.log(JSON.stringify(result,null,2));if(!result.targetReached)process.exitCode=2;
 }finally{if(daemon){daemon.stdin.end();await new Promise(resolve=>daemon.once('exit',resolve));}server.closeAllConnections?.();await new Promise(resolve=>server.close(resolve));fs.rmSync(directory,{recursive:true,force:true});}
})().catch(e=>{console.error(e.message);process.exitCode=1;});
