"""Deterministic source-free entry packaging. Browser assets remain visible."""
import hashlib,json,pathlib,struct,zipfile
ROOT=pathlib.Path(__file__).resolve().parents[1]
def sha(raw):return hashlib.sha256(raw).hexdigest()
def main():
 manifest=json.loads((ROOT/'manifest.json').read_text());files={};targets={}
 for arch,machine in [('arm64',183),('amd64',62)]:
  state=ROOT/'.agent-state/native-module-20261022'/arch;meta=json.loads((state/'artifact.json').read_text());raw=(state/'plugin.node').read_bytes()
  if meta['sourceSHA256']!=sha((ROOT/'index.js').read_bytes()) or meta['adapterSHA256']!=sha((ROOT/'native/addon.cc').read_bytes()):raise ValueError('Stale compilation')
  if sha(raw)!=meta['sha256'] or raw[:4]!=b'\x7fELF' or struct.unpack_from('<H',raw,18)[0]!=machine:raise ValueError('Invalid ELF')
  name=f'bin/linux-{arch}/plugin.node';files[name]=raw;targets['arm64' if arch=='arm64' else 'x64']={'file':name,**{k:meta[k] for k in ['node','modules','v8','sha256','bytes']}}
 files['native-runtime.json']=(json.dumps({'schemaVersion':1,'targets':targets},indent=2)+'\n').encode()
 files['index.js']=(ROOT/'native/loader.cjs').read_bytes()
 for name in ['manifest.json','README.md','LICENSE','capabilities.json','workbench.html']:
  if (ROOT/name).exists():files[name]=(ROOT/name).read_bytes()
 files['licenses/NODE-LICENSE']=(ROOT/'native/NODE-LICENSE').read_bytes()
 files['BINARY-DISTRIBUTION.md']=(ROOT/'docs/BINARY-DISTRIBUTION.md').read_bytes()
 out=ROOT/'dist'/f'aide-pkg-{manifest["id"]}-v{manifest["version"]}-compiled-linux-universal.zip';out.parent.mkdir(exist_ok=True)
 if sum(map(len,files.values()))>64<<20:raise ValueError('Expanded package limit exceeded')
 with zipfile.ZipFile(out,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for name,raw in sorted(files.items()):
   info=zipfile.ZipInfo(name,(2026,10,22,0,0,0));info.create_system=3;info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED;z.writestr(info,raw)
 if out.stat().st_size>24<<20:raise ValueError('ZIP package limit exceeded')
 receipt={'path':str(out),'sha256':sha(out.read_bytes()),'bytes':out.stat().st_size,'members':sorted(files),'targets':targets,'marketUpload':False}
 out.with_suffix('.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt))
if __name__=='__main__':main()
