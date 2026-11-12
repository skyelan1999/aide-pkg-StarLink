"""Regenerate the pinned Unicode default full case-fold table in index.js."""
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT=Path(__file__).resolve().parents[1]
raw=(ROOT/'unicode/CaseFolding-17.0.0.txt').read_bytes()
if hashlib.sha256(raw).hexdigest()!='ff8d8fefbf123574205085d6714c36149eb946d717a0c585c27f0f4ef58c4183':
    raise ValueError('Unicode 17.0 CaseFolding source digest changed')
table={}
for line in raw.decode().splitlines():
    fields=line.split('#')[0].split(';')
    if len(fields)>2 and fields[1].strip() in ('C','F'):
        table[chr(int(fields[0].strip(),16))]=''.join(chr(int(c,16)) for c in fields[2].split())
path=ROOT/'index.js'
source=path.read_text()
pattern=r'^const CASE_FOLD=.*;$'
if len(re.findall(pattern,source,re.M))!=1:
    raise ValueError('Case-fold table marker is ambiguous')
replacement='const CASE_FOLD='+json.dumps(table,ensure_ascii=True,separators=(',',':'))+';'
updated=re.sub(pattern,lambda _:replacement,source,flags=re.M)
if '--check' in sys.argv:
    if source!=updated:raise ValueError('Embedded Unicode case-fold table differs from pinned source')
else:path.write_text(updated)
print('Verified Unicode 17.0 full mappings:',len(table))
