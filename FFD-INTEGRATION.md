# FFD controlled trial integration

This is an opt-in sample path, not a production data-source switchover. Existing
95% breadth coverage, same-day history and five-index gates are unchanged.

## Safe sample

Supply `FFD_API_KEY` through the process environment / a scoped CI secret. Never
commit it, put it on the command line, or print it. No credentials are loaded from
personal client configuration by this runner.

```sh
python ffd_breadth_probe.py --cutoff 2026-11-12
python -m unittest test_ffd_history -v
```

The explicit cutoff must be a completed close according to the existing trading
calendar. Default security is `600000.SH`. The probe requests close and volume for
one 90-calendar-day interval with `options=CPS:2`, `coverage_policy=strict`. It
requires at least 50 real observations. It only writes under `output/ffd-probe/`;
it does not write or publish the site's successful snapshots.

Default budget is 200 data points. Before any request, the client reserves 182
points (91 inclusive calendar days × 2 fields), a conservative ceiling, rather
than assuming weekends/holidays will be returned. Actual charge is disclosed in
the provider response; reservations are not refunds or ledger balances. Raising
`--max-points` is an explicit operator choice, not an automatic fallback. Each run
uses one client; do not launch concurrent trials against the same quota. All client
network calls within a process are serialized. There is no automatic HTTP retry.
Unknown transport outcomes halt that client and retain its reservation; inspect
the original request in FFD before retrying in a new run.

The client rejects missing/unknown/partial coverage, wrong code/adjustment/date,
nonfinite/negative values, missing columns, stale/duplicate/unordered dates.
TLS verification remains enabled using the normal requests trust store. No
system security settings are changed.

## Scope and remaining acceptance

FFD declares native qfq execution but does not independently certify all
corporate-action factor reconciliation. A passing sample is not full-market
coverage, long-term availability, an SLA, or permission to mix adjusted price
segments from different dates/providers. Preserve one complete same-cutoff series
per security. News snippets and generated news commentary are not price inputs.

The local optional `complete_breadth.get_history(..., ffd_client=client)` hook is
not enabled by any default collector. It retains FFD cache responses separately
(`*.ffd.json`) and never overwrites existing Tencent/Eastmoney caches. Any result
using FFD is marked `qfq-shsz-ffd-experimental-v1`, intentionally not the existing
production scope. Do not deploy this hook without its integration tests and an
explicit production acceptance decision. `test_ffd_integration.py` belongs to that
future hook release; `test_ffd_history.py` tests the standalone adapter/probe.

## Persistent attempt receipts (required before retry)

Before POST, the client exclusively creates and fsyncs a receipt under
`output/ffd-request-receipts/`, keyed by the exact non-secret request-body SHA256.
It sends the same UUID in `X-Request-ID` and `X-FFD-Client-Request-ID`, matching the
public FFD MCP 0.8.53 client. HTTP status, exception **class** and service request ID
are retained when available; credentials, exception messages and headers are not.
Any existing attempt (including pending after a crash) blocks another call with
the same parameters across processes. Completed attempts also require deliberate
operator handling instead of silently repurchasing. No automatic clearing or
retry is provided. Do not clear a pending/unknown receipt before reconciling the
original request with FFD.

CI must preserve and restore these receipts before attempting data calls, with
workflow-level serialization. An ephemeral empty runner alone cannot guarantee
cross-run deduplication. A failure from the older client without receipts must be
reconciled separately; installing this version does not retroactively identify
or authorize retrying that failed request.

## Initial release acceptance (2026-11-13)

The GitHub `FFD bounded data-source acceptance` workflow performs offline tests
and zero-data-quota HTTPS health/entitlement checks using the repository secret.
It does **not** query historical prices on fresh runners, because persistent
cross-run receipts and reconciliation must be established first. A first local
90-day sample request ended with an unknown transport/HTTP result before the
receipt upgrade. Its parameters are locally blocked pending reconciliation;
no automatic retry or full-market query is authorized by this workflow.

Published production breadth remains on its existing source and scope. The
new source is installed for controlled acceptance, not yet promoted to production.
The factor-events coverage-only probe for 600000.SH through 2026-11-12 reports
completeThrough=2026-10-23 and incomplete interval coverage. Do not infer an
absence of later corporate actions or rebase cached prices using this gap.
