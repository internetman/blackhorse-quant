const vm=require('node:vm'),fs=require('node:fs'),assert=require('node:assert/strict');
const contents=fs.readFileSync('m2-archive.js','utf8');
const values=new Map(), listeners={};
const window={localStorage:{getItem:k=>values.get(k)||null,setItem:(k,v)=>values.set(k,v)},addEventListener:(k,f)=>listeners[k]=f,removeEventListener(){},dispatchEvent:e=>listeners[e.type]?.(e)};
vm.runInNewContext(contents,{window,console,CustomEvent:function(type,opts){this.type=type;this.detail=opts.detail}});
window.M2Archive.archive({code:'600000.SH',name:'test'});
assert.equal(window.M2Archive.isArchived('600000'),true);
// Reinitialize page code over the same browser storage, as after refresh/deploy.
vm.runInNewContext(contents,{window,console,CustomEvent:function(type,opts){this.type=type;this.detail=opts.detail}});
assert.equal(window.M2Archive.isArchived('600000.SH'),true);
window.M2Archive.restore('600000');assert.equal(window.M2Archive.isArchived('600000.SH'),false);
console.log('Existing archive persists across reload and explicit restore works; no storage migration.');
