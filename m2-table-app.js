(function () {
  const data = window.M2_TABLE_DATA;
  if (!data) return;

  const $ = (id) => document.getElementById(id);
  const pct = (value) => {
    if (!Number.isFinite(Number(value))) return "—";
    const n = Number(value);
    return `${n >= 0 ? "+" : "−"}${Math.abs(n).toFixed(1)}%`;
  };
  const price = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(2) : "—";
  const amountYi = (value) => Number.isFinite(Number(value)) ? (Number(value) / 100000000).toFixed(1) : "—";
  const count = (value) => Number.isFinite(Number(value)) ? Number(value).toLocaleString("zh-CN") : "—";
  const clamp = (value, min, max) => Math.min(max, Math.max(min, value));
  const bareCode = (value) => String(value || "").split(".")[0];
  const finite = (value) => (value === null || value === undefined || value === "") ? null : (Number.isFinite(Number(value)) ? Number(value) : null);
  const formatPivot = (value) => Number.isFinite(Number(value)) ? Number(value).toFixed(2) : "待确认";
  const pivotDistance = (row, pivot) => {
    const current = finite(row.price);
    if (current === null || !pivot) return "—";
    const distance = (pivot - current) / current * 100;
    if (Math.abs(distance) < 0.01) return "已到上沿";
    return distance > 0 ? `距上沿 +${distance.toFixed(1)}%` : `已越过 ${Math.abs(distance).toFixed(1)}%`;
  };
  const derivePivot = (history) => {
    const rows = (history?.rows || []).filter((item) => finite(item.high) !== null);
    if (!rows.length) return null;
    const contractionWindows = (history.metrics?.contractions || [])
      .map((item) => Number(item.window))
      .filter((value) => Number.isFinite(value) && value >= 5);
    const lookback = contractionWindows.length ? Math.min(...contractionWindows) : (rows.length >= 20 ? 20 : rows.length);
    const sample = rows.slice(-lookback);
    const highRow = sample.reduce((best, item) => finite(item.high) > finite(best.high) ? item : best, sample[0]);
    const pivot = finite(highRow.high);
    if (pivot === null) return null;
    return { price: pivot, date: highRow.date || "", lookback };
  };
  const applySnapshotPivot = (payload) => {
    const history = payload.history || {};
    data.rows.forEach((row) => {
      const itemHistory = history[bareCode(row.code)] || history[row.code];
      const pivot = derivePivot(itemHistory);
      if (!pivot) return;
      row.pivotPrice = pivot.price;
      row.pivot = formatPivot(pivot.price);
      row.pivotStatus = `${pivot.lookback}日参考买点`;
      row.pivotDistance = pivotDistance(row, pivot.price);
      row.pivotReason = `参考 Pivot 买点取最近 ${pivot.lookback} 日最高价 ${row.pivot}（${pivot.date}）；收盘突破并明显放量才算触发。`;
      const countValue = itemHistory?.metrics?.contractionCount;
      if (Number.isFinite(Number(countValue))) row.contractions = `${countValue} 次`;
      row.dataQuality = `${row.pivotStatus}已补；仍缺 RS 与人工图形确认`;
    });
  };

  $("tableAsOf").textContent = `导入快照 ${data.asOf}`;
  $("tableSource").textContent = data.source;
  $("summaryTotal").textContent = data.rowCount;
  $("summaryStacked").textContent = data.currentQualifiedCount || data.rows.filter((row) => row.currentQualified).length;
  $("summaryAbove200").textContent = data.newSinceClose || 0;
  $("summaryNearHigh").textContent = data.carryForwardCount || 0;
  $("summaryUp").textContent = data.rows.filter((row) => row.pct > 0).length;

  const renderAnalysis = () => {
    const nearHigh = data.rows.filter((row) => row.fromHighPct >= -10).length;
    const confirmed = data.rows.filter((row) => row.pivot && row.pivot !== "待确认" && row.contractions && row.contractions !== "待确认").length;
    $("flowTotal").textContent = data.priorCloseQualified || "—";
    $("flowStacked").textContent = data.importedCount || "—";
    $("flowAbove200").textContent = data.currentQualifiedCount || "—";
    $("flowNearHigh").textContent = data.newSinceClose || 0;
    $("flowPriority").textContent = data.rowCount;
    $("flowConfirmed").textContent = data.rowCount - confirmed;

    const adviceRows = [
      { label: "待观察", key: "wait", color: "wait" },
      { label: "过热不追，保留观察", key: "caution", color: "caution" },
      { label: "待复核观察", key: "review", color: "review" },
    ].map((item) => ({ ...item, value: data.rows.filter((row) => row.recommendationClass === item.key).length }));
    const maxAdvice = Math.max(1, ...adviceRows.map((item) => item.value));
    $("adviceChart").innerHTML = adviceRows.map((item) => `
      <div class="bar-row"><span>${item.label}</span><div class="bar-track"><i class="${item.color}" style="width:${Math.max(4, item.value / maxAdvice * 100)}%"></i></div><strong>${item.value}</strong></div>
    `).join("");

    const highRows = data.rows.filter((row) => Number.isFinite(Number(row.fromHighPct))).sort((a, b) => b.fromHighPct - a.fromHighPct).slice(0, 7);
    $("highChart").innerHTML = highRows.map((row) => {
      const position = clamp(100 + Number(row.fromHighPct), 3, 100);
      return `<div class="bar-row"><span>${row.name}</span><div class="bar-track"><i class="near" style="width:${position}%"></i></div><strong>${pct(row.fromHighPct)}</strong></div>`;
    }).join("");

    const maRows = data.rows.filter((row) => Number.isFinite(Number(row.priceToMa200Pct))).sort((a, b) => b.priceToMa200Pct - a.priceToMa200Pct).slice(0, 7);
    const maxMa = Math.max(1, ...maRows.map((row) => Number(row.priceToMa200Pct)));
    $("maChart").innerHTML = maRows.map((row) => `
      <div class="bar-row"><span>${row.name}</span><div class="bar-track"><i class="ma" style="width:${clamp(Number(row.priceToMa200Pct) / maxMa * 100, 4, 100)}%"></i></div><strong>${pct(row.priceToMa200Pct)}</strong></div>
    `).join("");
  };

  renderAnalysis();

  const getRows = () => {
    const query = $("tableSearch").value.trim().toLowerCase();
    const filter = $("tableFilter").value;
    const sort = $("tableSort").value;
    const rows = data.rows.filter((row) => {
      const matchesSearch = !query || `${row.code} ${row.name}`.toLowerCase().includes(query);
      const matchesFilter = filter === "all"
        || (filter === "stacked" && row.maStacked)
        || (filter === "nearHigh" && row.fromHighPct >= -10)
        || (filter === "caution" && row.recommendationClass === "caution")
        || (filter === "wait" && row.recommendationClass === "wait")
        || (filter === "review" && row.recommendationClass === "review")
        || filter === "needsPivot";
      return matchesSearch && matchesFilter;
    });
    const valueOf = (row) => ({
      pct: row.pct,
      fromHigh: row.fromHighPct,
      fromLow: row.fromLowPct,
      amount: row.avgAmount,
      price: row.price,
    }[sort]);
    return rows.sort((a, b) => Number(valueOf(b) ?? -Infinity) - Number(valueOf(a) ?? -Infinity));
  };

  const render = () => {
    const rows = getRows();
    $("visibleCount").textContent = rows.length;
    $("tableBody").innerHTML = rows.map((row, index) => `
      <tr>
        <td>${String(index + 1).padStart(2, "0")}</td>
        <td class="sticky-name name-cell"><strong>${row.name}</strong><small>${row.code} · ${row.exchange}</small></td>
        <td class="advice-cell ${row.recommendationClass}" title="${row.recommendationReason}"><strong>${row.recommendation}</strong><small>${row.recommendationReason}</small></td>
        <td>${price(row.price)}</td>
        <td class="${row.pct >= 0 ? "pct-up" : "pct-down"}">${pct(row.pct)}</td>
        <td>${price(row.ma50)}</td>
        <td>${price(row.ma150)}</td>
        <td>${price(row.ma200)}</td>
        <td class="${row.maStacked && row.aboveMa50 ? "ma-pass" : "ma-warn"}">${row.maStacked && row.aboveMa50 ? "多头通过" : "待复核"}</td>
        <td class="derived-cell"><strong>高于 MA200 ${pct(row.priceToMa200Pct)}</strong><small>MA50→150 ${pct(row.ma50ToMa150Pct)} · MA150→200 ${pct(row.ma150ToMa200Pct)}</small></td>
        <td class="stage-cell ${row.stageInference === "阶段 2 初筛通过" ? "stage-pass" : "stage-pending"}"><strong>${row.stageInference}</strong><small>${row.periodPct > 0 ? "阶段涨幅为正" : "阶段涨幅待复核"}</small></td>
        <td class="${row.periodPct >= 0 ? "pct-up" : "pct-down"}">${pct(row.periodPct)}</td>
        <td class="${row.fromHighPct >= -10 ? "near-high" : ""}">${pct(row.fromHighPct)}</td>
        <td>${pct(row.fromLowPct)}</td>
        <td>${count(row.avgAmount)}</td>
        <td>${amountYi(row.marketCap)}</td>
        <td class="trend-pending">${row.ma200Slope || "待复核"}</td>
        <td class="data-warning" title="${row.dataQuality || ""}">${row.dataQuality || "—"}</td>
        <td class="${row.pivotPrice ? "pivot-ready" : "pivot-pending"}" title="${row.pivotReason || ""}"><strong>${row.pivot}</strong><small>${row.pivotStatus || "待确认"} · ${row.pivotDistance || "—"}</small></td>
        <td class="contraction-pending">${row.contractions}</td>
      </tr>
    `).join("");
  };

  ["tableSearch", "tableFilter", "tableSort"].forEach((id) => $(id).addEventListener("input", render));
  render();

  const syncSnapshot = async () => {
    try {
      const response = await fetch(`/m2-snapshot.json?ts=${Date.now()}`, { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      applySnapshotPivot(await response.json());
      renderAnalysis();
      render();
    } catch (error) {
      console.warn("M2 table pivot snapshot failed", error);
    }
  };
  syncSnapshot();
})();
