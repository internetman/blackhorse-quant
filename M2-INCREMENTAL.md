# Four-sector FFD incremental close screening

**Readiness:** a private verified seed and persistent request ledger are mandatory.
The CLI neither searches for keys nor deploys files; it must be run from the cloud
compute environment where the operator has set up an authorized FFD key and
durable private state. Do not use a public GitHub workflow cache or an Actions
artifact to store raw FFD data. The absence of a seed is not a zero-result run.

## State and scope

Create a `0700` state directory outside the repository and deployment root.
Transfer a verified seed internally to `seed.json` in that directory:

- `schemaVersion: 1`, `adjustment: "qfq"`, `volumeUnit: "share"`, `amountUnit: "CNY"`.
- `provenance`: nonempty source description; `membershipDate`: verified effective date.
- `securities`: the frozen 360-symbol four-sector manifest, with six-digit code and
  `.SH` or `.SZ`, `name`, `sector` and risk classification
  `eligible` / `excluded` / `unknown`. ST/delisting status must not be guessed.
- `histories`: map from exchange-qualified codes to original, verified date-ordered
  completed daily bars, each with `date,open,high,low,close,volume,amount`.
  Use at least 319 observed seed rows before adding one target-day row. No
  intraday/future rows or fabricated suspended-date bars. The script currently
  omits a symbol if the supplied window has missing exchange trading dates.
  For historical sources without original turnover amount, explicitly specify
  `olderAmountsUnavailable: true` and set that recorded field to `null` only
  before the last three bars. The overlap and all newly appended sessions
  still require actual amount. This S2-only path uses no historical amount data.
- For the frozen manifest, all four sectors must separately reach 95% verified
  coverage. The full-market breadth tab is untouched. Never reuse the review
  result as a chart feed, full-market coverage, a confirmed trade or a zero
  result after a stopped or partial run.

History backups/apertures and the exact path to the state directory belong in the
private deployment setup documentation. Freeze seed identity and membership
before a run; do not overwrite private state out of band.

## Operator commands

No network / no market data cost (default):

```sh
python m2_incremental.py --state "$M2_PRIVATE_STATE" --as-of 2026-11-16 --max-points 13000 --plan-only
```

The report identifies missing/eligible history, potential per-sector coverage and
conservative cap. The cap is calendar-day cells × six fields (including three
overlapping dates, so a Wednesday-through-Monday query reserves 36 points per stock).
Actual usage for delivered cells is reported separately and unknown provider
outcomes must be reconciled against account records. A failed preflight makes
no requests; resolve the private seed or approved cap first rather than bypassing it.

Only after validating the plan, receiving authority for the actual spend cap,
and configuring authorized `FFD_API_KEY` in the environment, add `--execute`
instead of `--plan-only`. Expected session dates come from the exchange calendar. Supply independently verified
prior-year closures with `--history-calendar` when the published calendar does
not cover the long seed.
The provider's native daily field is `amt` (normalized inside to `amount`).
The producer checks same-date adjusted OHLC exactly (float representation
tolerance only), volume within 50 shares, and amount within one yuan before
appending. These checks catch materially shifted bases and units; they do not
independently verify corporate actions. VCP, pivot, volume quality and events
remain manual. The initial four-sector scope only screens the S2 rules.

Run only one process against the same private state. Request intents and
responses are persisted before validation, keyed by stable request fingerprints.
Replays accept only completed immutable receipts whose private response SHA
matches. A pending/unknown/rejected attempt blocks all new queries until an
operator reconciles the exact attempt and records the outcome; there is no
automatic retry or quota refund. Do not clear a receipt and repurchase silently.
Unexpected/unreported actual charge also creates a private billing hold.
Incremental bars, attempts and per-security errors stay private.

Look at `run-YYYY-MM-DD.json` for coverage, reservations and reported successful
charges. `derived-YYYY-MM-DD.json` is written only for a completed review run
that clears the four separate coverage gates. It is a derived *pilot* shape with
plain name/code/stage/position and review caveats, not the formal daily candidate
feed. CSV/JSON seeds, raw responses, test fixtures, numeric bars and charge
ledgers must never be committed, uploaded publicly or deployed. Any eventual
pilot publication is a separate validation/promotion step; require the current
run's `candidate_ready` receipt for the exact target date.
