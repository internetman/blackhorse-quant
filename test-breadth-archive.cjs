const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let html='',weatherInput,renderCount=0,archiveReads=0,archiveResolve;
let source=fs.readFileSync('market-breadth.js','utf8');
source=source.replace('  try{const saved=JSON.parse(localStorage.getItem(cacheKey));',`  globalThis.hooks={validArchive,chartSnapshot,chartContext,trend,table,weather,refresh,loadArchive,set:(current,history,mode='current')=>{data=current;archive=history;chartMode=mode;},stubRender:fn=>{render=fn;}};return;
  try{const saved=JSON.parse(localStorage.getItem(cacheKey));`);
const scrolling={set innerHTML(value){html=value;},scrollLeft:0};
const archiveOption={disabled:true,textContent:''};
const root={clientWidth:800,querySelector:selector=>selector==='.breadth-scroll'?scrolling:selector.includes('option[value="archive"]')?archiveOption:null};
const ctx={document:{getElementById:()=>root},Date,console,AbortSignal,localStorage:{setItem(){}},window:{MarketWeather:{setCalendar(){},evaluate(d){weatherInput=d;return {code:'weak',label:'fixture',action:'fixture',ceiling:'fixture',gates:[],fresh:{usable:true}};}}}};
vm.createContext(ctx);vm.runInContext(source,ctx);
const point=(date,pct=50)=>({date,n:5000,ma20:{pct,above:2500,valid:5000},ma50:{pct,above:2500,valid:5000}});
const fixture=(dates,scope)=>({schemaVersion:1,coveragePct:95,scopeVersion:scope,asOf:dates.at(-1),dates,market:dates.map(d=>point(d)),rows:[{industry:'银行',series:dates.map(d=>point(d))}],availableMetrics:['ma20','ma50'],universeLabel:'沪深A股',source:'fixture'});
const archive=fixture(['2026-11-11','2026-11-12'],'qfq-shsz-ffd-experimental-v1');
const current=fixture(['2026-11-24','2026-11-25'],'qfq-shsz-baostock-v1');
assert(ctx.hooks.validArchive(archive));
for(const modify of [d=>d.scopeVersion=current.scopeVersion,d=>d.dates.reverse(),d=>d.market.pop(),d=>d.rows[0].series[0].date='2026-11-10',d=>d.market[0].ma20.pct=101,d=>d.rows[0]=null]){
 const bad=structuredClone(archive);modify(bad);assert(!ctx.hooks.validArchive(bad));
}
const sparse=structuredClone(archive);sparse.market[0].ma20.pct=null;assert(ctx.hooks.validArchive(sparse),'original missing cells stay missing');
const before=JSON.stringify(current);
ctx.hooks.set(current,archive,'archive');ctx.hooks.table();
assert(html.includes('11-11'));assert(!html.includes('11-25'));
assert(ctx.hooks.chartContext().includes('历史归档（截至 11 月 12 日）'));
assert(ctx.hooks.chartContext().includes('实际显示 2 个交易日'));
assert(!ctx.hooks.chartContext().includes('qfq-shsz-ffd-experimental-v1'));
ctx.hooks.weather();assert.equal(weatherInput,current,'archive selection must not feed weather');
assert.equal(JSON.stringify(current),before,'archive selection must not splice or mutate current snapshot');
ctx.hooks.set(current,archive);ctx.hooks.table();assert(html.includes('11-25'));assert(!html.includes('11-11'));
(async()=>{
 ctx.hooks.stubRender(()=>{renderCount++;});ctx.hooks.set(undefined,null);
 ctx.fetch=async url=>{
  if(url==='/market-breadth-archive.json'){archiveReads++;return new Promise(resolve=>{archiveResolve=resolve;});}
  return {ok:!['/market-breadth-midday.json','/api/public-market'].includes(url),json:async()=>url==='/market-breadth.json'?current:{}};
 };
 await Promise.race([ctx.hooks.refresh(),new Promise((_,reject)=>setTimeout(()=>reject(Error('archive blocked current snapshot')),200))]);
 assert(renderCount>0);assert.equal(ctx.hooks.chartSnapshot().asOf,current.asOf);assert.equal(archiveReads,1);
 const pending=ctx.hooks.loadArchive();assert.equal(archiveReads,1,'deduplicate an in-flight optional archive read');
 const rendersBeforeArchive=renderCount;
 archiveResolve({ok:true,json:async()=>archive});await pending;
 assert.equal(renderCount,rendersBeforeArchive,'archive arrival must not rerender current panels or close a dialog');
 assert.equal(archiveOption.disabled,false);assert(archiveOption.textContent.includes('2 个交易日'));
 await ctx.hooks.loadArchive();assert.equal(archiveReads,1,'verified archive is not downloaded on every refresh');
 console.log('Archive scope, date selection, weather isolation and nonblocking loading passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
