'use strict';
const fs=require('node:fs'),path=require('node:path'),crypto=require('node:crypto');
const runtime=require('./native-runtime.json');
const target=process.platform==='linux'&&runtime.targets[process.arch];
if(!target||process.versions.node!==target.node||process.versions.modules!==target.modules||process.versions.v8!==target.v8)throw Error('Compiled plugin requires Linux and its recorded Node/V8 ABI; install a matching package. No source fallback.');
const file=path.join(__dirname,target.file),raw=fs.readFileSync(file);
if(raw.length!==target.bytes||crypto.createHash('sha256').update(raw).digest('hex')!==target.sha256)throw Error('Compiled plugin integrity check failed');
require(file).load.call(module.exports,module.exports,require,module,__filename,__dirname);
