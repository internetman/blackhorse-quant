/* Derived review pilot only. Never populates the official daily candidate feed. */
(function(root){
'use strict';
function model(d,today){
 const ok=d?.schemaVersion===1 && d.mode==='derived-pilot' && d.asOfDate==='2026-11-13' && d.asOfDate===today && d.valid===356 && d.total===360 && Array.isArray(d.sectors) && d.sectors.length===4 && Array.isArray(d.candidates) && d.candidates.length===3 && d.candidates.every(c=>/^\d{6}$/.test(c.code)&&typeof c.name==='string'&&['S2正常','S2延伸','S2位置待核'].includes(c.classification));
 return {show:ok,title:'2026-11-13 收盘后 · 四板块试跑',data:d};
}
function today(){return new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());}
function element(tag,text){const e=document.createElement(tag);e.textContent=text;return e;}
async function boot(){const host=document.getElementById('derivedPilot');if(!host)return;try{const r=await fetch('/m2-pilot-display.json',{cache:'no-store'});if(!r.ok)return;const d=await r.json();const refresh=()=>{host.replaceChildren();const m=model(d,today());host.hidden=!m.show;if(!m.show)return;host.append(element('h2',m.title),element('p','独立试跑，非正式自动名单；非全市场，非供应商最终确认，全部待核，需人工复盘。'),element('p',`${d.sectors.join('、')} · 有效 356 / 360`));for(const c of d.candidates.filter(c=>!root.M2Archive?.isArchived(c.code)))host.append(element('p',`${c.code} ${c.name} · ${c.classification} · 待核 · 数据日期 2026-11-13`));};refresh();root.M2Archive?.subscribe(refresh);root.setInterval(refresh,60000);}catch(_){host.hidden=true;}}
if(typeof module!=='undefined'&&module.exports)module.exports={model};if(typeof document!=='undefined')boot();
})(typeof window!=='undefined'?window:globalThis);
