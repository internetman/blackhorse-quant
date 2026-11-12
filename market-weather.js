/* Transparent breadth observations. Environment ceilings are not order sizes. */
(function (global) {
  'use strict';
  function finite(x) { return typeof x === 'number' && Number.isFinite(x); }
  let calendar = null;
  function setCalendar(value) { calendar = value?.schemaVersion === 1 && value?.years ? value : null; }
  function tradingDay(day) {
    const entry = calendar?.years?.[day.slice(0,4)];
    if (!entry) return null;
    const date = new Date(day+'T00:00:00Z');
    return ![0,6].includes(date.getUTCDay()) && !entry.closures.some(([a,b])=>a<=day && day<=b);
  }
  function metric(row, key) { const m = row?.[key]; return m && finite(m.pct) && (m.valid > 0 || m.reported === true) ? m.pct : null; }
  function expectedCloseDate(now = new Date()) {
    const parts = Object.fromEntries(new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit', hour: '2-digit', hourCycle: 'h23'
    }).formatToParts(now).map(p => [p.type, p.value]));
    const date = new Date(`${parts.year}-${parts.month}-${parts.day}T00:00:00Z`);
    if (Number(parts.hour) < 16) date.setUTCDate(date.getUTCDate() - 1);
    for(let n=0;n<35;n++) {
      const day=date.toISOString().slice(0,10), open=tradingDay(day);
      if(open===null)return null;
      if(open)return day;
      date.setUTCDate(date.getUTCDate()-1);
    }
    return null;
  }
  function freshness(data, now = new Date(), attempt = null) {
    const expected = expectedCloseDate(now);
    // A date in the payload cannot prove that its update ran today.
    const latest = data?.market?.at(-1);
    const complete = data?.barStatus === 'completed' && data?.coveragePct >= 95 && latest?.date === data?.asOf;
    const stale = !expected || !data?.asOf || data.asOf < expected;
    const future = expected && data?.asOf > expected;
    const failed = attempt?.status === 'failed' && attempt.attemptedAt > (data?.generatedAt || '');
    return {expected, complete, stale, failed, usable: complete && !stale && !future && !failed,
      note: !expected ? '交易所日历缺失或年份未核实，暂停加仓判断' : !complete ? '同日数据不完整，暂停加仓判断' : future ? '快照日期超出完整收盘范围，暂停判断' : stale ? `数据滞后，实际截至 ${data.asOf}；应有收盘日 ${expected}` : failed ? '最近采集失败，暂停加仓判断' : '完整收盘快照；盘中涨幅不计入收盘信号'};
  }
  function evaluate(data, now = new Date(), attempt = null) {
    const market = data?.market || [], latest = market.at(-1), old = market.at(-6);
    const ma20 = metric(latest, 'ma20'), ma50 = metric(latest, 'ma50');
    const change20 = ma20 != null && metric(old, 'ma20') != null ? ma20 - metric(old, 'ma20') : null;
    const change50 = ma50 != null && metric(old, 'ma50') != null ? ma50 - metric(old, 'ma50') : null;
    const validSectors = (data?.rows || []).filter(s => s.series?.at(-1)?.date === data.asOf && metric(s.series.at(-1), 'ma20') != null);
    const above50Sectors = validSectors.filter(s => metric(s.series.at(-1), 'ma20') >= 50);
    const sectorPct = validSectors.length ? above50Sectors.length / validSectors.length * 100 : null;
    const mainSectors = validSectors.filter(s => {
      const a = s.series.slice(-5).map(r => metric(r, 'ma20'));
      const b = a.slice(-3);
      return a.length === 5 && a.every(finite) && ((a.at(-1) >= 85 && a.reduce((x,y)=>x+y,0)/5 >= 80) ||
        (a.at(-1) >= 90 && b.reduce((x,y)=>x+y,0)/3 >= 80) || (a.at(-1) >= 70 && a.reduce((x,y)=>x+y,0)/5 >= 70));
    });
    const indices = data?.benchmarks || [];
    const indexPass = indices.filter(i => i.asOf === data.asOf && finite(i.close) && finite(i.ma50) && i.close > i.ma50 && i.ma50Slope20 > 0);
    const indexIds = ['1.000001','1.000300','1.000852','0.399006','1.000688'];
    const indicesComplete = indices.length === 5 && indexIds.every(id => indices.some(i => i.secid === id)) && indices.every(i => i.asOf === data.asOf && finite(i.close) && i.close>0 && finite(i.ma50) && i.ma50>0 && finite(i.ma50Slope20));
    const expansionAt = pos => {
      if (pos < 5) return false;
      const r = market[pos], p = market[pos-5], a = metric(r,'ma20'), b = metric(r,'ma50');
      const sectors = (data.rows || []).map(s => s.series.find(v=>v.date===r.date)).filter(s=>metric(s,'ma20')!=null);
      return a != null && b != null && metric(p,'ma20') != null && a >= 50 && b >= 50 && a >= metric(p,'ma20') &&
        sectors.length > 0 && sectors.filter(s=>metric(s,'ma20')>=50).length/sectors.length >= .5;
    };
    const steady = market.length >= 8 && [market.length-3,market.length-2,market.length-1].every(expansionAt);
    let code = 'mixed', label = '分化', action = '保持选择性，等待低风险买点；不因单日普涨放大仓位。', ceiling = '40%–50% 环境参考上限';
    if (ma20 != null && ma50 == null) {
      code='partial'; label=change20>0?'短线改善 · 中期未确认':'中期趋势未确认';
      action='最新MA20与涨跌参与度已接通；当前接入数据尚无完整MA50，暂不能确认中期顺风或提高进攻仓位。'; ceiling='等待MA50与指数确认';
    } else if (ma20 == null || ma50 == null || change20 == null) {
      code='unknown'; label='数据不足'; action='缺少足够同日宽度和历史，暂停加仓判断。'; ceiling='暂停判断';
    } else if (ma20 < 30 || ma50 < 30) {
      if (change20 > 0) {code='repair'; label='低位修复'; action='宽度仍低，改善尚不足以扩大仓位；等待参与面持续恢复。';}
      else {code='weak'; label='偏弱'; action='优先防守，暂停扩大仓位；红灯或连续亏损时不新开仓。';}
      ceiling='20%–30% 防守参考上限';
    } else if (expansionAt(market.length-1)) {
      code='expansion'; label='扩散'; action='参与面改善，先验证买点；连续性、指数和主线仍需同时确认。';
      if (steady && ma20 >= 60 && ma50 >= 55 && indicesComplete && indexPass.length >= 3 && mainSectors.length) {
        code='favorable'; label='顺风'; action='宽度、指数和行业共振通过，可复核逐笔加仓条件；仍受账户风险和买点约束。'; ceiling='60% 环境参考上限';
      }
    } else if (change20 > 0 && ma50 < 50) {
      code='repair'; label='修复中'; action='短期改善，中期参与面尚未恢复；暂不进入进攻档。'; ceiling='20%–30% 防守参考上限';
    }
    const observed = {code,label,action,ceiling};
    const fresh=freshness(data,now,attempt);
    if (!fresh.usable) {code='unavailable'; label='等待有效更新'; action=fresh.note+'。旧图仅供回顾，不能作为当前加仓依据。'; ceiling='暂停加仓判断';}
    const gates = [
      {label:'收盘数据有效',passed:fresh.usable,detail:fresh.note},
      {label:'参与面扩散',passed:expansionAt(market.length-1),detail:`MA20≥50%、MA50≥50%，行业半数以上宽度≥50%，MA20五日不下降`},
      {label:'扩散持续3日',passed:steady,detail:'按连续3个实际交易日计算'},
      {label:'指数趋势确认',passed:indicesComplete ? indexPass.length>=3 : null,detail:indicesComplete ? `${indexPass.length}/5 个指数站上MA50且MA50上行` : '指数日K未完整取得，不能视为通过'},
      {label:'行业资格确认',passed:mainSectors.length>0,detail:`${mainSectors.length} 个行业符合当前R02数值门槛；需复核个股买点`}
    ];
    return {code,label,action,ceiling,observed,fresh,ma20,ma50,change20,change50,sectorPct,sectorAbove:above50Sectors.length,sectorValid:validSectors.length,mainSectors:mainSectors.map(s=>s.industry),gates};
  }
  const api={evaluate,freshness,expectedCloseDate,setCalendar};
  if(typeof module !== 'undefined' && module.exports)module.exports=api;
  global.MarketWeather=api;
})(typeof window !== 'undefined' ? window : globalThis);
