const assert=require('node:assert/strict');const {model}=require('./m2-daily-candidates.js');
const fixture=()=>({schemaVersion:1,asOfDate:'2026-11-11',mode:'close',runStatus:'success',barStatus:'completed',candidateCount:8,candidates:Array.from({length:8},(_,i)=>({code:String(600000+i),asOfDate:'2026-11-11'}))});
const date='2026-11-11';
let d=fixture();assert.equal(model(d,date).candidates.length,8);assert.equal(model(d,date).usable,true);
for(const expected of [null,'2026-11-10','2026-11-12','bad']) {const m=model(d,expected);assert.equal(m.candidates.length,0);assert.equal(m.usable,false);assert.match(m.emptyMessage,/不代表筛选结果为零/);}
for(const patch of [{mode:'replay'},{mode:'intraday'},{runStatus:'failed'},{runStatus:undefined},{barStatus:'partial'},{candidateCount:9}]) {const m=model({...d,...patch},date);assert.equal(m.candidates.length,0);assert.equal(m.usable,false);}
let z={...d,candidateCount:0,candidates:[]};assert.match(model(z,date).emptyMessage,/已成功.*0 只/);
assert.match(model(z,'2026-11-12').emptyMessage,/不代表筛选结果为零/);
assert.match(model({...z,runStatus:'failed'},date).emptyMessage,/不代表筛选结果为零/);
assert.equal(model(d,date,c=>c==='600000').candidates.length,7);
assert.match(model(d,date,()=>true).emptyMessage,/均已手动归档/);
d.asOfDate='2026-11-12';d.candidates.forEach(c=>c.asOfDate=d.asOfDate);assert.equal(model(d,d.asOfDate,c=>c==='600000').candidates.length,7);
d.candidates[0].asOfDate='2026-11-11';assert.equal(model(d,d.asOfDate).usable,false);
assert.throws(()=>model(null,date));
console.log('PASS current verified close only; stale/future/replay/calendar/failed gates; valid zero distinct; archive persistence.');
