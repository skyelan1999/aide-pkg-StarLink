"""Test the final extracted compiled entry using the original behavior tests."""
import argparse,hashlib,json,pathlib,shutil,stat,subprocess,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def expected_members(name):
 expected={'index.js','manifest.json','native-runtime.json','licenses/NODE-LICENSE','BINARY-DISTRIBUTION.md','bin/linux-arm64/plugin.node','bin/linux-amd64/plugin.node'}
 for file in ['README.md','LICENSE','capabilities.json','classes.json','workbench.html']:
  if (ROOT/file).is_file():expected.add(file)
 if name=='rf-toolbox':expected.add('workbench.html')
 if name=='pjplan':expected.update(p.relative_to(ROOT).as_posix() for p in (ROOT/'examples').glob('*.json'))
 if name=='testbench':
  expected.add('execution-node/build.json')
  expected.update('licenses/'+n for n in ['GO-LICENSE','Cython-LICENSE.txt','Cython-COPYING.txt','pyserial-LICENSE.txt'])
  for arch,abi in [('arm64','aarch64'),('amd64','x86_64')]:
   prefix='execution-node/linux-'+arch+'/'
   expected.update(prefix+'core/'+n+'.cpython-312-'+abi+'-linux-gnu.so' for n in ['engine','server','http_worker'])
   expected.update(prefix+n for n in ['testbench-node','manifest.json','workbench.html','requirements.txt'])
   for directory in ['examples','profiles']:
    expected.update(prefix+p.relative_to(ROOT).as_posix() for p in (ROOT/directory).rglob('*') if p.is_file() and p.suffix in ['.json','.yaml'])
   expected.update(prefix+'wheels/'+p.name for p in (ROOT/'.agent-state/execution-wheels'/arch).glob('*.whl'))
 return expected

def extract_fresh(archive,stage,name):
 if stage.is_symlink():raise ValueError('Unsafe verification stage')
 if stage.exists():shutil.rmtree(stage)
 stage.mkdir(parents=True)
 with zipfile.ZipFile(archive) as z:
  names=z.namelist()
  if len(names)!=len(set(names)) or set(names)!=expected_members(name):raise ValueError('Archive allowlist mismatch')
  if z.testzip():raise ValueError('Corrupt ZIP')
  for member in z.infolist():
   path=pathlib.PurePosixPath(member.filename)
   if path.is_absolute() or '..' in path.parts or '\\' in member.filename or not stat.S_ISREG(member.external_attr>>16):raise ValueError('Unsafe ZIP entry')
   if path.suffix in ['.py','.pyc','.c','.cc','.h','.map'] or (path.suffix in ['.js','.cjs','.mjs'] and member.filename!='index.js'):raise ValueError('Business source fallback in archive')
  if z.read('index.js')!=(ROOT/'native/loader.cjs').read_bytes():raise ValueError('Archive loader differs from reviewed native adapter')
  z.extractall(stage)

def main():
 p=argparse.ArgumentParser();p.add_argument('--host-script',type=pathlib.Path,required=True);a=p.parse_args()
 manifest=json.loads((ROOT/'manifest.json').read_text());name=manifest['id'];archive=ROOT/'dist'/f'aide-pkg-{name}-v{manifest["version"]}-compiled-linux-universal.zip';state=ROOT/'.agent-state/native-module-20261022';stage=state/'verified-extracted'
 extract_fresh(archive,stage,name)
 if name=='feishu':shutil.copyfile(ROOT/'test.js',stage/'test.js');tests=['test.js']
 elif name=='auto-ai-model-router':shutil.copytree(ROOT/'test',stage/'test',dirs_exist_ok=True);tests=['--test']+[str(x.relative_to(stage)) for x in (stage/'test').glob('*.test.cjs')]
 elif name=='starlink':shutil.copytree(ROOT/'tests',stage/'tests',dirs_exist_ok=True);tests=['--test','tests/starlink.test.cjs']
 else:shutil.copytree(ROOT/'tests',stage/'tests',dirs_exist_ok=True);tests=['--test','tests/plugin.test.cjs']
 shutil.copyfile(a.host_script,stage/'host.cjs');results=[]
 for arch in ['arm64','amd64']:
  image='aide:local-pp-planning-20261021' if arch=='arm64' else 'aide:public-deps-20261021-amd64'
  prefix=['docker','run','--rm','--network','none','--platform','linux/'+arch,'--memory','512m','--cpus','1','--cap-drop','ALL','--security-opt','no-new-privileges','--mount',f'type=bind,src={stage},dst=/plugin,readonly','--workdir','/plugin','--entrypoint','node',image]
  for kind,args in [('behavior',tests),('host-load',['-e',"const fs=require('fs');eval(fs.readFileSync('/plugin/host.cjs','utf8'))",'validate','/plugin/index.js'])]:
   run=subprocess.run(prefix+args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);(state/f'{kind}-{arch}.log').write_text(run.stdout)
   if run.returncode:raise RuntimeError(run.stdout[-2000:])
   if kind=='host-load' and not json.loads(run.stdout).get('ok'):raise RuntimeError(run.stdout)
   results.append({'arch':arch,'mode':'native' if arch=='arm64' else 'emulated','check':kind,'exitCode':0})
 result={'status':'PASS','packageSHA256':hashlib.sha256(archive.read_bytes()).hexdigest(),'architectureTests':results,'realExternalServicesTested':False,'sourceEntryIncluded':False,'nodeVersion':'24.22.0','marketUpload':False}
 (state/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
if __name__=='__main__':main()
