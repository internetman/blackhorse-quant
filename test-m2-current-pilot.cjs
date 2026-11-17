const assert = require('node:assert/strict');
const {model} = require('./m2-current-pilot.js');
const {model:formal} = require('./m2-daily-candidates.js');
const asOfDate = '2026-11-16';
const universe = {scopeId:'four-sector-close-v1',valid:78,total:80,
  sectors:['半导体','消费电子','光伏设备','电子化学品'].map((name,i)=>({name,valid:19+(i%2),total:20}))};
const candidates = [{code:'600000',name:'测试股',asOfDate,stage:'S2',position:'正常'}];
const good = {schemaVersion:1,mode:'derived-pilot',asOfDate,runStatus:'success',
  barStatus:'completed',universe,candidateCount:1,candidates};
assert.equal(model(good,asOfDate).candidates.length,1);
assert.equal(model(good,asOfDate,()=>true).candidates.length,0);
const partialZero = model({...good,candidateCount:0,candidates:[]},asOfDate);
assert.equal(partialZero.candidateCount,0);
assert.match(partialZero.emptyMessage,/未覆盖股票不能判定/);
const fullUniverse = {...universe,valid:80,sectors:universe.sectors.map(s=>({...s,valid:s.total}))};
assert.match(model({...good,universe:fullUniverse,candidateCount:0,candidates:[]},asOfDate).emptyMessage,/为 0 只/);
assert.equal(model(good,'2026-11-17'),null);
assert.equal(model(good,null),null);
assert.equal(formal(good,asOfDate).usable,false);
for (const patch of [{mode:'close'},{runStatus:'partial'},{barStatus:'intraday'},
  {candidateCount:2,candidates:[...candidates,...candidates]},
  {candidates:[{...candidates[0],asOfDate:'2026-11-13'}]},
  {universe:{...universe,scopeId:'full-market'}},
  {universe:{...universe,valid:77}},
  {universe:{...universe,valid:76,sectors:[{...universe.sectors[0],valid:17},...universe.sectors.slice(1)]}},
  {universe:{...universe,sectors:universe.sectors.map(s=>({...s,name:'半导体'}))}},
  {universe:{...universe,sectors:[null,...universe.sectors.slice(1)]}}])
  assert.equal(model({...good,...patch},asOfDate),null);
console.log('PASS current-only and exact four-sector gate, duplicate and archived validation, valid zero, no official-feed promotion');
