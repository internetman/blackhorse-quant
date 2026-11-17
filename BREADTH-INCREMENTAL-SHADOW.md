# MA20/MA50 gap-only staging (not a production runner)

This offline tool does not query a provider, accept terms, deploy, publish, or switch
the current scheduled job. It proves a bounded day's plan without charging points.
The published manifest contains metadata/hashes, not reusable private price bars.

## Import preflight

Use the original cache for an independently verified close. Do not put price bars,
request receipts, or seed output in the public repository, Vercel, or workflow logs.
The private staging directory must be newly created and outside the checkout.

```sh
python breadth_incremental.py --snapshot market-breadth.json \
  --cache-dir /path/to/private/qfq-breadth-cache/2026-11-12 \
  --calendar market-trading-calendar.json --target-date 2026-11-16 \
  --private-stage /private/path/breadth-incremental-2026-11-16
```

Add `--ffd-receipt-dir /path/to/private/ffd-request-receipts` when the FFD native
responses are held as charged, verified request/response pairs.

The importer verifies native response SHA256, symbol, source, adjustment, date,
count, and calendar against the snapshot manifest. Missing/unverified raw cache
files are counted and never fetched by this tool. The temporary stage contains a
private source seed, frozen membership, and request plan. An exit code of 2 means
the fixed 95% market gate is impossible with the current seed. Exit 0 means only
that the usable seed can potentially reach 95%, not a release.

## Offline calculation and guardrails

To calculate, use `--bundle <private JSON>` instead of `--snapshot/--cache-dir`.
Bundle fields are `membership`, `seed`, `deltas`, and `independentQuotes`; the
last two mandatory fields should be produced by a separately authenticated and validated source
adapter. Each delta names the code, provider, cutoff, qfq basis, request ID,
bars and an independent corporate-actions coverage attestation, while each quote
names the security, final session, native source timestamp and source. See the test
fixture for exact fields. Handwritten attestations do not replace data evidence.

Only 1–5 missing exchange sessions plus three overlapping bars can be requested by
this plan. Comparing the overlap detects price-basis disagreements; it cannot prove
the absence of earlier price rebases. Verification must cover the retained MA window
through target and prove the adjustment basis has not changed. Missing factor data,
basis changes, or mixed suppliers fail closed for that security. Prior same-source FFD
cache is reusable; a Tencent/Eastmoney seed cannot be silently stitched onto FFD.
Target quote date and cutoff must match; a >0.5% per-name cross-check failure excludes
that stock and >1% of request candidates blocks acceptance. Sector ratios with <95%
coverage remain blank; market coverage uses the unchanged official denominator.

The raw-free report is deliberately **not publishable**. The optional
`benchmarks` map takes the five existing benchmark security IDs as keys; each
value contains `seed` and `delta` with `secid`, `provider`, `adjustment: none`
and `bars`. The seed also needs a canonical `barSha256` and the delta a
`requestId`. Missing or invalid benchmark input fails that gate and exits 2.
The staged private seed is not promoted by this tool. Keep the prior state when the
gate fails; do not allow partial runs to evict older source data or consume a retry.
Do not reuse a stale frozen universe as if it were a refreshed membership snapshot.

## Remaining production prerequisites

1. Verify a complete reusable private cache and migrate only minimal history into
   an approved private persistent cloud store, with atomic generation pointers,
   retained last-good state, request fingerprints, and a shared point cap.
2. Obtain authoritative factor-event or unchanged-basis evidence for each window,
   independently timestamped final close quotes, up-to-date universe/membership,
   and five benchmark seed windows. Recover the original FFD cache responses by
   hash; do not replace them with guesses or silently mix adjustment cuts.
3. Implement and accept the live gap-only source adapter and verify its benchmark
   collection, then perform an end-to-end private cloud run before publishing aggregate
   copy. Wider FFD migration may need a one-time separately authorized seed;
   never make a daily full-window refresh the fallback.
4. Noon still requires the prior verified close plus independently attributed,
   dated noon snapshots. Report misses separately. Do not generate noon from the
   closing feed; the offline close-only tool has no noon side effects.
