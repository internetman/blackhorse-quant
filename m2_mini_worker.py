#!/usr/bin/env python3
"""Scheduler protocol adapter for a private four-sector M2 close run only."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

SCOPE = "four-sector-close-v1"
SAFE = "retryable_no_paid_query"
LOCAL = "private_preview_ready"
SCRIPT = Path(__file__).resolve().with_name("m2_incremental.py")


def trusted_config(path):
    if not path.exists():
        return {"executionEnabled": False}
    st = path.lstat()
    if not stat.S_ISREG(st.st_mode) or st.st_uid != os.getuid() or st.st_mode & 0o077:
        raise ValueError("M2 worker config must be an owned private regular file")
    config = json.loads(path.read_text())
    if (not isinstance(config, dict) or set(config) - {"executionEnabled","maxPoints","historyCalendar"}
            or type(config.get("executionEnabled",False)) is not bool):
        raise ValueError("invalid M2 worker config")
    if "maxPoints" in config and (type(config["maxPoints"]) is not int or config["maxPoints"] < 1):
        raise ValueError("M2 worker points cap must be a positive integer")
    if config.get("executionEnabled") and "maxPoints" not in config:
        raise ValueError("paid M2 execution must declare a point cap")
    if "historyCalendar" in config and not Path(config["historyCalendar"]).is_absolute():
        raise ValueError("historical calendar path must be absolute")
    return config


def result_for(session, target, root, *, run=subprocess.run):
    result = dict(session=session,targetDate=target,scope=SCOPE,publicationVerified=False)
    def safe(reason, **extra):
        return dict(result,status=SAFE,historyCalls=0,reason=reason,**extra)

    if session != "close":
        return safe("midday_lane_not_supported_by_this_worker")
    if dt.date.fromisoformat(target).isoformat() != target:
        return safe("noncanonical_close_date")
    try:
        info = root.lstat()
        if not root.is_absolute() or not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid():
            return safe("private_scheduler_state_required")
        config = trusted_config(root/"m2-worker.json")
        m2 = root/"m2"
        info = m2.lstat()
        if not stat.S_ISDIR(info.st_mode) or info.st_mode & 0o077 or info.st_uid != os.getuid():
            return safe("private_m2_state_required")
        if not (m2/"seed.json").is_file():
            return safe("missing_private_m2_seed")
    except (ValueError, OSError, TypeError):
        return safe("private_config_or_seed_not_ready")
    budget = config.get("maxPoints", 1)
    cmd = [sys.executable,str(SCRIPT),"--state",str(m2),"--as-of",target,"--max-points",str(budget)]
    if config.get("historyCalendar"):
        cmd += ["--history-calendar",config["historyCalendar"]]
    env = os.environ.copy()
    env.pop("FFD_API_KEY",None)
    try:
        planned = run([*cmd,"--plan-only"],capture_output=True,text=True,check=False,timeout=60,env=env)
        plan = json.loads(planned.stdout)
        if (planned.returncode not in (0,2) or plan.get("asOfDate") != target
                or plan.get("status") != "plan_only"):
            return safe("m2_preflight_receipt_invalid")
        cells, calls = plan.get("worstCasePoints"), plan.get("plannedRequests")
        if type(cells) is not int or cells < 0 or type(calls) is not int or calls < 0:
            return safe("m2_preflight_receipt_invalid")
    except (subprocess.SubprocessError, OSError, ValueError, AttributeError, TypeError):
        return safe("m2_preflight_unavailable")
    brief = {"plannedRequests":calls,"worstCasePoints":cells}
    if not config.get("executionEnabled"):
        return safe("m2_execute_disabled_app_config",**brief)
    if (plan.get("canReachCoverageGate") is not True or plan.get("fitsCap") is not True
            or cells > budget or planned.returncode != 0):
        return safe("m2_coverage_or_budget_gate",**brief)
    # The private app configuration is the only enabling switch. Never load,
    # print, or read a credential from the config. Deployment is not this worker.
    # Any failure after starting paid mode is uncertain to the scheduler.
    try:
        done = run([*cmd,"--execute"],capture_output=True,text=True,check=False,timeout=825)
        receipt = json.loads(done.stdout)
        calls = receipt.get("historyCalls")
        if (done.returncode != 0 or receipt.get("status") != "candidate_ready" or receipt.get("asOfDate") != target
                or type(calls) is not int or not 0 <= calls <= brief["plannedRequests"]):
            raise ValueError("invalid private M2 execution receipt")
        preview = json.loads((m2/f"derived-{target}.json").read_text())
        u = preview["universe"]
        if (preview.get("mode") != "derived-pilot" or preview.get("asOfDate") != target
                or preview.get("runStatus") != "success" or preview.get("barStatus") != "completed"
                or u.get("scopeId") != SCOPE or receipt.get("valid") != u.get("valid") or u.get("total") != 360):
            raise ValueError("invalid private M2 candidate preview")
    except (subprocess.SubprocessError, OSError, ValueError, KeyError, AttributeError, TypeError):
        return dict(result,status="uncertain",reason="m2_execute_receipt_requires_reconciliation")
    return dict(result,status=LOCAL,verifiedDate=target,historyCalls=calls,
                valid=u["valid"],total=u["total"])


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--session",choices=("close","midday"),required=True)
    p.add_argument("--target-date",required=True)
    p.add_argument("--state-dir",required=True,type=Path)
    a=p.parse_args()
    os.umask(0o077)
    try:
        output=result_for(a.session,a.target_date,a.state_dir)
    except ValueError:
        output=dict(session=a.session,targetDate=a.target_date,scope=SCOPE,
                    publicationVerified=False,status=SAFE,historyCalls=0,reason="invalid_worker_arguments")
    print(json.dumps(output),flush=True)


if __name__ == "__main__":
    main()
