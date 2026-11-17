# China-market update scheduling

## Clock and date rules

- Interpret all run windows in `Asia/Shanghai` and use the checked-in verified exchange calendar, not a generic weekday calendar. Weekdays in a timer only reduce no-op invocations; the runner must still check holidays and fail closed for unknown years.
- **Midday:** 12:07, with a 12:27 retry only if no successful noon snapshot exists. Accept only the current trading day's genuine midday data within the existing collection window, with verified quote date/observation metadata. Never turn a late/noon retry into close collection. An expired noon attempt reports a missed snapshot, retaining the previous valid date.
- **Close:** 16:40 with checks at 17:40 and 18:40. On each invocation, resolve the latest finalized verified trading day (16:00 cutoff), even when the job starts after midnight or over a weekend. A manual backfill can specify `session=close` and a valid finalized `target_date=YYYY-MM-DD`. The request must catch up only missing sessions; date selection does not grant permission to reload full histories. Refuse to overwrite an already newer published date. A private historical repair may still update the private cache before calculating the latest publishable date.
- Record the intended date, actual source date, run ID, coverage and result separately. Do not count job status alone as publication. Read the deployed snapshot/status after publication and verify the date and generation. Report missing/unverified data as missing; never fall back to presenting old data as today's.
- GitHub schedule is a fallback, not an SLA: [GitHub documents that queued scheduled jobs can be delayed or dropped](https://docs.github.com/en/actions/how-tos/troubleshoot-workflows#scheduled-workflows-running-at-unexpected-times). The manual date input and retry-safe runner can catch up after late delivery; they don't fix events that never arrive. Moving noon off the hour reduces expected contention but remains best effort.

## Independent timer deployment template (not provisioned)

Preferred after full acceptance: assign one small always-on Linux runner with persistent, non-public storage. Use the direct incremental wrapper after it is implemented and verified; `cloud_breadth.py`'s publishing entrypoint is currently GitHub production Actions only and **must not** be run directly on another machine with fake `GITHUB_*` variables. A timer that only calls GitHub `workflow_dispatch` avoids cron event loss but still depends on Actions queue latency; it does not guarantee an exact midday snapshot.

Use two systemd timer units, both pointing to the same template service with different instances. These are templates; the local wrapper path, service account, directory ownership, secret-loading method and publishing transport must exist before enabling them.

```ini
# heima-noon.timer
[Timer]
OnCalendar=Mon..Fri *-*-* 12:07:00 Asia/Shanghai
OnCalendar=Mon..Fri *-*-* 12:27:00 Asia/Shanghai
AccuracySec=15s
Persistent=false
Unit=heima-refresh@midday.service
[Install]
WantedBy=timers.target
```

```ini
# heima-close.timer
[Timer]
OnCalendar=Mon..Fri *-*-* 16:40:00 Asia/Shanghai
OnCalendar=Mon..Fri *-*-* 17:40:00 Asia/Shanghai
OnCalendar=Mon..Fri *-*-* 18:40:00 Asia/Shanghai
AccuracySec=15s
Persistent=true
Unit=heima-refresh@close.service
[Install]
WantedBy=timers.target
```

```ini
# heima-refresh@.service
[Service]
Type=oneshot
User=heima
Group=heima
StateDirectory=heima
StateDirectoryMode=0700
WorkingDirectory=/opt/heima
UMask=0077
NoNewPrivileges=true
PrivateTmp=true
# Both sessions use one lock across all timer instances.
# Exit 75 means busy; wrapper receives the next normal timer retry.
ExecStart=/usr/bin/flock -n -E 75 /var/lib/heima/run.lock /opt/heima/bin/refresh-heima --session %i --state-dir /var/lib/heima
TimeoutStartSec=20min
```

The direct wrapper must implement these inputs, read-only/no-spend preview, safe reruns, persistent receipts and the strict validation rules; the template is not a readiness claim. Set any encrypted credential/secret configuration separately with the user's authorization. Keep API keys, full paid bars, requests, receipts, and persistent caches off the public repo, public CI caches/artifacts, and web root. A public publish step may receive only reviewed/license-compatible derived snapshots; grant only narrow repository-specific rights for that step if needed. Do not run the old cold process or enable an extra scheduler collecting concurrently during migration. A lock on one host is not a distributed lock; direct collection should have one owner, not both GitHub and server timers, unless the real collector has a shared lease and idempotency database.

Before enabling these timers:
1. Inventory verified historical seed and approved private durable storage, current FFD entitlement, and a compute runner with outbound HTTPS and enough space for the actual seed plus backups. Reuse existing resources only after checking they're available and authorized; no new purchase is implied.
2. Run offline fixtures and a no-write preflight. Then use a separately bounded representative live gap test with persistent point accounting; confirm scope and publication rights.
3. Verify on a real trading day while the Mac is unavailable. Check the deployed fresh date, separate noon/close observations and candidate scope, aggregate and per-sector coverage, and quota receipt. Exercise the explicit close catch-up and ensure duplicate dispatch does not repeat paid calls.
4. If scheduled jobs skip, carry forward the last verified display date and report the precise failed stage. Do not enable forced historical collection as a workaround.

To inspect calendar expressions without enabling anything: `systemd-analyze calendar 'Mon..Fri *-*-* 12:07:00 Asia/Shanghai'` (repeat for each time). Use a deployment-specific clock and check both timers with the service operator before releasing.

## Dedicated macOS mini alternative (template, not installed)

Use only the intended, explicitly connected Mac mini. Do not install on the laptop by default. The only process in this template is a user-level LaunchAgent; it requires the chosen account's GUI session to stay logged in and the machine to be awake and online. It does not enable automatic login, wake from sleep for lunch, change energy/security settings, or require sudo. If unattended operation after reboot without login is necessary, review a system LaunchDaemon/service account separately. Missed close can catch up when the agent returns; a missed lunch snapshot remains missing.

**Before loading:** provision an approved private local app/working tree and a user-owned non-synced state directory with mode 0700 (for example, under the chosen user's `Library/Application Support/Heima`); raw bars, quota receipts, and secrets do not belong in a public clone, iCloud/Dropbox, or logs. Add the user-level interpreter absolute path (Python 3.10+ with IANA tzdata) and executable adapter path. The approved publishing adapter and private historical seed still need to be connected; don't point the worker at the legacy force/cold collection scripts. If FileVault, sleep, reboot, or logout prevents execution, don't claim successful overnight operation.

1. Copy `deployment/com.heima.refresh.plist.example` into that user's `~/Library/LaunchAgents/com.heima.refresh.plist` with all placeholder paths replaced. Keep the template's preview mode (no `--execute`) initially. Prepare and restrict the log directory first because launchd opens those paths before the Python tick. Keep logs local and monitor/rotate them if enabled.
2. Validate the edited plist with `plutil -lint "$HOME/Library/LaunchAgents/com.heima.refresh.plist"`. From the dedicated Mac mini's signed-in account, an authorized operator can run `launchctl bootstrap "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.heima.refresh.plist"`, then inspect `launchctl print "gui/$(id -u)/com.heima.refresh"`. Preview invokes no worker and uses no FFD points. To unload, use `launchctl bootout "gui/$(id -u)" "$HOME/Library/LaunchAgents/com.heima.refresh.plist"`. These are setup instructions, not actions taken.
3. Verify selectable dates, worker readiness, local timezone behavior, and private state permissions with the actual mini. A 60-second launchd tick does not depend on the Mac's local timezone: the Python code explicitly uses Asia/Shanghai. The noon lane is limited to today's verified lunch window, with one safe retry; the close lane targets the latest finalized verified date with bounded retry/catch-up. The Python `fcntl` lock serializes both lanes; don't concurrently enable a second machine to do paid collection.
4. The adapter must accept `--session midday|close --target-date YYYY-MM-DD --state-dir DIR`; write only one small JSON receipt to stdout. Return `session` and `targetDate`. `verified` or `already_current` also needs `verifiedDate` equal to the target and `publicationVerified:true`. `retryable_no_paid_query` requires `historyCalls:0` and explicitly proves that no paid request occurred. The adapter must independently guard date/coverage/quotes, persist a quota ledger, and publish only authorized derived snapshots. The launcher leaves a durable in-flight record before spawn. A crash, timeout, unverified receipt, or uncertain consumption blocks all later paid starts until an operator reconciles the separate quota ledger; do not delete the receipt to force an automatic retry.
5. Only after offline and approved bounded live acceptance, add `--execute` to ProgramArguments, revalidate and reload the agent. Verify on a real trading day with the MacBook unavailable. The Scheduler does not change the system time zone, energy policies, login, or permissions.
