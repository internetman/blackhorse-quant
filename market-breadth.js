(() => {
  const root = document.getElementById('market-breadth');
  const cacheKey = 'heimaq:all-market-breadth:v1';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct = value => value == null ? '—' : `${Number(value).toFixed(1)}%`;
  const color = value => value == null ? '#eee' : value < 20 ? '#16836a' : value < 40 ? '#a9d5c3' : value < 60 ? '#edf0f0' : value < 80 ? '#f0b3a5' : '#bd3b43';
  let data, period = 'ma20', span = 30, search = '', sort = 'strength';
  function valid(d) { return d?.schemaVersion === 1 && d.coveragePct >= 95 && d.market?.length && d.rows?.length; }
  function trend() {
    const width = Math.max(280, root.clientWidth), right = width - 12;
    const line = metric => data.market.map((row, i) => row[metric].pct == null ? '' : `${40+i/Math.max(1,data.market.length-1)*(right-40)},${145-row[metric].pct*1.2}`).join(' ');
    return `<svg class="breadth-trend" viewBox="0 0 ${width} 180" role="img" aria-label="最近30个交易日全市场MA20和MA50站上比例趋势">${[0,50,100].map(n => `<line x1="40" y1="${145-n*1.2}" x2="${right}" y2="${145-n*1.2}" stroke="#ddd"/><text x="3" y="${149-n*1.2}" font-size="11">${n}%</text>`).join('')}<polyline points="${line('ma20')}" fill="none" stroke="#bd3b43" stroke-width="2.5"/><polyline points="${line('ma50')}" fill="none" stroke="#246b91" stroke-width="2.5"/><text x="40" y="173" font-size="11">${esc(data.dates[0])}</text><text x="${right}" y="173" text-anchor="end" font-size="11">${esc(data.asOf)}</text></svg>`;
  }
  function table() {
    let rows = data.rows.filter(row => row.industry.includes(search));
    rows = [...rows].sort((a,b) => sort === 'name' ? a.industry.localeCompare(b.industry,'zh-CN') : (b.series.at(-1)[period].pct ?? -1)-(a.series.at(-1)[period].pct ?? -1));
    const all = [{industry:'全市场', series:data.market}, ...rows];
    root.querySelector('.breadth-scroll').innerHTML = `<table class="breadth-table"><thead><tr><th>行业 / 日期</th>${data.dates.slice(-span).map(d=>`<th>${esc(d.slice(5))}</th>`).join('')}</tr></thead><tbody>${all.map(row=>`<tr><th scope="row">${esc(row.industry)}</th>${row.series.slice(-span).map(s=>{const m=s[period];return `<td style="background:${color(m.pct)};color:${m.pct!=null&&(m.pct<20||m.pct>=80)?'#fff':'#222'}"><button data-industry="${esc(row.industry)}" data-date="${s.date}" title="${esc(row.industry)} ${s.date} ${period.toUpperCase()}：${pct(m.pct)}；${m.above}/${m.valid}只" aria-label="${esc(row.industry)} ${s.date} ${pct(m.pct)}">${m.pct==null?'—':m.pct.toFixed(0)}</button></td>`;}).join('')}</tr>`).join('')}</tbody></table>`;
    root.querySelector('.breadth-scroll').scrollLeft = 99999;
  }
  function render(cached=false) {
    const latest=data.market.at(-1), old=data.market.at(-6), delta=old ? latest.ma20.pct-old.ma20.pct : null;
    const age=(Date.now()-new Date(data.asOf+'T15:00:00+08:00'))/86400000;
    root.innerHTML = `<div class="breadth-head"><h2>全市场收盘宽度</h2><span class="breadth-note">${esc(data.asOf)} 收盘 · ${cached?'沿用上次快照':'已保存快照'}${age>4?' · 数据已滞后，等待更新':''}</span></div><div class="breadth-stats">${[
      ['MA20 站上比例',pct(latest.ma20.pct),`${latest.ma20.above} / ${latest.ma20.valid} 只`],
      ['MA50 站上比例',pct(latest.ma50.pct),`${latest.ma50.above} / ${latest.ma50.valid} 只`],
      ['MA20 较5交易日前',delta==null?'—':`${delta>0?'+':''}${delta.toFixed(1)} 点`,'百分点变化'],
      ['收盘上涨比例',pct(latest.upPct),`${latest.up}涨 / ${latest.down}跌 / ${latest.flat}平`]
    ].map(([label,value,note])=>`<div class="breadth-stat"><span class="breadth-note">${label}</span><strong>${value}</strong><span class="breadth-note">${note}</span></div>`).join('')}</div><div class="breadth-legend"><span><i style="background:#bd3b43"></i>MA20</span><span><i style="background:#246b91"></i>MA50</span><span>全市场等权站上比例</span></div>${trend()}<div class="breadth-controls"><label>均线<select id="breadth-period"><option value="ma20">MA20</option><option value="ma50">MA50</option></select></label><label>区间<select id="breadth-span"><option value="30">30个交易日</option><option value="20">20个交易日</option><option value="10">10个交易日</option></select></label><label>行业<input id="breadth-search" type="search" placeholder="搜索行业"></label><label>排序<select id="breadth-sort"><option value="strength">最新宽度从高到低</option><option value="name">行业名称</option></select></label></div><div class="breadth-legend">${['0–20%','20–40%','40–60%','60–80%','80–100%'].map((s,i)=>`<span><i style="background:${color(i*20+1)}"></i>${s}</span>`).join('')}<span>灰色空格：数据不足</span></div><div class="breadth-scroll" tabindex="0" aria-label="行业市场宽度热力图"></div><p class="breadth-note">沪深京 ${data.universeCount} 只 · 同日历史覆盖 ${data.latestHistoryCount} 只（${data.coveragePct}%） · ${data.rows.length} 个行业 · ${esc(data.source)}</p><details class="breadth-note"><summary>计算口径与数据范围</summary><p>${esc(data.method)}</p><p>收盘后更新；未取得当天收盘数据时显示最近可用交易日。宽度为参与程度，不能独立确定买点。采集时间：${esc(data.generatedAt)}</p></details><dialog class="breadth-detail"><button aria-label="关闭详情">×</button><div></div></dialog>`;
    for (const [id,value] of [['period',period],['span',span],['search',search],['sort',sort]]) root.querySelector('#breadth-'+id).value=value;
    root.querySelector('#breadth-period').onchange=e=>{period=e.target.value;table();};
    root.querySelector('#breadth-span').onchange=e=>{span=Number(e.target.value);table();};
    root.querySelector('#breadth-search').oninput=e=>{search=e.target.value.trim();table();};
    root.querySelector('#breadth-sort').onchange=e=>{sort=e.target.value;table();};
    const dialog=root.querySelector('dialog');
    dialog.querySelector('button').onclick=()=>dialog.close();
    root.querySelector('.breadth-scroll').onclick=e=>{
      const b=e.target.closest('button[data-date]'); if(!b)return;
      const series=b.dataset.industry==='全市场'?data.market:data.rows.find(r=>r.industry===b.dataset.industry).series;
      const s=series.find(r=>r.date===b.dataset.date), m=s[period];
      dialog.querySelector('div').innerHTML=`<h3>${esc(b.dataset.industry)}</h3><p>${s.date} 收盘 · ${period.toUpperCase()}</p><p>站上比例 ${pct(m.pct)}</p><p>站上 ${m.above} 只 / 有效均线样本 ${m.valid} 只</p><p>当日成交样本 ${s.n} 只；历史不足 ${s.n-m.valid} 只。</p>`;
      dialog.showModal();
    };
    table();
  }
  async function load() {
    try {
      const response=await fetch('/market-breadth.json',{cache:'no-store'});
      if(!response.ok)throw Error('fetch');
      const next=await response.json(); if(!valid(next))throw Error('coverage');
      if(data && next.asOf<data.asOf)throw Error('older');
      data=next; render(); try{localStorage.setItem(cacheKey,JSON.stringify(data));}catch{}
    } catch {
      if(data)render(true); else root.textContent='市场宽度快照暂不可用，等待收盘数据更新。';
    }
  }
  try{const saved=JSON.parse(localStorage.getItem(cacheKey));if(valid(saved)){data=saved;render(true);}}catch{}
  load(); setInterval(load,1800000);
  new ResizeObserver(() => { if(data && root.querySelector('.breadth-trend')) root.querySelector('.breadth-trend').outerHTML=trend(); }).observe(root);
  document.getElementById('refreshBtn').addEventListener('click',load);
})();
