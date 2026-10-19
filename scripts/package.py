"""Build a reproducible, tools-only Aide ZIP without network dependencies."""
from pathlib import Path
import hashlib,json,subprocess,zipfile
root=Path(__file__).resolve().parents[1]
subprocess.run(['node','--test','tests/starlink.test.cjs'],cwd=root,check=True)
subprocess.run(['node','--check',str(root/'index.js')],check=True)
manifest=json.loads((root/'manifest.json').read_text())
assert manifest['id']=='starlink' and manifest['version']==json.loads((root/'package.json').read_text())['version']
assert 'workbench' not in manifest and (root/'index.js').stat().st_size<=262144
names=['docs/reviews/2026-10-19-light-index.md','docs/reviews/2026-10-19-light-index.json','manifest.json','index.js','README.md','CHANGELOG.md','docs/VERIFICATION.md','docs/reviews/2026-10-19-ai-acceptance.json','docs/reviews/2026-10-19-tools-only-acceptance.json','docs/PERFORMANCE.md','docs/reviews/2026-10-19-snapshot-performance.json','docs/reviews/2026-10-19-incremental-ai-acceptance.json']
out=root/'dist'/f'aide-pkg-StarLink-v{manifest["version"]}.zip';out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name in sorted(names):
        info=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
        z.writestr(info,(root/name).read_bytes())
with zipfile.ZipFile(out) as z:
    assert z.testzip() is None and set(z.namelist())==set(names)
    assert 'workbench' not in json.loads(z.read('manifest.json'))
    assert all(not name.endswith(('.html','.css')) for name in z.namelist())
out.with_suffix('.zip.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n')
print(out)
