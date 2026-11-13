const assert=require('node:assert/strict');const {model}=require('./m2-pilot-view.js');const d=require('./m2-pilot-display.json');
assert.equal(model(d,'2026-11-13').show,true);
assert.equal(model(d,'2026-11-14').show,false);assert.equal(model(d,'2026-11-12').show,false);
for(const patch of [{mode:'close'},{valid:360},{asOfDate:'2026-11-14'},{candidates:[]},{sectors:[]}])assert.equal(model({...d,...patch},'2026-11-13').show,false);
assert.deepEqual(d.candidates.map(x=>x.code),['688213','603893','688018']);
assert.deepEqual(Object.keys(d.candidates[0]).sort(),['classification','code','name']);
console.log('PASS pilot exact date/scope/three classifications, no raw metrics, day expiry, no official-feed promotion');
