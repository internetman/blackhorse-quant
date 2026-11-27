const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
let html='',weatherInput,renderCount=0,archiveReads=0,archiveResolve;
let source=fs.readFileSync('market-breadth.js','utf8');
source=source.replace('  try{const saved=JSON.parse(localStorage.getItem(cacheKey));',`  checkpoint.settled=checkpoint.calendarOK=checkpoint.statusOK=true;globalThis.hooks={validArchive,sourceSnapshot,chartContext,heatmapColumns,visibleColumns,trend,table,weather,refresh,loadArchive,set:(current,history,mode='all',days=30)=>{data=current;archive=history;chartMode=mode;span=days;},calendar:value=>{heatmapCalendar=value;},stubRender:fn=>{render=fn;}};return;
  try{const saved=JSON.parse(localStorage.getItem(cacheKey));`);
const scrolling={set innerHTML(value){html=value;},scrollLeft:0};
const archiveOption={disabled:true,textContent:''},periodOption={disabled:true,textContent:''},periodSelect={querySelector:()=>periodOption},context={innerHTML:''},scope={},method={};
const root={clientWidth:800,querySelector:selector=>selector==='.breadth-scroll'?scrolling:selector==='#breadth-chart-context'?context:selector==='#breadth-scope-note'?scope:selector==='#breadth-chart-method'?method:selector==='#breadth-period'?periodSelect:selector.includes('option[value="archive"]')?archiveOption:null};
const ctx={document:{getElementById:()=>root},Date,console,AbortSignal,localStorage:{setItem(){}},window:{MarketWeather:{setCalendar(){},evaluate(d){weatherInput=d;return {code:'weak',label:'fixture',action:'fixture',ceiling:'fixture',gates:[],fresh:{usable:true}};}}}};
vm.createContext(ctx);vm.runInContext(source,ctx);
const point=(date,pct=50)=>({date,n:5000,ma20:{pct,above:2500,valid:5000},ma50:{pct,above:2500,valid:5000}});
const fixture=(dates,scope)=>({schemaVersion:1,coveragePct:95,scopeVersion:scope,asOf:dates.at(-1),dates,market:dates.map(d=>point(d)),rows:[{industry:'银行',series:dates.map(d=>point(d))}],availableMetrics:['ma20','ma50'],universeLabel:'沪深A股',source:'fixture'});
const archive=JSON.parse(fs.readFileSync('market-breadth-archive.json','utf8'));
const current=fixture(['2026-11-18','2026-11-19','2026-11-20','2026-11-23','2026-11-24','2026-11-25'],'qfq-shsz-baostock-v1');
ctx.hooks.calendar(JSON.parse(fs.readFileSync('market-trading-calendar.json','utf8')));
assert(ctx.hooks.validArchive(archive));
for(const modify of [d=>d.scopeVersion=current.scopeVersion,d=>d.dates.reverse(),d=>d.market.pop(),d=>d.rows[0].series[0].date='2026-11-10',d=>d.market[0].ma20.pct=101,d=>d.rows[0]=null]){
 const bad=structuredClone(archive);modify(bad);assert(!ctx.hooks.validArchive(bad));
}
const before=JSON.stringify(current),archiveBefore=JSON.stringify(archive);
ctx.hooks.set(current,null);ctx.hooks.table();
assert.equal(ctx.hooks.visibleColumns().length,6,'current region renders immediately before optional history');
ctx.hooks.set(current,archive);ctx.hooks.table();
const visible=ctx.hooks.visibleColumns();
assert.equal(visible.length,30,'default heatmap includes the latest 30 dates without a toggle');
assert.equal(visible.filter(c=>c.source==='archive').length,21);
assert.deepEqual(Array.from(visible.filter(c=>c.source==='gap'),c=>c.date),['2026-11-13','2026-11-16','2026-11-17']);
assert.equal(visible.filter(c=>c.source==='current').length,6);
assert(html.includes('breadth-source-row'));assert(html.includes('breadth-scope-boundary'));
assert(html.includes('历史归档 · 腾讯/东财 + FFD'));assert(html.includes('当前口径 · 日线收益率复权'));
for(const date of ['2026-11-13','2026-11-16','2026-11-17']){
 assert(html.includes(`data-date="${date}" data-source="gap"`));
 assert(html.includes(`data-date="${date}" data-source="gap" title="沪深A股 ${date} 缺少已核验数据 MA20：—；未取得已核验快照"`));
}
assert(ctx.hooks.chartContext().includes('实际显示 30 个日期'));
assert(!ctx.hooks.chartContext().includes('qfq-shsz-ffd-experimental-v1'));
ctx.hooks.weather();assert.equal(weatherInput,current,'combined heatmap must not feed weather');
assert.equal(ctx.hooks.sourceSnapshot('current'),current);
assert(ctx.hooks.trend().includes('2026-11-18'));assert(!ctx.hooks.trend().includes('2026-09-28'));
assert.equal(JSON.stringify(current),before);assert.equal(JSON.stringify(archive),archiveBefore);
ctx.hooks.set(current,archive,'archive');assert.equal(ctx.hooks.visibleColumns().length,29);ctx.hooks.table();assert(!html.includes('data-date="2026-11-25"'));
assert.equal(ctx.hooks.sourceSnapshot('current'),current,'even archive-only heatmap leaves current line chart alone');
ctx.hooks.set(current,archive,'all',0);assert.equal(ctx.hooks.visibleColumns().length,38);
ctx.hooks.set(current,archive,'current');assert.equal(ctx.hooks.visibleColumns().length,6);
const overlap=fixture(['2026-11-11','2026-11-12','2026-11-13'],'qfq-shsz-baostock-v1');
ctx.hooks.set(overlap,archive,'all',0);
assert.equal(ctx.hooks.heatmapColumns().filter(c=>c.date==='2026-11-11').length,1,'never duplicate overlapping source dates');
assert.equal(ctx.hooks.heatmapColumns().find(c=>c.date==='2026-11-11').source,'current','current source wins overlap without blending');
(async()=>{
 ctx.hooks.stubRender(()=>{renderCount++;});ctx.hooks.set(undefined,null);
 ctx.fetch=async url=>{
  if(url==='/market-breadth-archive.json'){archiveReads++;return new Promise(resolve=>{archiveResolve=resolve;});}
  return {ok:!['/market-breadth-midday.json','/api/public-market'].includes(url),json:async()=>url==='/market-breadth.json'?{...current,availableMetrics:['ma20']}:JSON.parse(fs.readFileSync('market-trading-calendar.json','utf8'))};
 };
 await Promise.race([ctx.hooks.refresh(),new Promise((_,reject)=>setTimeout(()=>reject(Error('archive blocked current snapshot')),200))]);
 assert(renderCount>0);assert.equal(ctx.hooks.sourceSnapshot('current').asOf,current.asOf);assert.equal(archiveReads,1);
 const pending=ctx.hooks.loadArchive();assert.equal(archiveReads,1);
 const rendersBeforeArchive=renderCount;
 archiveResolve({ok:true,json:async()=>archive});await pending;
 assert.equal(renderCount,rendersBeforeArchive,'archive arrival must not rerender weather, cache status or dialog');
 assert.equal(archiveOption.disabled,false);assert(archiveOption.textContent.includes('29 个交易日'));
 assert.equal(periodOption.disabled,false,'late archive enables MA50 cells without rerendering current panels');
 assert.equal(ctx.hooks.visibleColumns().length,30,'archive arrival automatically extends default heatmap');
 assert(context.innerHTML.includes('按来源分段'));assert(html.includes('data-date="2026-11-13"'));
 await ctx.hooks.loadArchive();assert.equal(archiveReads,1);
 console.log('Default combined heatmap, source boundaries, real gaps, chart isolation and nonblocking loading passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
