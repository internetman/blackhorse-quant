# Dated issuer status for four-sector M2

The private screening runner requires risk evidence dated to the **same
completed trading day** as the close. A display name, present-day roster, an
HTTP Date header, or an echoed date filter cannot establish historical
eligibility. Preserve independent date, scope, completeness and original-file
evidence. The original `.BJ` manifest member is retained as `BJ-unverified` outside the
supported evidence boards; it is not treated as a SH/SZ listing.
Missing coverage is `unknown`, not normal; a dated positive warning
may be `excluded` even while the rest of that venue remains unverified.

## Source checks (2026-11-17 Beijing)

- [SSE main-board risk disclosures](https://www.sse.com.cn/disclosure/listedinfo/riskplate/)
  and [separate STAR risk disclosures](https://www.sse.com.cn/disclosure/listedinfo/starriskplate/).
  The [official site client](https://www.sse.com.cn/xhtml/home/2021public/querySearch/search_listedCompanyInfo_2021.js)
  calls `commonSoaQuery.do` using `PL_SSGSXX_FXJSBGPLB` (main warning and
  arrangement) and `SSE_PL_SSGSXX_KCBFXTS_L` (separate STAR status).
  Observed result counts: 69 main warnings, 12 STAR warnings and 0 STAR
  arrangements; main arrangement request returned HTTP 503. Default
  `queryDate` was blank. Supplying 2026-11-16 or 2020-01-02 to the STAR warning
  query only echoed the supplied date while returning the identical 12-row
  result, so this is not a dated historical archive. An undated empty market
  tab is not a verified zero. Active [main and STAR listing tables](https://www.sse.com.cn/assortment/stock/list/share/)
  and [suspension/termination tables](https://www.sse.com.cn/assortment/stock/list/delisting/)
  are separate evidence needs.
- [SZSE risk disclosure](https://www.szse.cn/disclosure/listed/warn/index.html)
  identifies official report catalog `fxjsb`. Its [public report endpoint](https://www.szse.cn/api/report/ShowReport/data?SHOWTYPE=JSON&CATALOGID=fxjsb&TABKEY=tab1&PAGENO=1)
  returned the publisher date **2026-11-17**, 115 warnings over 6 pages.
  A historical-date filter trial still returned Nov 17. Its arrangement tab
  returned empty without a publisher date and cannot be treated as a complete
  dated zero. The [official active A-share list](https://www.szse.cn/market/product/stock/list/)
  uses catalog `1110`, tab 1, and publisher date Nov 17 (2,905 records / 146
  pages in the JSON response); today’s list cannot backfill yesterday.
- [SSE gateway date-coded instrument-file standard](https://big5.sse.com.cn/site/cht/www.sse.com.cn/services/tradingtech/development/c/10827383/files/4a5c0f16fef7493a81be3b5c420c1dab.pdf)
  and [SZSE instrument-file status specification notice](https://www.szse.cn/marketServices/technicalservice/notice/t20250627_614645.html)
  show that participant feeds can convey dated instrument status (SZSE status
  4 = ST, 5 = *ST for the rule described). Access to original Nov 16 files,
  historical completeness and license were not verified.
- [FFD PIT documentation](https://ffd.findesk.cn/api-docs/fund-flow) lists
  `GET /api/v1/pit/catalog` and
  `GET /api/v1/pit/security-name-status-history`. Unauthenticated catalog
  reached the service and returned HTTP 401. No live authenticated status or
  quota query was made. If evaluating FFD, verify entitlement and whether the
  actual contract covers **effective date, knowledge timestamp/version,
  all requested symbols and listing/risk/delisting**, not just name changes.
  A catalog “available”, an empty event list or a statement about point-in-time
  capability is not evidence of completeness or pricing.

At this checkpoint, these public sources did **not** reconstruct November 16
for all four market boards. A source-date-complete preserved official snapshot
or a qualified dated PIT feed is the next independent acceptance requirement.
Only after such a feed can an operator capture the next close without
assuming current pages are historically stable. Keep both the provenance
bundle and originals private.

## Offline validator and bridge

`m2_risk_snapshot.py` does not fetch data or approve its provenance. A reviewer
supplies a normalized evidence bundle keyed by `SH-main`, `SH-star`, `SZ-main`
and `SZ-gem`, each with separate roles `active`, `warning`, `arrangement` and
`delisted`. A reviewed role contains a list of exact exchange-qualified
`codes` plus `receipt` keys `source`, `sourceDate`, `board`, `role`,
`complete`, `sourceVersion`, `reviewedBy`, `recordCount`,
`originalArtifact` (simple private filename), and `originalArtifactSha256`.
When using saved native SZSE reports, the helper independently verifies that
the intended tab attests the exact target date and all pages, counts and
unique security identities match. The reviewer is responsible for the lawful
source and normalized-to-original semantic match for all other formats.

```sh
python -B m2_risk_snapshot.py --manifest "$PRIVATE_UNIVERSE" \
  --evidence "$PRIVATE_REVIEWED_EVIDENCE" --target 2026-11-16
```

Default prints only aggregate coverage by board and frozen sector, does not
write private state or use FFD/anything online. To opt into private export of a
reviewed source (not a website publication), add `--artifacts` for the archived
original files and `--write-private` for an owned 0700 state directory outside
the repo. Each archived source file must match its reviewed SHA; the resulting
`risk-YYYY-MM-DD.json` is private, create-only and understood by
`m2_incremental.py`. If source dates, scope, original receipts or counts are
missing, preserve the unknown coverage instead of labelling a full run.
