const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const day='2026-11-25', prev='2026-11-24', at=s=>day+'T'+s+':00Z';
const metric={valid:5000,above:2500,pct:50};
const row={date:day,ma20:metric,ma50:metric};
const close={schemaVersion:1,asOf:day,generatedAt:at('08:10'),barStatus:'completed',coveragePct:100,market:[row],rows:[{industry:'fixture',series:[row]}],dates:[day]};
const noon={schemaVersion:1,scopeVersion:'qfq-shsz-midday-v1',session:'midday',barStatus:'intraday',coveragePct:100,universeCount:5000,latestHistoryCount:5000,asOf:day,previousCloseDate:prev,membershipDate:prev,observedAt:day+'T11:59:00+08:00',generatedAt:day+'T12:10:00+08:00',rows:Array.from({length:50},()=>({industry:'fixture'})),market:{ma20:metric,ma50:metric}};
const fallback=date=>({...close,asOf:date,dataMode:'public-aggregates',participation:{asOf:date,updatedAt:date+'T16:15:00+08:00',n:5050,upPct:35},market:[{...row,date,ma20:{pct:null},ma50:{pct:null}}]});
const status=(time,status)=>({attemptedAt:at(time),status});
const calendar={schemaVersion:1,years:{2026:{closures:[]}}};
const round=(attempt,midday=noon,formal=close,backup)=>[midday,calendar,attempt,formal,backup];
const halt=()=>new Promise(r=>setImmediate(r));
function fixture(rounds,cached) {
  let rendered, fetches=0, unblock;
  const first=new Promise(r=>unblock=r);
  let handlers={};
  const raws=fs.readFileSync(process.env.RADAR_LOADER || 'market-breadth.js','utf8');
  const idx=raws.indexOf('  try{const saved=JSON.parse(localStorage.getItem(cacheKey));');
  assert(idx>0);
  const source=raws.slice(0,idx)+`  render=(cached)=>record({data,attempt,midday,middayReadFailed,live:typeof liveParticipation==='undefined'?undefined:liveParticipation,eligible:window.MarketWeather.freshness(data,new Date('${at('09:00')}'),attempt).usable});\n`+raws.slice(idx);
  const ctx={console,Date,Intl,AbortSignal,record:x=>{rendered=x;},fetch:async url=>{
    const i=fetches++;
    if(i===0)await first;
    const v=rounds[Math.floor(i/5)]?.[i%5];
    return {ok:!!v,json:async()=>v};
  },document:{getElementById:id=>id==='refreshBtn'?{addEventListener:(_,fn)=>handlers.manual=fn}:{}},setInterval:fn=>handlers.timer=fn,ResizeObserver:class{observe(){}},localStorage:{getItem:()=>JSON.stringify(cached),setItem:()=>{}}};
  ctx.window=ctx; vm.createContext(ctx);
  vm.runInContext(fs.readFileSync('market-weather.js','utf8'),ctx);
  vm.runInContext(source,ctx);
  return {fetches:()=>fetches,release:unblock,last:()=>rendered,manual:()=>handlers.manual(),timer:()=>handlers.timer()};
}
(async()=>{
  const overlap=fixture([round(status('08:00','ok'),null),round(status('08:30','failed')),round(status('08:45','ok'))]);
  overlap.manual();const queued=overlap.timer();
  await halt();
  assert.equal(overlap.fetches(),3,'scheduled and manual triggers should wait behind the pending initial refresh');
  overlap.release();await queued;
  assert.equal(overlap.fetches(),10,'piled-up triggers should coalesce into one follow-up');
  assert.equal(overlap.last().attempt.status,'failed');
  assert.equal(overlap.last().eligible,false);
  assert.equal(overlap.last().middayReadFailed,false);
  await overlap.manual();
  assert.equal(overlap.last().eligible,true,'verified newer status should restore eligibility');
  const reversed=fixture([round(status('08:30','failed')),round(status('08:00','ok'))]);
  reversed.release();await halt();await reversed.manual();
  assert.equal(reversed.last().eligible,false,'older status cannot overwrite a newer failure even on a later read');
  for (const date of [prev,day,'2026-11-26']) {
    const warm=fixture([round(status('08:30','failed'),noon,null,fallback(date))],close);
    warm.release();await halt();
    assert.equal(warm.last().data.dataMode,undefined,'backup must never replace a cached formal snapshot');
    assert.equal(warm.last().live.asOf,date,'participation remains available independently');
  }
  const cold=fixture([round(status('08:00','ok'),noon,null,fallback(day)),round(status('08:30','failed'),noon,close,fallback(day))]);
  cold.release();await halt();assert.equal(cold.last().data.dataMode,'public-aggregates');assert.equal(cold.last().eligible,false);
  await cold.manual();assert.equal(cold.last().data.dataMode,undefined);assert.equal(cold.last().eligible,false);
  console.log('radar refresh regression cases passed');
})().catch(error=>{console.error(error);process.exitCode=1;});
