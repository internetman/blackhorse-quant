/* Independent review shortlist. Never turns an imported watchlist into a fresh signal. */
(function (root) {
  'use strict';
  function validDate(x) { return typeof x === 'string' && /^\d{4}-\d{2}-\d{2}$/.test(x) && new Date(x+'T00:00:00Z').toISOString().slice(0,10) === x; }
  function model(data, expected, isArchived = () => false) {
    if (!data || data.schemaVersion !== 1 || !validDate(data.asOfDate) || !Array.isArray(data.candidates)) throw new Error('候选格式或数据日期无效');
    const seen = new Set();
    const candidates = data.candidates.filter(c => {
      if (!c || !/^\d{6}$/.test(c.code) || seen.has(c.code) || isArchived(c.code) || c.asOfDate !== data.asOfDate) return false;
      seen.add(c.code); return true;
    });
    const label = data.mode === 'replay' ? '历史试跑 · 非今日名单' : data.mode !== 'close' ? '运行口径待核 · 非确认名单' : !expected ? '新鲜度待核' : data.asOfDate < expected ? '数据滞后 · 非最新名单' : data.asOfDate > expected ? '收盘日期待核' : '最新完整收盘候选 · 待人工复盘';
    return {data,candidates,label};
  }
  function node(tag, text, cls) {
    const el = document.createElement(tag); if (text != null) el.textContent = String(text); if (cls) el.className = cls; return el;
  }
  function render(host, state) {
    host.replaceChildren();
    const heading = document.getElementById('dailyCandidateTitle');
    if (heading) heading.textContent = `每日候选 · ${state.data.asOfDate}`;
    host.append(node('p',state.label,'daily-status'));
    const d = state.data, u = d.universe || {};
    host.append(node('p',`行情截至 ${d.asOfDate} · 来源：${d.source || '待核'} · ${u.scope || '范围待核'} · 有效 ${u.valid ?? '—'} / ${u.total ?? '—'}（${u.coveragePct ?? '—'}%）`,'daily-meta'));
    host.append(node('p','展示本次所有规则入围候选；仅供人工复盘，不代表确认突破或交易指令。原导入记录单独保留为历史与备用。手动归档按股票代码持续生效，换日期不会自动恢复，需在归档箱手动恢复。','daily-meta'));
    if (Array.isArray(d.limitations) && d.limitations.length) host.append(node('p',d.limitations.join('；'),'daily-warning'));
    const grid = node('div',null,'daily-grid');
    for (const c of state.candidates) {
      const card = node('article',null,'daily-card');
      card.append(node('h3',`${c.name || ''} ${c.code}`));
      // This first-release panel never promotes automatic confirmation flags.
      card.append(node('p',`${c.stage || '阶段待核'} · ${c.position || '位置待核'} · 待核`,'daily-status'));
      card.append(node('p',`数据日 ${c.asOfDate}`,'daily-meta'));
      if (Array.isArray(c.reasons)) card.append(node('p',c.reasons.join('；')));
      const checks = Array.isArray(c.pendingChecks) ? c.pendingChecks : [];
      card.append(node('p',`人工复核：${checks.length ? checks.join('；') : '复权、形态、量能及重大事件'}`,'daily-warning'));
      grid.append(card);
    }
    if (!state.candidates.length) grid.append(node('p','本次没有可展示候选，不使用旧名单补足。'));
    host.append(grid);
  }
  async function boot() {
    const host = document.getElementById('dailyCandidateContent'); if (!host) return;
    try {
      const [response, cal] = await Promise.all([fetch('/m2-daily-candidates.json',{cache:'no-store'}), fetch('/market-trading-calendar.json',{cache:'no-store'}).then(r => r.ok ? r.json() : null).catch(()=>null)]);
      if (!response.ok) throw new Error('尚未发布候选结果');
      const data = await response.json();
      root.MarketWeather?.setCalendar(cal);
      const refresh = () => render(host,model(data,root.MarketWeather?.expectedCloseDate() || null,code => Boolean(root.M2Archive?.isArchived(code))));
      refresh();
      root.M2Archive?.subscribe(refresh);
    } catch (_) { host.replaceChildren(node('p','每日候选尚未就绪或读取失败；下方股票足迹是原导入记录，不是本次新筛选结果。','daily-warning')); }
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {model};
  if (typeof document !== 'undefined') boot();
})(typeof window !== 'undefined' ? window : globalThis);
