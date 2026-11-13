/* Independent frozen-membership observation, never an index/MA50 replacement. */
(async function(){
  const root=document.getElementById('sector-observation'); if(!root)return;
  const esc=x=>String(x??'—').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
  const pct=x=>typeof x==='number'&&Number.isFinite(x)?`${x.toFixed(2)}%`:'—（覆盖不足）';
  try{
    const response=await fetch('/sector-observation.json',{cache:'no-store'});if(!response.ok)throw Error('尚未发布');
    const d=await response.json();
    if(d.scopeVersion!=='ffd-frozen-industry-midday-observation-v1'||!d.publishable||d.candidateOnly!==false||d.publicationApproved!==true||d.market.valid/d.universeCount<.95)throw Error('未通过95%完整性保护');
    const today=new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Shanghai',year:'numeric',month:'2-digit',day:'2-digit'}).format(new Date());
    const stale=d.asOf!==today;
    const rows=list=>list.map(r=>`<tr><td>${esc(r.industry)}</td><td>${pct(r.meanChangePct)}</td><td>${pct(r.medianChangePct)}</td><td>${pct(r.upPct)} / ${pct(r.downPct)} / ${pct(r.flatPct)}</td><td>${r.valid}/${r.expected}；缺${r.missing}；零量${r.zeroVolumeCount}</td><td>${esc(r.sourceTimeMin)} → ${esc(r.sourceTimeMax)}</td><td>${(r.top3||[]).map(s=>`${esc(s.name||s.code)} (${esc(s.code)}) ${pct(s.changeRatio)}`).join('<br>')||'—'}</td></tr>`).join('');
    const table=list=>`<div class="so-scroll"><table><thead><tr><th>行业</th><th>等权平均涨跌</th><th>中位数</th><th>涨/跌/平比例</th><th>报价覆盖/缺口</th><th>源时间范围</th><th>本次前三</th></tr></thead><tbody>${rows(list)}</tbody></table></div>`;
    root.innerHTML=`<h2>冻结行业名单 · 午休涨跌观察</h2><p>${stale?'历史观察，非今日行情。':''}午休固定观察，非实时刷新。数据日期 ${esc(d.asOf)}；名单 ${esc(d.membershipDate)}。${esc(d.source)}</p><p>有效 ${d.market.valid}/${d.universeCount}，行业 ${d.industryCount}；源时间 ${esc(d.market.sourceTimeMin)} → ${esc(d.market.sourceTimeMax)}。不同批次，不是11:30精确截点。</p><p class="so-warning">非东财板块指数、非MA50、非多日趋势。保持原板块榜与宽度不变；行业不足95%留空。</p><h3>按原生涨跌幅等权均值 Top15</h3>${table(d.top15)}<details><summary>全部 ${d.industryCount} 行业覆盖与领涨样本</summary>${table(d.industries)}</details><p>${esc(d.method)}</p><p>${(d.limitations||[]).map(esc).join('；')}</p>`;
  }catch(e){root.textContent='冻结行业午休观察暂不可用；不影响原板块榜或宽度。';}
})();
