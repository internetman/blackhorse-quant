# Daily candidate publication contract

`m2-daily-candidates.json` is a completed screening output, not an attempt log.
To render cards in the current daily section, the producer must supply:

- `schemaVersion: 1`, `mode: "close"`, `runStatus: "success"`, `barStatus: "completed"`.
- `asOfDate` exactly matching the verified calendar's expected completed close.
- `candidateCount` equal to `candidates.length`, including a genuine zero.
- Every candidate has a six-digit `code` and matching `asOfDate`.

These flags attest successful completion, not corporate-action verification or a confirmed buy signal. Unverified corporate actions remain `待核`, and the UI never emits confirmed signals.

Replay, stale/future dates, unknown calendars, failure/partial/unknown completion and malformed records show diagnostic metadata only, never current stock cards. Older files are preserved, not added to the current view. A missing or failed file does not mean zero candidates. A complete successful zero has its own message. Archived candidates remain excluded across dates until explicitly restored.

The currently published no-data state is unchanged. The pilot replay schema will intentionally display no cards. The producer must add the completion flags only after a real completed-close run; never relabel a replay to satisfy this gate.
