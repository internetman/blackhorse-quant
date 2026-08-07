window.M2_DATA = {
  asOf: "2026-08-07 盘中行情",
  selectionAsOf: "2026-08-06 收盘",
  quoteGeneratedAt: "2026-08-07T10:37:13+08:00",
  market: {
    status: "🟡 震荡 / 分化",
    note: "观察池仍按 8-6 收盘维护；本次只更新 8-7 盘中报价。上涨增多时更要区分监控、买点和追高。",
    stats: [
      { label: "观察池", value: "45 只" },
      { label: "当前合格", value: "32 只" },
      { label: "盘中上涨", value: "24 只" },
      { label: "待复核保留", value: "13 只" }
    ]
  },
  decision: {
    title: "待观察股票池：45 只",
    text: "8-7 盘中已更新 45 只监控股报价，其中 24 只上涨。盘中强度只做监控，不把上涨直接等同于 B1/B2 买点。",
    nextFocus: "桐昆股份 / 金诚信",
    pivot: "未确认",
    distance: "—"
  },
  changes: [
    { time: "报价", text: "8-7 10:37 盘中报价已更新，45 只监控股全部取到东方财富实时行情。" },
    { time: "强度", text: "盘中上涨 24 只；涨幅靠前包括美迪西、凯莱英、创世纪、养元饮品、科伦药业。" },
    { time: "边界", text: "页面继续提供参考 Pivot 买点；只有收盘突破且明显放量才可能触发，盘中上涨不自动生成 B1/B2。" }
  ],
  candidates: [
    {
      code: "300628", name: "亿联网络", sector: "通信 / 历史档案", state: "未入选", stateClass: "review", stage: "历史档案",
      price: "—", change: "—", volume: "—", volumeLabel: "未出现在收盘表", pivot: "未确认", distance: "—",
      range: 20, pivotPrice: null, pivotStatus: "未入选", pivotReason: "8-5 收盘导入表未出现；保留历史档案，不据此判定形态失效。", stageReason: "本次未进入收盘初筛，不能把历史看板状态当作今日信号。", volumeRule: "等待新的收盘快照", advice: "继续观察", adviceClass: "wait", adviceReason: "等待重新进入导入表并补齐 RS、Pivot 与收缩证据。", action: "保留历史档案，等重新出现或结构数据更新。", note: "动态历史扫描：40日深度 20.93%，20日波动 18.82%，收缩次数 0；早盘与收盘名单变化不等于买点或失效。", baseAge: "40 个交易日", contractions: "0 次", contractionDetail: "VCP 收缩未确认；量能收缩比 1.31×", correction: "20.93%", chart: "m2-assets/亿联网络.jpg", priority: 1
    },
    {
      code: "601677", name: "明泰铝业", sector: "铝 / 有色", state: "趋势观察", stateClass: "watch", stage: "阶段 2 初筛",
      price: "17.17", change: "+1.00%", volume: "数据不足", volumeLabel: "收盘表无量比", pivot: "未确认", distance: "—",
      range: 42, pivotPrice: null, pivotStatus: "待确认", pivotReason: "当前导出没有 Pivot；不能把当天高点直接当 Pivot。", stageReason: "价格 > MA50 > MA150 > MA200，且位于 52 周高点 86.8%；仍需历史形态确认。", volumeRule: "突破日需明显放量", advice: "等待平台 / 突破", adviceClass: "wait", adviceReason: "先确认平台上沿、收缩次数和突破量，再判断是否进入买点。", action: "重点补历史 OHLCV，确认平台上沿与放量突破。", note: "MA50 +2.61%，20D +9.09%；动态扫描 40日深度16.11%、20日波动14.80%、收缩0次，趋势位置较好但未形成买点。", baseAge: "40 个交易日", contractions: "0 次", contractionDetail: "VCP 收缩未确认；量能收缩比 0.70×", correction: "16.11%", chart: "m2-assets/明泰铝业.jpg", priority: 2
    },
    {
      code: "002648", name: "卫星化学", sector: "化工材料 / 独立强势", state: "趋势观察", stateClass: "watch", stage: "阶段 2 初筛",
      price: "25.26", change: "+0.24%", volume: "数据不足", volumeLabel: "收盘表无量比", pivot: "未确认", distance: "—",
      range: 38, pivotPrice: null, pivotStatus: "待复核", pivotReason: "历史看板曾记录候选上沿，但本次收盘表没有 Pivot，需用动态历史数据复核。", stageReason: "价格 > MA50 > MA150 > MA200，且位于 52 周高点 84.6%；趋势初筛通过。", volumeRule: "突破日需明显放量", advice: "等待平台 / 突破", adviceClass: "wait", adviceReason: "先确认收缩和量能，不能把旧压力位直接当买点。", action: "重点补动态 VCP/Pivot，确认平台收紧后再看突破。", note: "MA50 +5.84%，20D +10.21%；动态扫描 20日/10日收缩共2次，量能收缩比0.72×，是当前 VCP 候选但仍未触发。", baseAge: "40 个交易日", contractions: "2 次", contractionDetail: "20日 14.78%、10日 9.08%；量能比 0.60× / 0.77×", correction: "21.26%", chart: "m2-assets/卫星化学.jpg", priority: 3
    },
    {
      code: "601872", name: "招商轮船", sector: "航运 / 主线共振", state: "不追", stateClass: "review", stage: "阶段 2 初筛",
      price: "18.10", change: "+7.87%", volume: "数据不足", volumeLabel: "收盘表无量比", pivot: "未确认", distance: "—",
      range: 24, pivotPrice: null, pivotStatus: "待复核", pivotReason: "原平台上沿需要用收盘后的历史 OHLCV 重画；今日上涨不能自动形成买点。", stageReason: "趋势初筛通过，且航运主线可观察；但今日单日涨幅过大，先不追。", volumeRule: "突破日需明显放量", advice: "不追当日大涨", adviceClass: "caution", adviceReason: "单日 +7.87%，距 MA50 +11.80%；等待缩量回踩或新平台。", action: "航运主线只作加分项；等待新平台、收缩和有效放量突破。", note: "20D +18.30%，52 周高点位置 82.6%；动态扫描 40日深度37.24%、20日波动24.20%、收缩1次，当前扩张明显。", baseAge: "40 个交易日", contractions: "1 次", contractionDetail: "20日波动24.20%；量能比 0.65×", correction: "37.24%", chart: "m2-assets/招商轮船.jpg", priority: 4
    },
    {
      code: "300750", name: "宁德时代", sector: "电池新能源 / 独立强势", state: "趋势观察", stateClass: "watch", stage: "阶段 2 初筛",
      price: "405.20", change: "+2.56%", volume: "数据不足", volumeLabel: "收盘表无量比", pivot: "未确认", distance: "—",
      range: 34, pivotPrice: null, pivotStatus: "压力区待复核", pivotReason: "400–410 只能先视为压力/观察区；本次收盘表没有 Pivot。", stageReason: "价格 > MA50 > MA150 > MA200，且位于 52 周高点 86.4%；底部与收缩仍需动态历史数据。", volumeRule: "突破日需明显放量", advice: "等待平台 / 突破", adviceClass: "wait", adviceReason: "趋势尚在但买点证据不完整；先重新定义紧平台，不把压力区当现成买点。", action: "等待更紧的平台、收缩和放量突破。", note: "MA50 +3.68%，20D +12.24%；动态扫描 40日深度16.39%、20日波动15.14%、收缩1次，趋势候选。", baseAge: "40 个交易日", contractions: "1 次", contractionDetail: "10日波动10.27%；量能比 0.84×", correction: "16.39%", chart: "m2-assets/宁德时代.jpg", priority: 5
    },
    {
      code: "000582", name: "北部湾港", sector: "港口航运 / 主线共振", state: "主线观察", stateClass: "mainline", stage: "阶段 2 初筛",
      price: "12.91", change: "+2.22%", volume: "数据不足", volumeLabel: "收盘表无量比", pivot: "未确认", distance: "—",
      range: 29, pivotPrice: null, pivotStatus: "待形成", pivotReason: "本次收盘表没有 Pivot；前高只能作参考，不能直接作为买点。", stageReason: "趋势初筛通过，主线标签可作加分项；但平台与收缩仍未确认。", volumeRule: "突破日需明显放量", advice: "等待平台 / 突破", adviceClass: "wait", adviceReason: "主线共振不能替代个股买点；等待新平台、收缩和量能确认。", action: "航运/港口主线继续观察，但不把前高直接当买点。", note: "MA50 +8.86%，20D +16.20%，52 周高点位置 83.5%；动态扫描 40日深度21.76%、20日波动17.62%、收缩1次，修复仍需控制。", baseAge: "40 个交易日", contractions: "1 次", contractionDetail: "40日波动21.76%；量能比 0.64×", correction: "21.76%", chart: "m2-assets/北部湾港.jpg", priority: 6
    }
  ]
};
