(() => {
  const root = document.getElementById('market-breadth');
  const cacheKey = 'heimaq:all-market-breadth:v1';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct = value => value == null ? '—' : `${Number(value).toFixed(1)}%`;
  const color = value => value == null ? '#eee' : value < 20 ? '#16836a' : value < 40 ? '#a9d5c3' : value < 60 ? '#edf0f0' : value < 80 ? '#f0b3a5' : '#bd3b43';
  let data, attempt = null, period = 'ma20', span = 30, search = '', sort = 'strength';
  const point = value => value == null ? '—' : `${value > 0 ? '+' : ''}${value.toFixed(1)} 个百分点`;
  const fraction = m => m.pct==null ? '未取得该项数据' : m.valid==null ? '上游聚合值，未提供分子分母' : `${m.above} / ${m.valid} 只`;
  function participation() {
    const p=data.participation;
    if(!p)return '';
    return `<section class="participation-panel" aria-label="最新市场涨跌参与度"><div class="breadth-head"><h3>最新市场参与度</h3><span class="breadth-note">${esc(p.asOf)} 收盘 · 报价时间 ${esc(p.updatedAt)} · beta大盘云图</span></div><div class="breadth-stats">${[
      ['上涨占比',pct(p.upPct),`${p.up}涨 / ${p.down}跌 / ${p.flat}平`],
      ['个股涨跌幅中位数',pct(p.median),`${p.n}只有效报价，等权统计`],
      ['涨跌幅下四分位',pct(p.p25),'25%的股票涨跌幅不高于此值'],
      ['涨跌幅上四分位',pct(p.p75),'75%的股票涨跌幅不高于此值']
    ].map(([label,value,note])=>`<div class="breadth-stat"><span class="breadth-note">${label}</span><strong>${value}</strong><span class="breadth-note">${note}</span></div>`).join('')}</div><p class="breadth-note">涨跌参与度衡量当日修复力度；MA20/MA50宽度衡量趋势位置，两者分别计算。</p></section>`;
  }
  function weather() {
    const w=window.MarketWeather.evaluate(data,new Date(),attempt);
    const latest=data.market.at(-1);
    return `<section class="weather-panel weather-${esc(w.code)}" aria-label="市场天气与仓位参考">
      <div class="weather-summary"><div><span class="breadth-note">市场天气 · 收盘确认</span><h3>${esc(w.label)}</h3><p>${esc(w.action)}</p></div><div class="weather-budget"><span>现行 R05 环境档</span><strong>${esc(w.ceiling)}</strong><small>上限不是目标仓位，不触发自动交易</small></div></div>
      <div class="weather-gates">${w.gates.map(g=>`<div class="weather-gate"><b>${g.passed===true?'通过':g.passed===false?'未通过':'缺数据'} · ${esc(g.label)}</b><small>${esc(g.detail)}</small></div>`).join('')}</div>
      <div class="weather-evidence"><span>行业扩散 ${pct(w.sectorPct)}（${w.sectorAbove}/${w.sectorValid} 个行业宽度≥50%）</span><span>个股涨跌幅中位数 ${pct(latest.median)}</span><span>MA50五日变化 ${point(w.change50)}</span></div>
      ${!w.fresh.usable?`<p class="weather-stale">历史快照当时的分类：${esc(w.observed.label)}，不代表今天。最新采集：${esc(attempt?.attemptedAt || '没有运行记录')} ${attempt?.error?`· ${esc(attempt.error)}`:''}</p>`:''}
      <details class="weather-method"><summary>天气如何判定 / 仓位边界</summary><p>这是独立、未回测的观察分类：MA20或MA50站上比例低于30%为偏弱，低位五日改善标记修复；两项均≥50%、行业半数以上宽度≥50%、MA20五日不下降为扩散；扩散持续3日且MA20≥60%、MA50≥55%，至少3/5个指数站上上行的MA50，并有行业符合R02门槛，才标记顺风。</p><p>指数：上证、沪深300、中证1000、创业板、科创50。R02门槛：最新≥85且5日均≥80；或最新≥90且3日均≥80；或最新与5日均均≥70。缺失不算通过。</p><p>20%–30% / 40%–50% / 60%引用现行R05的防守、结构性行情、顺风环境参考上限；实际仓位仍取账户约束、个股买点及风险限制中的更严格值。红灯不新开仓，不用宽度替代止损。</p><p>盘中不提前写入收盘结论。工作日参考截止按北京时间16:00和周末计算，法定休市日未核实时保守提示待更新，不假装交易日历完整。</p></details>
    </section>`;
  }
  function valid(d) { return d?.schemaVersion === 1 && (d.coveragePct >= 95 || d.dataMode==='public-aggregates' && d.participation?.n>=4000) && d.market?.length && d.rows?.length; }
  function trend() {
    const width = Math.max(280, root.clientWidth), right = width - 12;
    const rows=data.market.slice(-span);
    const lines = (metric,stroke) => {
      const segments=[]; let points=[];
      rows.forEach((row,i)=>{if(row[metric].pct==null){if(points.length)segments.push(points);points=[];}else points.push(`${40+i/Math.max(1,rows.length-1)*(right-40)},${145-row[metric].pct*1.2}`);});
      if(points.length)segments.push(points);
      return segments.map(points=>`<polyline points="${points.join(' ')}" fill="none" stroke="${stroke}" stroke-width="2.5"/>`).join('');
    };
    return `<svg class="breadth-trend" viewBox="0 0 ${width} 180" role="img" aria-label="最近${span}个交易日全市场MA20和MA50站上比例趋势">${[0,50,100].map(n => `<line x1="40" y1="${145-n*1.2}" x2="${right}" y2="${145-n*1.2}" stroke="#ddd"/><text x="3" y="${149-n*1.2}" font-size="11">${n}%</text>`).join('')}${lines('ma20','#bd3b43')}${lines('ma50','#246b91')}<text x="40" y="173" font-size="11">${esc(rows[0]?.date)}</text><text x="${right}" y="173" text-anchor="end" font-size="11">${esc(data.asOf)}</text></svg>`;
  }
  function table() {
    let rows = data.rows.filter(row => row.industry.includes(search));
    rows = [...rows].sort((a,b) => sort === 'name' ? a.industry.localeCompare(b.industry,'zh-CN') : (b.series.at(-1)[period].pct ?? -1)-(a.series.at(-1)[period].pct ?? -1));
    const all = [{industry:data.universeLabel || '全市场', series:data.market}, ...rows];
    root.querySelector('.breadth-scroll').innerHTML = `<table class="breadth-table"><thead><tr><th>行业 / 日期</th>${data.dates.slice(-span).map(d=>`<th>${esc(d.slice(5))}</th>`).join('')}</tr></thead><tbody>${all.map(row=>`<tr><th scope="row">${esc(row.industry)}</th>${row.series.slice(-span).map(s=>{const m=s[period];return `<td style="background:${color(m.pct)};color:${m.pct!=null&&(m.pct<20||m.pct>=80)?'#fff':'#222'}"><button data-industry="${esc(row.industry)}" data-date="${s.date}" title="${esc(row.industry)} ${s.date} ${period.toUpperCase()}：${pct(m.pct)}；${esc(fraction(m))}" aria-label="${esc(row.industry)} ${s.date} ${pct(m.pct)}">${m.pct==null?'—':m.pct.toFixed(0)}</button></td>`;}).join('')}</tr>`).join('')}</tbody></table>`;
    root.querySelector('.breadth-scroll').scrollLeft = 99999;
  }
  function render(cached=false) {
    const latest=data.market.at(-1), old=data.market.at(-6), delta=old?.ma20.pct!=null && latest.ma20.pct!=null ? latest.ma20.pct-old.ma20.pct : null;
    const fresh=window.MarketWeather.freshness(data,new Date(),attempt);
    const partial=data.availableMetrics && !data.availableMetrics.includes('ma50');
    if(partial)period='ma20';
    root.innerHTML = `<div class="breadth-head"><h2>市场天气与市场宽度</h2><div><span class="breadth-note">${esc(data.asOf)} 收盘 · ${cached?'沿用上次快照':'已保存快照'} · ${fresh.usable?(partial?'MA20数据有效；MA50缺失':'数据有效'):'数据待更新'}</span> <a class="breadth-download" href="/market-breadth.json" download>下载原始数据</a></div></div>${participation()}${weather()}<div class="breadth-stats">${[
      [`${data.universeLabel || '全市场'} MA20站上比例`,pct(latest.ma20.pct),fraction(latest.ma20)],
      ['MA50 站上比例',pct(latest.ma50.pct),partial?'公开源未提供，不使用旧值':fraction(latest.ma50)],
      ['MA20 较5交易日前',delta==null?'—':`${delta>0?'+':''}${delta.toFixed(1)} 点`,'百分点变化'],
      ['收盘上涨比例',pct(latest.upPct),`${latest.up}涨 / ${latest.down}跌 / ${latest.flat}平`]
    ].map(([label,value,note])=>`<div class="breadth-stat"><span class="breadth-note">${label}</span><strong>${value}</strong><span class="breadth-note">${note}</span></div>`).join('')}</div><div class="breadth-legend"><span><i style="background:#bd3b43"></i>MA20</span><span><i style="background:#246b91"></i>MA50</span><span>全市场等权站上比例</span></div>${trend()}<div class="breadth-controls"><label>均线<select id="breadth-period"><option value="ma20">MA20</option><option value="ma50">MA50</option></select></label><label>区间<select id="breadth-span"><option value="30">30个交易日</option><option value="20">20个交易日</option><option value="10">10个交易日</option></select></label><label>行业<input id="breadth-search" type="search" placeholder="搜索行业"></label><label>排序<select id="breadth-sort"><option value="strength">最新宽度从高到低</option><option value="name">行业名称</option></select></label></div><div class="breadth-legend">${['0–20%','20–40%','40–60%','60–80%','80–100%'].map((s,i)=>`<span><i style="background:${color(i*20+1)}"></i>${s}</span>`).join('')}<span>灰色空格：数据不足</span></div><div class="breadth-scroll" tabindex="0" aria-label="行业市场宽度热力图"></div><p class="breadth-note">沪深京 ${data.universeCount} 只 · 同日历史覆盖 ${data.latestHistoryCount} 只（${data.coveragePct}%） · ${data.rows.length} 个行业 · ${esc(data.source)}</p><details class="breadth-note"><summary>计算口径与数据范围</summary><p>${esc(data.method)}</p><p>收盘后更新；未取得当天收盘数据时显示最近可用交易日。宽度为参与程度，不能独立确定买点。采集时间：${esc(data.generatedAt)}</p></details><dialog class="breadth-detail"><button aria-label="关闭详情">×</button><div></div></dialog>`;
    for (const [id,value] of [['period',period],['span',span],['search',search],['sort',sort]]) root.querySelector('#breadth-'+id).value=value;
    if(partial){const option=root.querySelector('#breadth-period option[value="ma50"]');option.disabled=true;option.textContent='MA50（数据未提供）';}
    if(data.dataMode==='public-aggregates'){
      root.querySelector('.breadth-head .breadth-note').textContent=`${data.asOf} 行业MA20 · 在线备用模式 · 全市场均线待逐股校验`;
      const notes=[...root.querySelectorAll('p.breadth-note')];
      const coverage=notes.find(p=>p.textContent.includes('同日历史覆盖'));
      if(coverage)coverage.textContent=`${data.rows.length}个行业MA20聚合值 · beta有效报价${data.participation.n}只 · 未取得全市场均线分母，不推算覆盖率`;
    }
    root.querySelector('#breadth-period').onchange=e=>{period=e.target.value;table();};
    root.querySelector('#breadth-span').onchange=e=>{span=Number(e.target.value);table();root.querySelector('.breadth-trend').outerHTML=trend();};
    root.querySelector('#breadth-search').oninput=e=>{search=e.target.value.trim();table();};
    root.querySelector('#breadth-sort').onchange=e=>{sort=e.target.value;table();};
    const dialog=root.querySelector('dialog');
    dialog.querySelector('button').onclick=()=>dialog.close();
    root.querySelector('.breadth-scroll').onclick=e=>{
      const b=e.target.closest('button[data-date]'); if(!b)return;
      const series=b.dataset.industry===(data.universeLabel || '全市场')?data.market:data.rows.find(r=>r.industry===b.dataset.industry).series;
      const s=series.find(r=>r.date===b.dataset.date), m=s[period];
      dialog.querySelector('div').innerHTML=`<h3>${esc(b.dataset.industry)}</h3><p>${s.date} 收盘 · ${period.toUpperCase()}</p><p>站上比例 ${pct(m.pct)}</p><p>${esc(fraction(m))}</p>${m.valid!=null?`<p>当日有效行情样本 ${s.n} 只；均线不足 ${s.n-m.valid} 只。</p>`:''}`;
      dialog.showModal();
    };
    root.querySelector('.breadth-legend span:last-child').textContent=`${data.universeLabel || '全市场'}等权站上比例${data.excludedMarkets?.length?'（北交所未覆盖）':''}`;
    if(partial)root.querySelector('.breadth-legend span:nth-child(2)').innerHTML='<i style="background:#246b91"></i>MA50（未提供）';
    root.querySelector('.breadth-trend').setAttribute('aria-label',`最近${span}个交易日${data.universeLabel || '全市场'}均线站上比例趋势`);
    const scopeNote=[...root.querySelectorAll('p.breadth-note')].find(p=>p.textContent.includes('同日历史覆盖'));
    if(scopeNote && data.universeLabel)scopeNote.textContent=scopeNote.textContent.replace(/^沪深京/,data.universeLabel)+' · 北交所不在MA20主指标范围';
    table();
  }
  async function load() {
    try {
      try {const r=await fetch('/market-breadth-status.json',{cache:'no-store'});if(r.ok){const j=await r.json();if(j.attemptedAt)attempt=j;}}catch{}
      const reads=await Promise.allSettled(['/market-breadth.json','/api/public-market'].map(async url=>{
        const response=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(20000)});
        if(!response.ok)throw Error('fetch');
        const value=await response.json();if(!valid(value))throw Error('coverage');
        // Show a verified new static snapshot immediately; a slow backup must
        // not leave the old cached chart visible for the full network timeout.
        if(!data || value.asOf>data.asOf || value.asOf===data.asOf && value.dataMode!=='public-aggregates'){
          data=value;render();try{localStorage.setItem(cacheKey,JSON.stringify(data));}catch{}
        }
        return value;
      }));
      const choices=reads.filter(r=>r.status==='fulfilled').map(r=>r.value).sort((a,b)=>b.asOf.localeCompare(a.asOf)||(a.dataMode==='public-aggregates'?1:0)-(b.dataMode==='public-aggregates'?1:0));
      const next=choices[0]; if(!next)throw Error('coverage');
      if(data && next.asOf<data.asOf)throw Error('older');
      data=next; render(); try{localStorage.setItem(cacheKey,JSON.stringify(data));}catch{}
    } catch {
      if(data)render(true); else root.textContent='市场宽度快照暂不可用，等待收盘数据更新。';
    }
  }
  try{const saved=JSON.parse(localStorage.getItem(cacheKey));if(valid(saved)){data=saved;render(true);}}catch{}
  load(); setInterval(load,1800000);
  new ResizeObserver(() => { if(data && root.querySelector('.breadth-trend')) root.querySelector('.breadth-trend').outerHTML=trend(); }).observe(root);
  document.getElementById('refreshBtn')?.addEventListener('click',load);
})();
