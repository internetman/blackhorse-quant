(() => {
  const root = document.getElementById('market-breadth');
  const cacheKey = 'heimaq:all-market-breadth:v1';
  const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct = value => value == null ? '—' : `${Number(value).toFixed(1)}%`;
  const color = value => value == null ? '#eee' : value < 20 ? '#16836a' : value < 40 ? '#a9d5c3' : value < 60 ? '#edf0f0' : value < 80 ? '#f0b3a5' : '#bd3b43';
  let archive = null, archiveReadPromise = null, heatmapCalendar = null, chartMode = 'all';
  const archiveLabel = '历史归档（截至 11 月 12 日）';
  let data, liveParticipation, activeRefresh, refreshQueued = false, attempt = null, midday = null, middayReadFailed = false, period = 'ma20', span = 30, search = '', sort = 'strength';
  const point = value => value == null ? '—' : `${value > 0 ? '+' : ''}${value.toFixed(1)} 个百分点`;
  const fraction = m => m.pct==null ? '未取得该项数据' : m.valid==null ? '上游聚合值，未提供分子分母' : `${m.above} / ${m.valid} 只`;
  function validMidday(d) {
    if(d?.schemaVersion!==1 || d.scopeVersion!=='qfq-shsz-midday-v1' || d.session!=='midday' || d.barStatus!=='intraday' || d.coveragePct<95 || d.universeCount<4000 || d.latestHistoryCount/d.universeCount<.95 || !/^\d{4}-\d{2}-\d{2}$/.test(d.asOf) || !(d.previousCloseDate<d.asOf) || d.membershipDate!==d.previousCloseDate || !Array.isArray(d.rows) || d.rows.length<50 || d.rows.some(r=>!r || typeof r.industry!=='string') || ![d.coveragePct,d.universeCount,d.latestHistoryCount].every(Number.isFinite))return false;
    const stamp=value=>{if(typeof value!=='string' || !/(?:Z|[+-]\d{2}:\d{2})$/.test(value))return false;const t=new Date(value);if(!Number.isFinite(t.getTime()))return false;const b=new Date(t.getTime()+8*3600000).toISOString();return b.slice(0,10)===d.asOf && b.slice(11,16)>='11:30' && b.slice(11,16)<'13:00';};
    return stamp(d.observedAt) && stamp(d.generatedAt) && ['ma20','ma50'].every(k=>{const m=d.market?.[k];return m && [m.valid,m.above,m.pct].every(Number.isFinite) && m.valid/d.universeCount>=.95 && m.above>=0 && m.above<=m.valid && Math.abs(m.pct-100*m.above/m.valid)<=.011;});
  }
  function middayPanel() {
    if(!validMidday(midday))return '';
    const today=new Date(Date.now()+8*3600000).toISOString().slice(0,10);
    const label=midday.asOf===today ? data.asOf>=midday.asOf?'当日午盘回看':'今日午盘参考' : '历史午盘参考';
    const m=midday.market;
    return `<section class="participation-panel midday-panel" aria-label="午盘市场宽度参考"><div class="breadth-head"><h3>${label} · 非收盘确认</h3><span class="breadth-note">${esc(midday.asOf)} · 报价 ${esc(midday.observedAt)} · 计算完成 ${esc(midday.generatedAt)}</span></div>${middayReadFailed?'<p class="breadth-note">最新午盘文件读取失败，以下保留上次读取值，请核对日期。</p>':''}<div class="breadth-stats">${[
      ['午盘动态 MA20',pct(m.ma20.pct),fraction(m.ma20)],
      ['午盘动态 MA50',pct(m.ma50.pct),fraction(m.ma50)],
      ['午盘上涨比例',pct(m.upPct),`${m.up}涨 / ${m.down}跌 / ${m.flat}平`],
      ['同日有效覆盖',pct(midday.coveragePct),`${midday.latestHistoryCount} / ${midday.universeCount}只沪深股票`]
    ].map(([label,value,note])=>`<div class="breadth-stat"><span class="breadth-note">${label}</span><strong>${value}</strong><span class="breadth-note">${note}</span></div>`).join('')}</div><p class="breadth-note">前19/49个完整收盘价 + 当日午休价；独立于下方收盘趋势与天气，不作为收盘确认。行业名单日期：${esc(midday.membershipDate)}。<a href="/market-breadth-midday.json" download>下载午盘原始数据</a></p><details class="breadth-note"><summary>午盘行业宽度与计算口径</summary>${midday.rows.map(r=>`<p>${esc(r.industry)} · MA20 ${pct(r.ma20?.pct)} · MA50 ${pct(r.ma50?.pct)}</p>`).join('')}<p>${esc(midday.method)}</p></details></section>`;
  }
  function participation() {
    const p=liveParticipation || data.participation;
    if(!p)return '';
    return `<section class="participation-panel" aria-label="最新市场涨跌参与度"><div class="breadth-head"><h3>最新市场参与度</h3><span class="breadth-note">${esc(p.asOf)} ${p.barStatus==='intraday'?'盘中报价':'报价'} · 报价时间 ${esc(p.updatedAt)} · beta大盘云图</span></div><div class="breadth-stats">${[
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
      <details class="weather-method"><summary>5个指数的MA50确认明细</summary>${(data.benchmarks || []).length ? data.benchmarks.map(i=>`<p>${esc(i.name)} · ${esc(i.asOf || '缺日期')} · 收盘 ${esc(i.close ?? '—')} · MA50 ${esc(i.ma50 ?? '—')} · MA50近20日 ${pct(i.ma50Slope20)} · ${esc(i.provider || '来源未标记')}</p>`).join('') : '<p>指数日K未完整取得，不能视为通过。</p>'}</details>${!w.fresh.usable?`<p class="weather-stale">历史快照当时的分类：${esc(w.observed.label)}，不代表今天。最新采集：${esc(attempt?.attemptedAt || '没有运行记录')} ${attempt?.error?`· ${esc(attempt.error)}`:''}</p>`:''}
      <details class="weather-method"><summary>天气如何判定 / 仓位边界</summary><p>这是独立、未回测的观察分类：MA20或MA50站上比例低于30%为偏弱，低位五日改善标记修复；两项均≥50%、行业半数以上宽度≥50%、MA20五日不下降为扩散；扩散持续3日且MA20≥60%、MA50≥55%，至少3/5个指数站上上行的MA50，并有行业符合R02门槛，才标记顺风。</p><p>指数：上证、沪深300、中证1000、创业板、科创50。R02门槛：最新≥85且5日均≥80；或最新≥90且3日均≥80；或最新与5日均均≥70。缺失不算通过。</p><p>20%–30% / 40%–50% / 60%引用现行R05的防守、结构性行情、顺风环境参考上限；实际仓位仍取账户约束、个股买点及风险限制中的更严格值。红灯不新开仓，不用宽度替代止损。</p><p>盘中不提前写入收盘结论。应有收盘日按北京时间16:00和交易所年度休市安排计算；日历缺失或年份未核实时暂停判断，不按调休工作日冒充交易日。</p></details>
    </section>`;
  }
  function valid(d) { return d?.schemaVersion === 1 && (d.coveragePct >= 95 || d.dataMode==='public-aggregates' && d.participation?.n>=4000) && d.market?.length && d.rows?.length; }
  function validArchive(d) {
    if(!valid(d) || d.scopeVersion!=='qfq-shsz-ffd-experimental-v1' || d.asOf!=='2026-11-12' || !Array.isArray(d.dates) || !d.dates.length || !Array.isArray(d.market) || !Array.isArray(d.rows))return false;
    const dates=d.dates;
    if(dates.at(-1)!==d.asOf || dates.some((date,i)=>!/^\d{4}-\d{2}-\d{2}$/.test(date) || i>0 && date<=dates[i-1]))return false;
    const aligned=series=>Array.isArray(series) && series.length===dates.length && series.every((row,i)=>row && row.date===dates[i] && ['ma20','ma50'].every(key=>row[key] && (row[key].pct===null || Number.isFinite(row[key].pct) && row[key].pct>=0 && row[key].pct<=100)));
    return aligned(d.market) && d.rows.every(row=>row && typeof row.industry==='string' && aligned(row.series));
  }
  // Historical cells are displayed alongside current cells, never fed into
  // the current line chart, market weather, rankings, or browser snapshot cache.
  function sourceSnapshot(source) { return source==='archive'?archive:source==='current'?data:null; }
  function heatmapColumns() {
    const current=data.dates.map(date=>({date,source:'current'}));
    if(chartMode==='current' || !archive)return current;
    if(chartMode==='archive')return archive.dates.map(date=>({date,source:'archive'}));
    const first=data.dates[0], older=archive.dates.filter(date=>date<first).map(date=>({date,source:'archive'}));
    const gaps=[];
    if(older.length) {
      const cursor=new Date(older.at(-1).date+'T00:00:00Z');
      for(let i=0;i<370;i++) {
        cursor.setUTCDate(cursor.getUTCDate()+1);
        const date=cursor.toISOString().slice(0,10);if(date>=first)break;
        const entry=heatmapCalendar?.years?.[date.slice(0,4)];
        if(entry && ![0,6].includes(cursor.getUTCDay()) && !entry.closures.some(([a,b])=>a<=date && date<=b))gaps.push({date,source:'gap'});
      }
    }
    return [...older,...gaps,...current];
  }
  function visibleColumns() { const columns=heatmapColumns();return span>0?columns.slice(-span):columns; }
  function chartContext() {
    const columns=visibleColumns(), archived=chartMode==='archive', combined=chartMode==='all';
    const range=`${columns[0]?.date} 至 ${columns.at(-1)?.date} · 实际显示 ${columns.length} 个日期`;
    return `<strong>${combined?'全部日期 · 按来源分段':archived?archiveLabel:'当前口径'}</strong><span>${esc(range)}</span><p>${combined?(archive?'历史归档与当前口径按列分组；中间缺失交易日留灰，不跨口径计算。':'先显示当前数据；历史归档读取后自动补入图表。'):archived?'旧来源：腾讯 / 东方财富日线，含 FFD 试验补源。':'当前已核验收盘快照。'} 折线与上方市场天气始终采用当前快照（截至 ${esc(data.asOf)}）。</p>${archive && chartMode!=='current'?`<p>归档灰格为原始缺失；旧全市场行仅 11 月 11–12 日有效。 <a href="/market-breadth-archive.json" download>下载历史归档</a></p>`:''}`;
  }
  function updateHeatmap() {
    if(!data || !root.querySelector('#breadth-chart-context') || !root.querySelector('.breadth-scroll'))return;
    root.querySelector('#breadth-chart-context').innerHTML=chartContext();
    const view=chartMode==='archive' && archive?archive:data;
    root.querySelector('#breadth-scope-note').textContent=view.dataMode==='public-aggregates'
      ? `${view.rows.length}个行业MA20聚合值 · beta有效报价${view.participation.n}只 · 未取得全市场均线分母，不推算覆盖率`
      : `${view.universeLabel || '沪深京'} ${view.universeCount} 只 · 同日历史覆盖 ${view.latestHistoryCount} 只（${view.coveragePct}%） · ${view.rows.length} 个行业${view.excludedMarkets?.length?' · 北交所未覆盖':''} · ${view.source}`;
    root.querySelector('#breadth-chart-method').innerHTML=`<summary>计算口径与数据范围</summary><p>当前：${esc(data.method)} · 采集 ${esc(data.generatedAt)}</p>${archive && chartMode!=='current'?`<p>历史归档：${esc(archive.method)} · 采集 ${esc(archive.generatedAt)}</p>`:''}<p>同名行业分别展示各来源原值；不拼接全市场曲线，不以灰格推算数据。宽度不能独立确定买点。</p>`;
    table();
  }
  function updatePeriodPicker() {
    const partial=data.availableMetrics && !data.availableMetrics.includes('ma50');
    const archiveMA50=archive?.availableMetrics?.includes('ma50') && chartMode!=='current';
    if(partial && !archiveMA50)period='ma20';
    const select=root.querySelector('#breadth-period');if(!select)return;
    const ma50=select.querySelector('option[value="ma50"]');
    select.value=period;ma50.disabled=Boolean(partial && !archiveMA50);ma50.textContent=ma50.disabled?'MA50（数据未完整取得）':'MA50';
  }
  function updateCharts() {
    const partial=data.availableMetrics && !data.availableMetrics.includes('ma50');
    updatePeriodPicker();
    root.querySelector('.breadth-trend').outerHTML=trend();
    root.querySelector('.breadth-legend span:last-child').textContent=`${data.universeLabel || '全市场'}等权站上比例 · 当前口径`;
    root.querySelector('.breadth-legend span:nth-child(2)').innerHTML=`<i style="background:#246b91"></i>${partial?'MA50（当前未完整取得）':'MA50'}`;
    updateHeatmap();
  }
  function trend() {
    const width=Math.max(280,root.clientWidth),right=width-12,rows=span>0?data.market.slice(-span):data.market;
    const lines=(metric,stroke)=>{
      const segments=[];let points=[];
      rows.forEach((row,i)=>{if(row[metric]?.pct==null){if(points.length)segments.push(points);points=[];}else points.push(`${40+i/Math.max(1,rows.length-1)*(right-40)},${145-row[metric].pct*1.2}`);});
      if(points.length)segments.push(points);
      return segments.map(points=>`<polyline points="${points.join(' ')}" fill="none" stroke="${stroke}" stroke-width="2.5"/>`).join('');
    };
    return `<svg class="breadth-trend" viewBox="0 0 ${width} 180" role="img" aria-label="当前口径最近${rows.length}个交易日${esc(data.universeLabel || '全市场')}均线站上比例趋势">${[0,50,100].map(n=>`<line x1="40" y1="${145-n*1.2}" x2="${right}" y2="${145-n*1.2}" stroke="#ddd"/><text x="3" y="${149-n*1.2}" font-size="11">${n}%</text>`).join('')}${lines('ma20','#bd3b43')}${lines('ma50','#246b91')}<text x="40" y="173" font-size="11">${esc(rows[0]?.date)}</text><text x="${right}" y="173" text-anchor="end" font-size="11">${esc(data.asOf)}</text></svg>`;
  }
  function table() {
    const columns=visibleColumns(), sources=chartMode==='archive' && archive?[archive]:chartMode==='all' && archive?[data,archive]:[data];
    const names=[...new Set(sources.flatMap(source=>source.rows.map(row=>row.industry)))].filter(name=>name.includes(search));
    const sortSource=chartMode==='archive' && archive?archive:data;
    const strength=name=>sortSource.rows.find(row=>row.industry===name)?.series.at(-1)?.[period]?.pct ?? -1;
    names.sort((a,b)=>sort==='name'?a.localeCompare(b,'zh-CN'):strength(b)-strength(a));
    const groups=[];
    columns.forEach(column=>{const group=groups.at(-1);if(group?.source===column.source)group.count++;else groups.push({source:column.source,count:1});});
    const labels={archive:'历史归档 · 腾讯/东财 + FFD 试验补源',gap:'缺少已核验数据',current:'当前口径 · 日线收益率复权'};
    const rows=[{name:data.universeLabel || '全市场',market:true},...names.map(name=>({name,market:false}))];
    root.querySelector('.breadth-scroll').innerHTML=`<table class="breadth-table"><thead><tr class="breadth-source-row"><th>来源 / 口径</th>${groups.map(group=>`<th class="breadth-source-${group.source}" data-source="${group.source}" colspan="${group.count}">${esc(labels[group.source])}</th>`).join('')}</tr><tr class="breadth-date-row"><th>行业 / 日期</th>${columns.map((column,i)=>`<th data-date="${column.date}" data-source="${column.source}" class="${i>0 && column.source!==columns[i-1].source?'breadth-scope-boundary':''}">${esc(column.date.slice(5))}</th>`).join('')}</tr></thead><tbody>${rows.map(row=>`<tr><th scope="row">${esc(row.name)}</th>${columns.map((column,i)=>{
      const source=sourceSnapshot(column.source),series=row.market?source?.market:source?.rows.find(item=>item.industry===row.name)?.series;
      const value=series?.find(item=>item.date===column.date),metric=value?.[period] || {pct:null};
      const title=`${row.name} ${column.date} ${labels[column.source]} ${period.toUpperCase()}：${pct(metric.pct)}；${column.source==='gap'?'未取得已核验快照':fraction(metric)}`;
      return `<td data-source="${column.source}" class="${column.source==='gap'?'breadth-gap ':''}${i>0 && column.source!==columns[i-1].source?'breadth-scope-boundary':''}" style="background:${color(metric.pct)};color:${metric.pct!=null&&(metric.pct<20||metric.pct>=80)?'#fff':'#222'}"><button data-industry="${esc(row.name)}" data-market="${row.market}" data-date="${column.date}" data-source="${column.source}" title="${esc(title)}" aria-label="${esc(title)}">${metric.pct==null?'—':metric.pct.toFixed(0)}</button></td>`;
    }).join('')}</tr>`).join('')}</tbody></table>`;
    root.querySelector('.breadth-scroll').scrollLeft=99999;
  }
  function render(cached=false) {
    const latest=data.market.at(-1), old=data.market.at(-6), delta=old?.ma20.pct!=null && latest.ma20.pct!=null ? latest.ma20.pct-old.ma20.pct : null;
    const fresh=window.MarketWeather.freshness(data,new Date(),attempt);
    const partial=data.availableMetrics && !data.availableMetrics.includes('ma50');
    root.innerHTML = `<div class="breadth-head"><h2>市场天气与市场宽度</h2><div><span class="breadth-note">${esc(data.asOf)} 收盘 · ${cached?'沿用上次快照':'已保存快照'} · ${fresh.usable?(partial?'MA20数据有效；MA50缺失':'数据有效'):'数据待更新'}</span> ${data.dataMode==='public-aggregates'?'':'<a class="breadth-download" href="/market-breadth.json" download>下载当前服务端正式快照</a>'}</div></div><p class="weather-stale" data-history-policy="incremental-only">${data.dataMode==='public-aggregates'?'正式收盘宽度暂不可用。以下为行业备用数据，不能作为全市场收盘确认。':`正式收盘宽度截至 ${esc(data.asOf)}；若未取得当日正式数据，保留已核验快照，不计作当日更新。`} 独立午盘观察和市场涨跌参与度按各自日期显示。</p>${middayPanel()}${participation()}${weather()}<div class="breadth-stats">${[
      [`${data.universeLabel || '全市场'} MA20站上比例`,pct(latest.ma20.pct),fraction(latest.ma20)],
      ['MA50 站上比例',pct(latest.ma50.pct),partial?'当前MA50未完整取得，不使用旧值':fraction(latest.ma50)],
      ['MA20 较5交易日前',delta==null?'—':`${delta>0?'+':''}${delta.toFixed(1)} 点`,'百分点变化'],
      ['收盘上涨比例',pct(latest.upPct),`${latest.up}涨 / ${latest.down}跌 / ${latest.flat}平`]
    ].map(([label,value,note])=>`<div class="breadth-stat"><span class="breadth-note">${label}</span><strong>${value}</strong><span class="breadth-note">${note}</span></div>`).join('')}</div><div class="breadth-legend"><span><i style="background:#bd3b43"></i>MA20</span><span><i style="background:#246b91"></i>MA50</span><span>全市场等权站上比例</span></div><div class="breadth-controls"><label>数据范围<select id="breadth-dataset"><option value="all">全部日期（默认）</option><option value="current">当前口径（${data.dates.length} 个交易日）</option><option value="archive" ${archive?'':'disabled'}>${archiveLabel}${archive?` · ${archive.dates.length} 个交易日`:' · 暂未取得'}</option></select></label><label>均线<select id="breadth-period"><option value="ma20">MA20</option><option value="ma50">MA50</option></select></label><label>区间<select id="breadth-span"><option value="30">30个交易日</option><option value="20">20个交易日</option><option value="10">10个交易日</option><option value="0">全部日期</option></select></label><label>行业<input id="breadth-search" type="search" placeholder="搜索行业"></label><label>排序<select id="breadth-sort"><option value="strength">最新宽度从高到低</option><option value="name">行业名称</option></select></label></div><div id="breadth-chart-context" class="breadth-chart-context" aria-live="polite">${chartContext()}</div>${trend()}<div class="breadth-legend">${['0–20%','20–40%','40–60%','60–80%','80–100%'].map((s,i)=>`<span><i style="background:${color(i*20+1)}"></i>${s}</span>`).join('')}<span>灰色空格：数据不足</span></div><div class="breadth-scroll" tabindex="0" aria-label="行业市场宽度热力图"></div><p id="breadth-scope-note" class="breadth-note">沪深京 ${data.universeCount} 只 · 同日历史覆盖 ${data.latestHistoryCount} 只（${data.coveragePct}%） · ${data.rows.length} 个行业 · ${esc(data.source)}</p><details id="breadth-chart-method" class="breadth-note"><summary>计算口径与数据范围</summary><p>${esc(data.method)}</p><p>收盘后更新；未取得当天收盘数据时显示最近可用交易日。宽度为参与程度，不能独立确定买点。采集时间：${esc(data.generatedAt)}</p></details><dialog class="breadth-detail"><button aria-label="关闭详情">×</button><div></div></dialog>`;
    for (const [id,value] of [['period',period],['span',span],['search',search],['sort',sort]]) root.querySelector('#breadth-'+id).value=value;
    if(data.dataMode==='public-aggregates'){
      root.querySelector('.breadth-head .breadth-note').textContent=`${data.asOf} 行业MA20 · 在线备用模式 · 全市场均线待逐股校验`;
      const notes=[...root.querySelectorAll('p.breadth-note')];
      const coverage=notes.find(p=>p.textContent.includes('同日历史覆盖'));
      if(coverage)coverage.textContent=`${data.rows.length}个行业MA20聚合值 · beta有效报价${data.participation.n}只 · 未取得全市场均线分母，不推算覆盖率`;
    }
    root.querySelector('#breadth-dataset').value=chartMode;
    root.querySelector('#breadth-dataset').onchange=e=>{chartMode=e.target.value==='archive' && archive?'archive':e.target.value==='current'?'current':'all';updateCharts();};
    root.querySelector('#breadth-period').onchange=e=>{period=e.target.value;updateCharts();};
    root.querySelector('#breadth-span').onchange=e=>{span=Number(e.target.value);updateCharts();};
    root.querySelector('#breadth-search').oninput=e=>{search=e.target.value.trim();table();};
    root.querySelector('#breadth-sort').onchange=e=>{sort=e.target.value;table();};
    const dialog=root.querySelector('dialog');
    dialog.querySelector('button').onclick=()=>dialog.close();
    root.querySelector('.breadth-scroll').onclick=e=>{
      const b=e.target.closest('button[data-date]'); if(!b)return;
      const source=b.dataset.source,view=sourceSnapshot(source);
      const series=b.dataset.market==='true'?view?.market:view?.rows.find(r=>r.industry===b.dataset.industry)?.series;
      const row=series?.find(r=>r.date===b.dataset.date),metric=row?.[period] || {pct:null};
      const label=source==='archive'?archiveLabel:source==='gap'?'缺少已核验数据':'当前口径';
      dialog.querySelector('div').innerHTML=`<h3>${esc(b.dataset.industry)}</h3><p>${label} · ${esc(b.dataset.date)} · ${period.toUpperCase()}</p><p>站上比例 ${pct(metric.pct)}</p><p>${source==='gap'?'该交易日没有已核验快照，保留灰格。':esc(fraction(metric))}</p>${metric.valid!=null?`<p>当日有效行情样本 ${row.n} 只；均线不足 ${row.n-metric.valid} 只。</p>`:''}`;
      dialog.showModal();
    };
    updateCharts();
  }
  const partialSnapshot = value => value.dataMode === 'public-aggregates';
  function preferSnapshot(next, current) {
    if(!current)return true;
    if(partialSnapshot(next)!==partialSnapshot(current))return !partialSnapshot(next);
    if(next.asOf!==current.asOf)return next.asOf>current.asOf;
    return (Date.parse(next.generatedAt)||0)>=(Date.parse(current.generatedAt)||0);
  }
  function rememberParticipation(p) {
    if(!p || !Number.isFinite(Date.parse(p.updatedAt)))return;
    if(!liveParticipation || Date.parse(p.updatedAt)>=Date.parse(liveParticipation.updatedAt))liveParticipation=p;
  }
  function loadArchive() {
    // The optional historical file must never block the current snapshot.
    // A verified archive is immutable here; retry only a failed first read.
    if(archive)return Promise.resolve(archive);
    if(archiveReadPromise)return archiveReadPromise;
    archiveReadPromise=(async()=>{
      try {
        const response=await fetch('/market-breadth-archive.json',{cache:'no-store',signal:AbortSignal.timeout(10000)});
        if(!response.ok)throw Error('archive');
        const value=await response.json();if(!validArchive(value))throw Error('archive validation');
        archive=value;
        const option=root.querySelector('#breadth-dataset option[value="archive"]');
        if(option){option.disabled=false;option.textContent=`${archiveLabel} · ${archive.dates.length} 个交易日`;}
        if(data && chartMode==='all'){updatePeriodPicker();updateHeatmap();}
      } catch { /* Retry this optional read on the next refresh. */ }
      finally { archiveReadPromise=null; }
    })();
    return archiveReadPromise;
  }
  async function refresh() {
    void loadArchive();
    try {
      await Promise.allSettled([
        (async()=>{try{const r=await fetch('/market-breadth-midday.json',{cache:'no-store',signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error('midday');const j=await r.json();if(!validMidday(j))throw Error('midday validation');midday=j;middayReadFailed=false;}catch{middayReadFailed=true;}})(),
        (async()=>{const r=await fetch('/market-trading-calendar.json',{cache:'no-store',signal:AbortSignal.timeout(10000)});if(!r.ok)throw Error('calendar');heatmapCalendar=await r.json();window.MarketWeather.setCalendar(heatmapCalendar);})(),
        (async()=>{const r=await fetch('/market-breadth-status.json',{cache:'no-store',signal:AbortSignal.timeout(10000)});if(r.ok){const j=await r.json();const t=Date.parse(j.attemptedAt);
          if(Number.isFinite(t) && (!attempt || t>Date.parse(attempt.attemptedAt) ||
            t===Date.parse(attempt.attemptedAt) && j.status==='failed'))attempt=j;}})()
      ]);
      let currentSnapshot;
      const reads=await Promise.allSettled(['/market-breadth.json','/api/public-market'].map(async url=>{
        const response=await fetch(url,{cache:'no-store',signal:AbortSignal.timeout(20000)});
        if(!response.ok)throw Error('fetch');
        const value=await response.json();if(!valid(value))throw Error('coverage');
        rememberParticipation(value.participation);
        if(preferSnapshot(value,data)) {
          data=value;
          currentSnapshot=value;
          try{localStorage.setItem(cacheKey,JSON.stringify(data));}catch{}
        }
        if(data)render(data!==currentSnapshot);
        return value;
      }));
      if(!reads.some(r=>r.status==='fulfilled'))throw Error('coverage');
    } catch {
      if(data)render(true); else root.textContent='市场宽度快照暂不可用，等待收盘数据更新。';
    }
  }
  function load() {
    if(activeRefresh){refreshQueued=true;return activeRefresh;}
    activeRefresh=(async()=>{
      try {
        do { refreshQueued=false; await refresh(); } while(refreshQueued);
      } finally { activeRefresh=null; }
    })();
    return activeRefresh;
  }
  try{const saved=JSON.parse(localStorage.getItem(cacheKey));if(valid(saved)){rememberParticipation(saved.participation);data=saved;render(true);}}catch{}
  load(); setInterval(load,1800000);
  new ResizeObserver(() => { if(data && root.querySelector('.breadth-trend')) root.querySelector('.breadth-trend').outerHTML=trend(); }).observe(root);
  document.getElementById('refreshBtn')?.addEventListener('click',load);
})();
