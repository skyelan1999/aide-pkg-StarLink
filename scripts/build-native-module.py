"""Build a Node/V8 compiled ELF addon for the unchanged plugin CommonJS entry.
The original license is preserved. Runtime must match the recorded Node/V8 ABI.
"""
import argparse, hashlib, json, pathlib, shutil, subprocess, tarfile, urllib.request, zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
VERSION='24.22.0'
HEADERS_SHA='00e9f08b9057f9f5428387a5ffd496e53f274565b40b144b7ba876700755352a'
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--arch',choices=['arm64','amd64'],required=True);p.add_argument('--image');p.add_argument('--sdk-cache',type=pathlib.Path);a=p.parse_args()
 state=ROOT/'.agent-state/native-module-20261022'/a.arch;state.mkdir(parents=True,exist_ok=True)
 cache=a.sdk_cache or ROOT/'.agent-state/node-sdk';cache.mkdir(parents=True,exist_ok=True)
 archive=cache/'node-headers.tar.gz'
 if not archive.exists():urllib.request.urlretrieve(f'https://nodejs.org/dist/v{VERSION}/node-v{VERSION}-headers.tar.gz',archive)
 if digest(archive)!=HEADERS_SHA:raise ValueError('Node SDK SHA-256 mismatch')
 sdk=state/f'node-v{VERSION}'
 if not sdk.exists():
  with tarfile.open(archive) as t:
   for member in t.getmembers():
    target=(state/member.name).resolve()
    if state.resolve() not in target.parents or not (member.isfile() or member.isdir()):raise ValueError('Unsafe SDK member')
   t.extractall(state)
 for name in ('index.js','native/addon.cc'):shutil.copyfile(ROOT/name,state/('source.js' if name=='index.js' else 'addon.cc'))
 inputs={'index.js':digest(state/'source.js'),'native/addon.cc':digest(state/'addon.cc')}
 compile_js="""const fs=require('fs'),vm=require('vm'),Module=require('module');const s=Module.wrap(fs.readFileSync('source.js','utf8'));const b=new vm.Script(s).createCachedData();fs.writeFileSync('payload.h','static const unsigned char payload[]={'+Array.from(b).join(',')+'};\\nstatic const int payload_size='+b.length+';\\nstatic const int payload_source_length='+s.length+';\\n');fs.writeFileSync('abi.json',JSON.stringify({node:process.versions.node,modules:process.versions.modules,v8:process.versions.v8,architecture:process.arch}));"""
 (state/'compile.cjs').write_text(compile_js)
 image=a.image or ('aide:local-pp-planning-20261021' if a.arch=='arm64' else 'aide:public-deps-20261021-amd64')
 command=f'node --no-lazy compile.cjs && g++ -shared -fPIC -std=c++20 -O2 -s -DNODE_GYP_MODULE_NAME=compiled_plugin -I node-v{VERSION}/include/node addon.cc -o plugin.node'
 subprocess.run(['docker','run','--rm','--network','none','--platform','linux/'+a.arch,'--memory','512m','--cpus','1','--mount',f'type=bind,src={state},dst=/build','--workdir','/build','--entrypoint','sh',image,'-c',command],check=True)
 abi=json.loads((state/'abi.json').read_text())
 if abi['node']!=VERSION:raise ValueError('Build image Node version differs from pinned SDK')
 if any(digest(ROOT/name)!=value for name,value in inputs.items()):raise ValueError('Source inputs changed during compilation; rebuild required')
 result={'schemaVersion':1,'format':'ELF V8 compiled CommonJS module','sourceSHA256':inputs['index.js'],'adapterSHA256':inputs['native/addon.cc'],'inputs':inputs,'headersSHA256':HEADERS_SHA,'sha256':digest(state/'plugin.node'),'bytes':(state/'plugin.node').stat().st_size,**abi}
 (state/'artifact.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
