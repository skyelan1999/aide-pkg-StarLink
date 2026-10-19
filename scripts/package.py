"""Build a self-contained Aide plugin ZIP; no downloads or package dependencies."""
from pathlib import Path
import hashlib,json,subprocess,zipfile
root=Path(__file__).resolve().parents[1]
subprocess.run(['node','--test','tests/starlink.test.cjs'],cwd=root,check=True)
for name in ['index.js','web/app.js','scripts/workbench-client.js']:
    subprocess.run(['node','--check',str(root/name)],check=True)
manifest=json.loads((root/'manifest.json').read_text())
assert manifest['id']=='starlink' and manifest['version']==json.loads((root/'package.json').read_text())['version']
assert (root/'index.js').stat().st_size<=262144
page=(root/'web/workbench.template.html').read_text().replace('/*__BRIDGE__*/',(root/'scripts/workbench-client.js').read_text()).replace('/*__APP__*/',(root/'web/app.js').read_text())
assert '</script' not in (root/'web/app.js').read_text().lower()
(root/'workbench.html').write_text(page)
out=root/'dist'/f'aide-pkg-StarLink-v{manifest["version"]}.zip';out.parent.mkdir(exist_ok=True)
with zipfile.ZipFile(out,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name in ['manifest.json','index.js','workbench.html','README.md','CHANGELOG.md','docs/VERIFICATION.md']:
        info=zipfile.ZipInfo(name,date_time=(2026,10,19,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16
        z.writestr(info,(root/name).read_bytes())
with zipfile.ZipFile(out) as z: assert z.testzip() is None
out.with_suffix('.zip.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n')
print(out)
