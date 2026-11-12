const assert = require('node:assert/strict');
const weather = require('./market-weather.js');
weather.setCalendar(require('./market-trading-calendar.json'));
const now = new Date('2026-11-04T06:00:00Z');
const dates = ['2026-10-23','2026-10-26','2026-10-27','2026-10-28','2026-10-29','2026-10-30','2026-11-02','2026-11-03'];
function fixture(a=70,b=60) {
  const market=dates.map(date=>({date,n:100,up:60,down:40,flat:0,median:1,ma20:{pct:a,above:a,valid:100},ma50:{pct:b,above:b,valid:100}}));
  return {schemaVersion:1,asOf:dates.at(-1),generatedAt:'2026-11-03T08:30:00Z',barStatus:'completed',coveragePct:100,
    dates,market,rows:[{industry:'测试',series:market.map(r=>({...r,ma20:{pct:85,above:85,valid:100}}))}],
    benchmarks:['1.000001','1.000300','1.000852','0.399006','1.000688'].map(secid=>({secid,asOf:dates.at(-1),close:110,ma50:100,ma50Slope20:1}))};
}
assert.equal(weather.expectedCloseDate(now),'2026-11-03');
assert.equal(weather.expectedCloseDate(new Date('2026-11-09T01:00:00Z')),'2026-11-06');
assert.equal(weather.expectedCloseDate(new Date('2026-10-07T09:00:00Z')),'2026-09-30');
assert.equal(weather.expectedCloseDate(new Date('2026-10-10T09:00:00Z')),'2026-10-09');
assert.equal(weather.expectedCloseDate(new Date('2027-02-01T09:00:00Z')),null);
assert.equal(weather.evaluate(fixture(),now).code,'favorable');
let d=fixture();d.benchmarks=[];
assert.equal(weather.evaluate(d,now).code,'expansion');
assert.equal(weather.evaluate(d,now).gates.find(g=>g.label==='指数趋势确认').passed,null);
d=fixture();d.asOf='2026-09-11';d.market.at(-1).date=d.asOf;
assert.equal(weather.evaluate(d,now).code,'unavailable');
d=fixture();d.asOf='2026-11-04';d.market.at(-1).date=d.asOf;
assert.equal(weather.evaluate(d,now).code,'unavailable');
d=fixture();d.market.at(-1).ma20.pct=null;
assert.equal(weather.evaluate(d,now).code,'unknown');
d=fixture(20,25);
assert.equal(weather.evaluate(d,now).code,'weak');
d.market.at(-1).ma20.pct=25;
assert.equal(weather.evaluate(d,now).code,'repair');
d=fixture();d.benchmarks[0].asOf='2026-11-02';
assert.notEqual(weather.evaluate(d,now).code,'favorable');
d=fixture();
assert.equal(weather.evaluate(d,now,{status:'failed',attemptedAt:'2026-11-04T12:00:00+08:00'}).code,'unavailable');
d=fixture();d.market.forEach(r=>{r.ma50={pct:null,above:0,valid:0};});
assert.equal(weather.evaluate(d,now).code,'partial');
assert.notEqual(weather.evaluate(d,now).code,'favorable');
console.log('Weather gates: freshness, missing values, continuity, indices and failed refresh passed.');

d=fixture();d.benchmarks[4]={...d.benchmarks[0]};assert.equal(weather.evaluate(d,now).gates.find(g=>g.label==='指数趋势确认').passed,null);
d=fixture();d.benchmarks[0].close=null;assert.notEqual(weather.evaluate(d,now).code,'favorable');
