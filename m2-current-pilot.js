/* Four-sector review pilot: never supplies the official daily feed. */
(function (root) {
  'use strict';
  const SCOPE = 'four-sector-close-v1';
  const SECTORS = new Set(['半导体','消费电子','光伏设备','电子化学品']);
  const DATE = /^\d{4}-\d{2}-\d{2}$/;
  function eligibleCount(part) {
    return Number.isInteger(part?.valid) && Number.isInteger(part.total) &&
      part.total > 0 && part.valid <= part.total && part.valid * 100 >= part.total * 95;
  }
  function model(payload, expected, isArchived = () => false) {
    if (!payload || !DATE.test(expected || '') || payload.asOfDate !== expected ||
        payload.schemaVersion !== 1 || payload.mode !== 'derived-pilot' ||
        payload.runStatus !== 'success' || payload.barStatus !== 'completed') return null;
    const u = payload.universe, sectors = u?.sectors;
    if (u?.scopeId !== SCOPE || !eligibleCount(u) || !Array.isArray(sectors) ||
        sectors.length !== SECTORS.size || new Set(sectors.map(s => s?.name)).size !== SECTORS.size ||
        !sectors.every(s => SECTORS.has(s?.name) && eligibleCount(s)) ||
        sectors.reduce((sum,s) => sum+s.valid,0) !== u.valid ||
        sectors.reduce((sum,s) => sum+s.total,0) !== u.total) return null;
    const c = payload.candidates;
    if (!Array.isArray(c) || c.length !== payload.candidateCount || c.length > u.valid ||
        !c.every(x => x && typeof x.code === 'string' && /^\d{6}$/.test(x.code) &&
          x.asOfDate === expected && typeof x.name === 'string' && x.name.trim() &&
          x.stage === 'S2' && typeof x.position === 'string') ||
        new Set(c.map(x => x.code)).size !== c.length) return null;
    return {asOfDate:expected,valid:u.valid,total:u.total,sectors,candidateCount:c.length,
      candidates:c.filter(x => !isArchived(x.code)),
      limitations:Array.isArray(payload.limitations) ? payload.limitations.filter(v => typeof v === 'string') : []};
  }
  function node(tag,text,cls) {
    const e = document.createElement(tag);
    if (text != null) e.textContent = text;
    if (cls) e.className = cls;
    return e;
  }
  function render(host, state) {
    host.replaceChildren();
    host.hidden = !state;
    if (!state) return;
    host.append(node('h2',`${state.asOfDate} 收盘 · 四板块云端试跑`),
      node('p','仅四个板块的 S2 复盘候选，不代表全市场名单，也不是确认突破或买点。','daily-status'),
      node('p',`数据覆盖 ${state.valid} / ${state.total} · ${state.sectors.map(s=>`${s.name} ${s.valid}/${s.total}`).join('、')}`,'daily-meta'));
    if (state.limitations.length) host.append(node('p',state.limitations.join('；'),'daily-warning'));
    const grid = node('div',null,'daily-grid');
    for (const c of state.candidates) {
      const el = node('article',null,'daily-card');
      el.append(node('h3',`${c.name} ${c.code}`),node('p',`S2 · ${c.position} · 待核`,'daily-status'));
      if (Array.isArray(c.reasons)) el.append(node('p',c.reasons.filter(x=>typeof x==='string').join('；')));
      const checks = Array.isArray(c.pendingChecks) ? c.pendingChecks.filter(x=>typeof x==='string') : [];
      el.append(node('p',`人工复核：${checks.join('；') || '复权、形态、量能及重大事件'}`,'daily-warning'));
      grid.append(el);
    }
    if (!state.candidates.length) grid.append(node('p',state.candidateCount
      ? '本次候选均已归档。' : '本次四板块筛选完成，S2 候选为 0 只。'));
    host.append(grid);
  }
  async function boot() {
    const host = document.getElementById('currentDerivedPilot');
    if (!host) return;
    let inflight = false;
    let current = null;
    const refresh = () => render(host,model(current,
      root.MarketWeather?.expectedCloseDate(),code=>Boolean(root.M2Archive?.isArchived(code))));
    async function load() {
      if (inflight) return;
      inflight = true;
      try {
        const [r, c] = await Promise.all(['/m2-pilot-current.json','/market-trading-calendar.json']
          .map(path => fetch(path,{cache:'no-store',signal:AbortSignal.timeout(9000)})));
        if (!r.ok || !c.ok) { current = null; return; }
        root.MarketWeather?.setCalendar(await c.json());
        current = await r.json();
      } catch (_) {
        current = null;
      } finally {
        inflight = false;
        refresh();
      }
    }
    root.M2Archive?.subscribe(refresh);
    document.addEventListener('visibilitychange',() => { if (!document.hidden) load(); });
    root.setInterval(load,60000);
    await load();
  }
  if (typeof module !== 'undefined' && module.exports) module.exports = {model};
  if (typeof document !== 'undefined') boot();
})(typeof window !== 'undefined' ? window : globalThis);
