const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let source=fs.readFileSync('market-breadth.js','utf8');
source=source.replace('  try{const saved=JSON.parse(localStorage.getItem(cacheKey));',`  globalThis.hooks={validMidday,render:(d,c,failed=false)=>{midday=d;data=c;middayReadFailed=failed;return middayPanel();}};return;
  try{const saved=JSON.parse(localStorage.getItem(cacheKey));`);
const ctx={document:{getElementById:()=>({})},Date,console};vm.createContext(ctx);vm.runInContext(source,ctx);
const day=new Date(Date.now()+8*3600000).toISOString().slice(0,10);
const prior=new Date(Date.parse(day+'T00:00:00Z')-86400000).toISOString().slice(0,10);
const d={schemaVersion:1,scopeVersion:'qfq-shsz-midday-v1',session:'midday',barStatus:'intraday',asOf:day,previousCloseDate:prior,membershipDate:prior,observedAt:day+'T11:59:00+08:00',generatedAt:day+'T12:10:00+08:00',coveragePct:100,universeCount:5000,latestHistoryCount:5000,market:{ma20:{valid:5000,above:3000,pct:60},ma50:{valid:5000,above:2500,pct:50},upPct:55,up:2750,down:2250,flat:0},rows:Array.from({length:50},(_,i)=>({industry:i?'行业'+i:'<script>alert(1)</script>',ma20:{pct:60},ma50:{pct:50}})),method:'实测动态宽度'};
assert(ctx.hooks.validMidday(d));
for(const modify of [x=>x.barStatus='completed',x=>x.session='close',x=>x.coveragePct=NaN,x=>delete x.rows,x=>x.rows=[],x=>x.previousCloseDate=day,x=>x.observedAt=day+'T15:00:00+08:00',x=>x.observedAt=day+'T11:59:00',x=>x.market.ma50.pct=65]){
 const bad=structuredClone(d);modify(bad);assert(!ctx.hooks.validMidday(bad));
}
const close={asOf:prior,market:[{date:prior,ma20:{pct:40}}]};const before=JSON.stringify(close);
const html=ctx.hooks.render(d,close);
assert(html.includes('今日午盘参考 · 非收盘确认'));assert(html.includes('60.0%'));assert(html.includes('50.0%'));assert(html.includes('3000 / 5000 只'));assert(!html.includes('<script>'));assert(html.includes('&lt;script&gt;'));
assert.equal(JSON.stringify(close),before);
assert.equal(ctx.hooks.render(d,close),html,'repeated render should be idempotent');
assert(ctx.hooks.render(d,{asOf:day}).includes('当日午盘回看'));
assert(ctx.hooks.render(d,close,true).includes('最新午盘文件读取失败'));
assert.equal(ctx.hooks.render({...d,barStatus:'completed'},close),'');
console.log('midday view tests passed');
