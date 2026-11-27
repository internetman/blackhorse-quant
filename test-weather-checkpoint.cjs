const assert=require('node:assert/strict'),fs=require('node:fs'),vm=require('node:vm');
const fixed=Date.parse('2026-11-27T07:00:00Z');
class Clock extends Date { constructor(...args){super(...(args.length?args:[fixed]));}static now(){return fixed;} }
function harness(){
 let html='',text='',renders=[];
 const root={set innerHTML(v){html=v;},get innerHTML(){return html;},set textContent(v){text=v;},querySelector:()=>null};
 const ctx={Date:Clock,Intl,console,AbortSignal,setTimeout,document:{getElementById:()=>root},localStorage:{setItem(){}},record:v=>renders.push(v)};
 ctx.window=ctx;vm.createContext(ctx);vm.runInContext(fs.readFileSync('market-weather.js','utf8'),ctx);
 let source=fs.readFileSync('market-breadth.js','utf8');
 source=source.replace('  try{const saved=JSON.parse(localStorage.getItem(cacheKey));',`  globalThis.hooks={weather,participation,validParticipation,refresh,renderReferenceOnly,set:(d,p,m)=>{data=d;liveParticipation=p;midday=m;},check:value=>Object.assign(checkpoint,value),state:()=>({checkpoint:{...checkpoint},attempt,data,liveParticipation}),stubRender:()=>{render=cached=>record({cached,weather:weather(),participation:participation(),asOf:data?.asOf});}};return;
  try{const saved=JSON.parse(localStorage.getItem(cacheKey));`);
 vm.runInContext(source,ctx);
 return {ctx,hooks:ctx.hooks,html:()=>html,text:()=>text,renders:()=>renders};
}
const calendar=JSON.parse(fs.readFileSync('market-trading-calendar.json','utf8'));
const close=JSON.parse(fs.readFileSync('market-breadth.json','utf8'));
const midday=JSON.parse(fs.readFileSync('market-breadth-midday.json','utf8'));
const quote=(day='2026-11-27')=>({asOf:day,updatedAt:day+'T14:10:00+08:00',barStatus:'intraday',n:5000,up:3000,down:1900,flat:100,upPct:60,median:1,p25:-1,p75:2});
(async()=>{
 const warm=harness();warm.hooks.set(close);let panel=warm.hooks.weather();
 assert(panel.includes('正在核验收盘状态'));assert(!panel.includes('读取失败'));
 warm.ctx.MarketWeather.setCalendar(calendar);warm.hooks.check({settled:true,calendarOK:true,statusOK:false});
 panel=warm.hooks.weather();assert(panel.includes('最新采集记录读取失败'));assert(panel.includes(close.asOf));assert(panel.includes('2026-11-26'));assert(!panel.includes('交易日历读取失败'));
 warm.hooks.check({calendarOK:false});panel=warm.hooks.weather();assert(panel.includes('交易日历读取失败'));assert(panel.includes('暂无法确定'));
 warm.hooks.check({calendarOK:true,statusOK:true});panel=warm.hooks.weather();assert(!panel.includes('正在核验收盘状态'));assert(!panel.includes('收盘状态暂无法核验'));
 const stale=structuredClone(close);stale.asOf='2026-11-04';stale.market.at(-1).date=stale.asOf;warm.hooks.set(stale);
 panel=warm.hooks.weather();assert(panel.includes('等待 2026-11-26 收盘数据'));assert(panel.includes('最近有效收盘：2026-11-04'));assert(panel.includes('应有收盘日：2026-11-26'));
 const nowQuote=quote();assert(warm.hooks.validParticipation(nowQuote));
 for(const modify of [p=>p.n=3000,p=>p.upPct=80,p=>p.updatedAt='2026-11-27T14:10:00',p=>p.updatedAt='2026-11-28T14:10:00+08:00',p=>p.asOf='2026-11-26']){
  const bad=structuredClone(nowQuote);modify(bad);assert(!warm.hooks.validParticipation(bad));
 }
 warm.hooks.set(undefined,quote('2026-11-26'));assert(warm.hooks.participation().includes('历史市场参与度'));assert(warm.hooks.participation().includes('历史报价，仅供回看'));
 warm.hooks.set(undefined,undefined,midday);warm.hooks.renderReferenceOnly();assert(warm.html().includes('午盘'));assert(warm.html().includes('非收盘确认'));assert(warm.html().includes('暂无收盘天气判断'));
 const cold=harness();cold.hooks.stubRender();
 cold.ctx.fetch=async url=>({ok:!['/market-breadth-archive.json','/market-breadth.json'].includes(url),json:async()=>url==='/market-trading-calendar.json'?calendar:url==='/market-breadth-status.json'?{status:'success',attemptedAt:'2026-11-27T14:43:25+08:00'}:url==='/market-breadth-midday.json'?midday:{schemaVersion:1,participation:nowQuote}});
 await cold.hooks.refresh();
 assert.equal(cold.hooks.state().data,undefined,'invalid breadth must not become a close snapshot');
 assert.equal(cold.hooks.state().liveParticipation.asOf,'2026-11-27','valid participation survives invalid breadth');
 assert(cold.html().includes('当日市场参与度'));assert(cold.html().includes('暂无收盘天气判断'));
 const delayed=harness();delayed.hooks.set(close);delayed.hooks.stubRender();let releaseCalendar,releaseStatus;
 delayed.ctx.fetch=async url=>{
  if(url==='/market-breadth-archive.json')return new Promise(()=>{});
  if(url==='/market-trading-calendar.json')return new Promise(resolve=>releaseCalendar=()=>resolve({ok:true,json:async()=>calendar}));
  if(url==='/market-breadth-status.json')return new Promise(resolve=>releaseStatus=()=>resolve({ok:true,json:async()=>({status:'success',attemptedAt:'2026-11-27T14:43:25+08:00'})}));
  return {ok:url==='/market-breadth.json',json:async()=>close};
 };
 const pending=delayed.hooks.refresh();await new Promise(r=>setImmediate(r));
 assert(delayed.hooks.weather().includes('正在核验收盘状态'));
 releaseCalendar();await new Promise(r=>setImmediate(r));assert(delayed.hooks.weather().includes('正在核验收盘状态'),'calendar alone does not finish status checkpoint');
 releaseStatus();await pending;assert(delayed.hooks.state().checkpoint.settled);assert(!delayed.hooks.weather().includes('正在核验收盘状态'));
 console.log('Weather startup checkpoint, exact failure dates, dated participation and midday-only fallback passed.');
})().catch(error=>{console.error(error);process.exitCode=1;});
