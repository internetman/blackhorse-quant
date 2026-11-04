"""Build an auditable A-share close breadth snapshot from public daily bars."""
from __future__ import annotations

import argparse
import concurrent.futures
import datetime as dt
import json
import math
import statistics
import subprocess
import time
import urllib.parse
import urllib.request
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
ZONE = dt.timezone(dt.timedelta(hours=8))
UNIVERSE = "m:0+t:6,m:0+t:80,m:1+t:2,m:1+t:23,m:0+t:81+s:2048"


def fetch(url, attempts=3, timeout=8):
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0", "Referer": "https://quote.eastmoney.com/"})
    for attempt in range(attempts):
        try:
            # curl honours the workstation's network route more reliably than
            # urllib's CONNECT tunnel; never interpolate a URL into shell text.
            try:
                result = subprocess.run([
                    "curl", "--fail", "--silent", "--show-error", "--location",
                    "--max-time", str(timeout), "--user-agent", "Mozilla/5.0",
                    "--referer", "https://quote.eastmoney.com/", url,
                ], capture_output=True, text=True, timeout=timeout+2, check=True)
                return json.loads(result.stdout)
            except FileNotFoundError:
                with urllib.request.urlopen(request, timeout=timeout) as response:
                    return json.load(response)
        except Exception:
            if attempt == attempts-1:
                raise
            time.sleep(0.5 * (attempt + 1))


def universe():
    def page(n):
        query = urllib.parse.urlencode(dict(pn=n, pz=100, po=1, np=1, fltt=2, invt=2, fid="f12", fs=UNIVERSE, fields="f2,f3,f12,f13,f14,f100,f124"))
        last_error = None
        for host in ('push2delay.eastmoney.com', 'push2.eastmoney.com'):
            try:
                return fetch('https://'+host+'/api/qt/clist/get?'+query, attempts=1, timeout=6)['data']
            except Exception as exc:
                last_error = exc
        raise ValueError(f'Universe page {n} failed on both providers: {type(last_error).__name__}')
    first = page(1)
    rows = first["diff"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        for data in pool.map(page, range(2, math.ceil(first["total"] / 100) + 1)):
            if data["total"] != first["total"]:
                raise ValueError("Universe changed during pagination; retry later")
            rows.extend(data["diff"])
    unique = {str(x["f13"]) + "." + x["f12"]: x for x in rows}
    if len(unique) != first["total"] or len(unique) < 4000:
        raise ValueError("Incomplete all-market universe")
    # The upstream list also includes delisted shells with no price or industry.
    listed = {k: v for k, v in unique.items() if isinstance(v.get("f2"), (int, float)) and v["f2"] > 0 and v.get("f100") not in (None, "", "-")}
    if len(listed) < 4000:
        raise ValueError("Listed universe is unexpectedly small")
    return [{"secid": k, "code": v["f12"], "name": v["f14"], "industry": v["f100"]} for k, v in listed.items()]


def bars(stock, cutoff, cache):
    path = cache / (stock["secid"] + ".json")
    if path.exists():
        saved = json.loads(path.read_text())
        if saved.get("cutoff") == cutoff:
            return saved["bars"]
    query = urllib.parse.urlencode(dict(secid=stock["secid"], klt=101, fqt=1, lmt=100, end=cutoff.replace("-", ""), fields1="f1,f2,f3,f4,f5,f6", fields2="f51,f52,f53,f54,f55,f56,f57,f58,f59,f60,f61"))
    data = {}
    for host in ("push2his.eastmoney.com", "push2delay.eastmoney.com"):
        try:
            data = fetch("https://" + host + "/api/qt/stock/kline/get?" + query, attempts=1, timeout=4).get("data") or {}
            if data.get("klines"):
                break
        except Exception:
            continue
    result = []
    if data.get("code") and str(data["code"]) != stock["code"]:
        raise ValueError("Daily bars returned the wrong security")
    for line in data.get("klines", []):
        values = line.split(",")
        date, close, volume, pct = values[0], float(values[2]), float(values[5]), float(values[8])
        if date <= cutoff and close > 0 and all(math.isfinite(x) for x in [close, volume, pct]):
            result.append({"date": date, "close": close, "volume": volume, "pct": pct})
    if not result and not stock["code"].startswith(("4", "8", "9")):
        symbol = ("sh" if stock["secid"].startswith("1.") else "sz") + stock["code"]
        begin = (dt.date.fromisoformat(cutoff)-dt.timedelta(days=220)).isoformat()
        url = "https://proxy.finance.qq.com/ifzqgtimg/appstock/app/fqkline/get?" + urllib.parse.urlencode({"param": f"{symbol},day,{begin},{cutoff},150,qfq"})
        node = (fetch(url, attempts=2).get("data") or {}).get(symbol) or {}
        raw = node.get("qfqday") or node.get("day") or []
        previous = None
        for row in raw:
            close, volume = float(row[2]), float(row[5])
            if previous and row[0] <= cutoff and close > 0 and all(math.isfinite(x) for x in (close, volume)):
                result.append(dict(date=row[0], close=close, volume=volume, pct=round((close/previous-1)*100, 2), source="Tencent"))
            previous = close
    if not result:
        raise ValueError("No valid daily bars from available providers")
    if len({x["date"] for x in result}) != len(result):
        raise ValueError("Duplicate daily bars")
    result.sort(key=lambda x: x["date"])
    path.write_text(json.dumps({"cutoff": cutoff, "bars": result}))
    return result


def summarize(samples):
    def ratio(period):
        valid = [x for x in samples if x.get("ma" + str(period)) is not None]
        above = sum(x["close"] > x["ma" + str(period)] for x in valid)
        return {"pct": round(above / len(valid) * 100, 2) if valid else None, "above": above, "valid": len(valid)}
    changes = sorted(x["pct"] for x in samples)
    n = len(changes)
    up, down = sum(x > 0 for x in changes), sum(x < 0 for x in changes)
    return {"n": n, "up": up, "down": down, "flat": n-up-down,
            "upPct": round(up/n*100, 2) if n else None,
            "downPct": round(down/n*100, 2) if n else None,
            "median": round(statistics.median(changes), 2) if n else None,
            "mean": round(statistics.mean(changes), 2) if n else None,
            "p25": changes[int((n-1)*0.25)] if n else None,
            "p75": changes[int((n-1)*0.75)] if n else None,
            "ma20": ratio(20), "ma50": ratio(50)}


def calculate(stocks, histories, cutoff):
    if not stocks or not histories:
        raise ValueError("No valid all-market history; preserving previous snapshot")
    latest_counts = Counter(rows[-1]["date"] for rows in histories.values() if rows)
    latest = latest_counts.most_common(1)[0][0]
    if latest_counts[latest] / len(stocks) < 0.95:
        raise ValueError("Latest-date history coverage below 95%; preserving previous snapshot")
    if (dt.date.fromisoformat(cutoff)-dt.date.fromisoformat(latest)).days > 14:
        raise ValueError("Source daily bars are stale")
    by_date = defaultdict(list)
    for stock in stocks:
        rows = histories.get(stock["secid"], [])
        for i, row in enumerate(rows):
            # Zero-volume days do not count as actively traded market participation.
            if row["date"] > latest or row["volume"] <= 0:
                continue
            sample = dict(row, industry=stock["industry"])
            for period in (20, 50):
                sample["ma"+str(period)] = statistics.mean(x["close"] for x in rows[i-period+1:i+1]) if i+1 >= period else None
            by_date[row["date"]].append(sample)
    dates = sorted(by_date)[-30:]
    market = [dict(date=date, **summarize(by_date[date])) for date in dates]
    sectors = []
    for industry in sorted({x["industry"] for x in stocks}):
        series = [dict(date=date, **summarize([x for x in by_date[date] if x["industry"] == industry])) for date in dates]
        values = [x["ma20"]["pct"] for x in series]
        recent = values[-5:]
        prior = values[-10:-5]
        valid_recent = len(recent) == 5 and all(x is not None for x in recent)
        valid_prior = len(prior) == 5 and all(x is not None for x in prior)
        sectors.append({"industry": industry, "series": series, "latest": values[-1],
                        "avg5": round(statistics.mean(recent), 2) if valid_recent else None,
                        "slope5": round(statistics.mean(recent)-statistics.mean(prior), 2) if valid_recent and valid_prior else None,
                        "days70": sum(x is not None and x >= 70 for x in values),
                        "daysTotal": sum(x is not None for x in values), "isCurrentR02": False})
    sectors.sort(key=lambda x: x["latest"] if x["latest"] is not None else -1, reverse=True)
    return {"schemaVersion": 1, "asOf": latest, "dateStart": dates[0], "dateEnd": latest,
            "generatedAt": dt.datetime.now(ZONE).isoformat(timespec="seconds"), "barStatus": "completed",
            "source": "东方财富沪深京A股名单及前复权日K；腾讯前复权日K备用，本地计算",
            "method": "股票池取当前有有效报价及行业分类的沪深京A股，排除无报价的退市/未上市记录。收盘价严格大于MA20/MA50；当日有成交且具备足够历史的个股等权计数。含ST和北交所，剔除当日无成交及历史不足样本。行业采用当前东方财富分类回溯，历史存在存续样本偏差。",
            "universeCount": len(stocks), "historyCount": len(histories),
            "providerCounts": dict(Counter(rows[-1].get("source", "Eastmoney") for rows in histories.values() if rows)),
            "latestHistoryCount": latest_counts[latest], "coveragePct": round(latest_counts[latest]/len(stocks)*100, 2),
            "missing": [x["code"] for x in stocks if x["secid"] not in histories],
            "dates": dates, "market": market, "rows": sectors}


def benchmark_snapshot(cutoff, cache):
    specs = [("1.000001", "上证指数"), ("1.000300", "沪深300"),
             ("1.000852", "中证1000"), ("0.399006", "创业板指"), ("1.000688", "科创50")]
    def one(spec):
        secid, name = spec
        try:
            rows = bars(dict(secid=secid, code=secid.split('.')[1]), cutoff, cache)
            closes = [x['close'] for x in rows]
            if len(closes) < 70:
                raise ValueError('指数历史不足70日')
            avg = statistics.mean(closes[-50:])
            prior = statistics.mean(closes[-70:-20])
            return dict(secid=secid, name=name, asOf=rows[-1]['date'], close=closes[-1],
                        ma50=round(avg, 4), ma50Slope20=round((avg/prior-1)*100, 4))
        except Exception as exc:
            return dict(secid=secid, name=name, asOf=None, close=None, ma50=None, ma50Slope20=None, error=str(exc)[:160])
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        return list(pool.map(one, specs))


def atomic_json(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, ensure_ascii=False, separators=(',', ':')))
    temp.replace(path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--output", type=Path, default=ROOT/"market-breadth.json")
    parser.add_argument("--cutoff", help="可复现的收盘日期，不能晚于最近允许的完整收盘日")
    args = parser.parse_args()
    now = dt.datetime.now(ZONE)
    allowed = now.date() if now.hour >= 16 else now.date()-dt.timedelta(days=1)
    cutoff = args.cutoff or allowed.isoformat()
    if dt.date.fromisoformat(cutoff) > allowed:
        raise ValueError('Refusing incomplete/future close date')
    status_path = args.output.with_name(args.output.stem+'-status.json')
    attempted = now.isoformat(timespec='seconds')
    atomic_json(status_path, dict(status='running', attemptedAt=attempted, requestedCutoff=cutoff))
    cache = ROOT/"output"/"breadth-cache"
    cache.mkdir(parents=True, exist_ok=True)
    stocks = universe()
    benchmarks = benchmark_snapshot(cutoff, cache)
    calendar_dates = [x['asOf'] for x in benchmarks if x.get('asOf')]
    expected = max(calendar_dates) if calendar_dates else cutoff
    print(f"universe={len(stocks)} cutoff={cutoff}", flush=True)
    histories, failures = {}, []
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
        jobs = {pool.submit(bars, stock, cutoff, cache): stock for stock in stocks}
        for done, future in enumerate(concurrent.futures.as_completed(jobs), 1):
            stock = jobs[future]
            try:
                histories[stock["secid"]] = future.result()
            except Exception as exc:
                failures.append({"code": stock["code"], "error": str(exc)[:160]})
                if len(failures) <= 5:
                    print(f"missing {stock['code']}: {str(exc)[:120]}", flush=True)
            if done % 300 == 0:
                print(f"history={done}/{len(stocks)} failures={len(failures)}", flush=True)
            if len(failures) > len(stocks)*0.05:
                for job in jobs:
                    job.cancel()
                raise ValueError('全市场历史行情缺失超过5%，保留上次成功快照；暂停加仓判断')
    (cache/"failures.json").write_text(json.dumps(failures, ensure_ascii=False))
    result = calculate(stocks, histories, cutoff)
    if result['asOf'] != expected:
        raise ValueError(f"History date {result['asOf']} does not match expected close {expected}")
    result['benchmarks'] = benchmarks
    result['expectedCloseDate'] = expected
    if args.output.exists() and json.loads(args.output.read_text()).get("asOf", "") > result["asOf"]:
        raise ValueError("Refusing to regress snapshot date")
    atomic_json(args.output, result)
    atomic_json(status_path, dict(status='success', attemptedAt=attempted, completedAt=dt.datetime.now(ZONE).isoformat(timespec='seconds'), asOf=result['asOf'], coveragePct=result['coveragePct']))
    print(json.dumps({k: result[k] for k in ["asOf", "universeCount", "historyCount", "coveragePct"]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        # The old successful snapshot must remain intact; expose the failed run.
        parser_output = ROOT/'market-breadth.json'
        import sys
        if '--output' in sys.argv:
            parser_output = Path(sys.argv[sys.argv.index('--output')+1])
        status_path = parser_output.with_name(parser_output.stem+'-status.json')
        previous = json.loads(status_path.read_text()) if status_path.exists() else {}
        atomic_json(status_path, dict(status='failed', attemptedAt=previous.get('attemptedAt', dt.datetime.now(ZONE).isoformat(timespec='seconds')), error=str(exc)[:250]))
        raise
