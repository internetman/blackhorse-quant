"""Offline M2 issuer-status evidence: incomplete, undated data remain unknown."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import stat
from urllib.parse import urlsplit

from m2_incremental import M2_SYMBOL, validate_seed

SZ_CATALOG = {"active":("1110","tab1","agdm"),
              "warning":("fxjsb","tab1","zqdm"), "arrangement":("fxjsb","tab2","zqdm")}
ROLES = {"active", "warning", "arrangement", "delisted"}
BOARDS = {"SH-main", "SH-star", "SZ-main", "SZ-gem"}
OFFICIAL_HOST = {"SH-main":{"www.sse.com.cn","star.sse.com.cn","query.sse.com.cn"},
                 "SH-star":{"www.sse.com.cn","star.sse.com.cn","query.sse.com.cn"},
                 "SZ-main":{"www.szse.cn","docs.static.szse.cn","disc.static.szse.cn"},
                 "SZ-gem":{"www.szse.cn","docs.static.szse.cn","disc.static.szse.cn"}}



def canonical_day(day):
    if dt.date.fromisoformat(day).isoformat()!=day:
        raise ValueError("date must be canonical ISO format")
    return day


def board_for(code):
    if not isinstance(code,str) or not M2_SYMBOL.fullmatch(code):
        raise ValueError("invalid exchange-qualified security code")
    prefix = code[:3]
    if code.endswith(".BJ"):
        return "BJ-unverified"  # Preserve original scope; no approved evidence adapter.
    if code.endswith(".SH"):
        if prefix in {"688","689"}:
            return "SH-star"
        if prefix in {"600","601","603","605"}:
            return "SH-main"
    else:
        if prefix in {"300","301"}:
            return "SZ-gem"
        if prefix in {"000","001","002","003"}:
            return "SZ-main"
    raise ValueError("unsupported board prefix; do not infer eligibility")


def codes_from_szse_pages(pages, role, target):
    """Verify the actual site report contract, with no archive/date guessing."""
    catalog,tab,field=SZ_CATALOG[role]
    all_rows, seen_pages, first = set(),set(),None
    for p in pages:
        matches=[entry for entry in p if (entry.get("metadata") or {}).get("tabkey")==tab]
        if len(matches)!=1:
            raise ValueError("missing/duplicate SZSE report tab")
        entry=matches[0]
        meta=entry["metadata"]
        if meta.get("catalogid")!=catalog or meta.get("subname","").strip()!=target:
            raise ValueError("SZSE report does not attest target trading date")
        counts=tuple(meta.get(x) for x in ("pagesize","pagecount","recordcount"))
        if any(type(x) is not int or x<0 for x in counts) or counts[0]==0:
            raise ValueError("invalid SZSE report pagination metadata")
        size, n, total=counts
        if n!=(total+size-1)//size:
            raise ValueError("inconsistent SZSE page/record count")
        first=counts if first is None else first
        if first!=counts:
            raise ValueError("SZSE report pages have differing counts")
        slot=meta.get("pageno")
        if type(slot) is not int or not 1<=slot<=max(1,n) or slot in seen_pages:
            raise ValueError("missing or duplicate SZSE page")
        seen_pages.add(slot)
        records=entry.get("data")
        if not isinstance(records,list) or len(records)!=min(size,max(0,total-(slot-1)*size)):
            raise ValueError("SZSE report page truncated")
        for row in records:
            code=row.get(field,"")+".SZ"
            if board_for(code) not in {"SZ-main","SZ-gem"} or code in all_rows:
                raise ValueError("duplicate or wrong scope symbol")
            all_rows.add(code)
    if first is None or len(all_rows)!=first[2] or seen_pages!=set(range(1,max(1,first[1])+1)):
        raise ValueError("SZSE report missing pages")
    return all_rows


def evidence_codes(role, target, board, document):
    """Consume an independently reviewed normalized bundle; never attests it itself."""
    receipt=document["receipt"]
    url=urlsplit(receipt["source"])
    if url.scheme!="https" or url.hostname not in OFFICIAL_HOST[board] or url.username or url.password:
        raise ValueError("evidence source is not a permitted official exchange HTTPS origin")
    if receipt.get("sourceDate")!=target or receipt.get("board")!=board or receipt.get("role")!=role:
        raise ValueError("evidence date/board/role does not match requested snapshot")
    if receipt.get("complete") is not True or not receipt.get("sourceVersion") or not receipt.get("reviewedBy"):
        raise ValueError("missing complete dated evidence reviewer or source version")
    if not re.fullmatch(r"[0-9a-f]{64}",receipt.get("originalArtifactSha256","")):
        raise ValueError("missing hash for independently archived original evidence")
    codes=document["codes"]
    if not isinstance(codes,list) or type(receipt.get("recordCount")) is not int or receipt["recordCount"]!=len(codes):
        raise ValueError("normalized list count mismatch")
    if any(board_for(c)!=board for c in codes) or len(codes)!=len(set(codes)):
        raise ValueError("duplicate or wrong board code in evidence list")
    if role=="active" and not codes:
        raise ValueError("an empty active board is not a complete roster")
    return set(codes), receipt


def build(manifest, target, evidence):
    canonical_day(target)
    if (not manifest.get("membershipSource") or not manifest.get("membershipDate")
            or canonical_day(manifest["membershipDate"])>target):
        raise ValueError("missing or forward-dated membership manifest")
    frozen=[dict(s,risk=s.get("risk","unknown")) for s in manifest["securities"]]
    validate_seed(frozen)
    by_board={}
    for board, records in evidence.items():
        if board not in BOARDS or set(records)-ROLES:
            raise ValueError("unknown evidence board or role")
        by_board[board]={role:evidence_codes(role,target,board,doc) for role,doc in records.items()}
    statuses={}
    summary={}
    sectors={}
    for s in frozen:
        code=s["code"]
        board=board_for(code)
        roles=by_board.get(board,{})
        excluded=any(code in payload[0] for role,payload in roles.items() if role!="active")
        status="excluded" if excluded else ("eligible" if set(roles)==ROLES and code in roles["active"][0] else "unknown")
        statuses[code]=status
        counts=summary.setdefault(board,dict(eligible=0,excluded=0,unknown=0))
        counts[status]+=1
        sectors.setdefault(s["sector"],dict(eligible=0,excluded=0,unknown=0))[status]+=1
    digest=hashlib.sha256(json.dumps(evidence,sort_keys=True,ensure_ascii=False,separators=(",",":")).encode()).hexdigest()
    return dict(asOfDate=target,evidence=f"Independently reviewed venue evidence bundle sha256={digest}",
                evidenceSha256=digest,statuses=statuses,coverageByBoard=summary,coverageBySector=sectors)


def verify_archived_artifacts(evidence, directory):
    if directory is None:
        raise ValueError("reviewer must supply the private original evidence artifact directory")
    for records in evidence.values():
        for doc in records.values():
            receipt=doc["receipt"]
            artifact=receipt.get("originalArtifact") or ""
            if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,100}",artifact):
                raise ValueError("original artifact requires a simple filename")
            path=directory/artifact
            if not stat.S_ISREG(path.lstat().st_mode):
                raise ValueError("source artifact must be a regular archived file")
            if hashlib.sha256(path.read_bytes()).hexdigest()!=receipt["originalArtifactSha256"]:
                raise ValueError("archived evidence bytes do not match reviewed checksum")


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument("--manifest",type=Path,required=True)
    p.add_argument("--evidence",type=Path,required=True,help="Independent reviewed normalized evidence bundle; no network")
    p.add_argument("--target",required=True)
    p.add_argument("--artifacts",type=Path,help="Private archived original evidence files; required when writing")
    p.add_argument("--write-private",type=Path,help="Optional 0700 private state directory outside repository")
    a=p.parse_args()
    evidence=json.loads(a.evidence.read_text())
    out=build(json.loads(a.manifest.read_text()),a.target,evidence)
    if a.write_private:
        state=a.write_private.absolute()
        st=state.lstat()
        repo=Path(__file__).resolve().parent
        if (not stat.S_ISDIR(st.st_mode) or st.st_uid!=os.getuid() or st.st_mode&0o077
                or state.resolve()==repo or repo in state.resolve().parents):
            p.error("requires owned 0700 outside the checkout")
        verify_archived_artifacts(evidence,a.artifacts)
        os.umask(0o077)
        with (state/f"risk-{a.target}.json").open("x") as f:
            json.dump(out,f,ensure_ascii=False)
    print(json.dumps({"asOfDate":out["asOfDate"],"coverageByBoard":out["coverageByBoard"],
                      "coverageBySector":out["coverageBySector"],"writePrivate":bool(a.write_private)},ensure_ascii=False))


if __name__=="__main__":
    main()
