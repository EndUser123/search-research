#!/usr/bin/env python3
"""Falsification test for hypothesis H-A.

H-A (load-bearing, unverified): "CC reads settings.json['model'] once at session
start and never re-reads it mid-session, so the autoswitch apply hook's
settings.json write is INERT for same-turn routing."

This script resolves H-A empirically by joining two independent telemetry streams:

  1. apply_audit.jsonl  — what the hook WROTE at UserPromptSubmit
     (new_model, current_model, session_id, ts; dry_run=False rows only).
  2. CCR request log    — what Claude Code actually SENT in the request body
     (`type: "request body"` -> data.model, emitted by CCR per request).

Discriminating signal: for each live apply at time T writing new_model=M, the
FIRST CCR request body with time > T carries data.model. If CC honors the write,
data.model == M (H-A FALSE, propagation works, possibly with a one-turn lag).
If CC caches at session start, data.model ignores M and stays the session-start
model (H-A TRUE, write is inert).

Why dry-run rows are excluded: MODEL_ROUTER_APPLY_DRY_RUN=1 logs a would-be write
WITHOUT touching settings.json, so by construction it cannot test propagation.
Testing H-A requires LIVE writes.

Run:  python scripts/verify_h_a_settings_cadence.py [--audit PATH] [--ccr-log-dir DIR]
Exit code: 0 = evidence collected (see printed verdict); 1 = no joinable evidence.
"""
import argparse
import glob
import json
import os
import sys
from datetime import datetime, timezone

DEFAULT_AUDIT = "P:/.claude/state/model-router/apply_audit.jsonl"
DEFAULT_CCR_LOG_DIR = os.path.expanduser("~/.claude-code-router/logs")


def load_live_applies(path, session_id=None):
    """Live (non-dry-run) apply events, newest last. Optional session filter."""
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            if r.get("dry_run"):
                continue  # writes nothing; cannot test propagation
            if session_id and r.get("session_id") != session_id:
                continue
            rows.append(r)
    return rows


def load_ccr_request_timeline(log_dir, single_log=None):
    """Timeline of (epoch_ms, reqId, cc_sent_model, ccr_routed_model).

    Pass single_log= to restrict to one CCR log file (recommended: CCR's log has
    no session_id, so joining across files/months/config-eras is noise).
    """
    req_sent = {}
    req_final = {}
    req_time = {}
    if single_log:
        files = [single_log]
    else:
        files = sorted(glob.glob(os.path.join(log_dir, "ccr-*.log")))
    for fp in files:
        try:
            with open(fp, encoding="utf-8") as f:
                for line in f:
                    try:
                        e = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    rid = e.get("reqId")
                    t = e.get("time")
                    if not rid or not isinstance(t, (int, float)):
                        continue
                    if e.get("type") == "request body":
                        req_sent.setdefault(rid, e.get("data", {}).get("model"))
                        req_time.setdefault(rid, t)
                    elif e.get("msg") == "final request":
                        body = e.get("request", {}).get("body", "")
                        try:
                            bj = json.loads(body) if isinstance(body, str) else body
                            req_final[rid] = bj.get("model")
                        except (json.JSONDecodeError, AttributeError):
                            pass
        except OSError:
            continue
    timeline = [
        (req_time[rid], rid, req_sent[rid], req_final.get(rid))
        for rid in req_sent
        if rid in req_time
    ]
    timeline.sort(key=lambda x: x[0])
    return timeline


def iso_to_epoch_ms(ts):
    # apply_audit ts is naive LOCAL time (hook writes datetime.now().isoformat()).
    # CCR `time` is absolute epoch ms. Both run on the same host, so leave the
    # naive datetime alone — Python's .timestamp() resolves it via system tz.
    # (Do NOT force UTC: that shifted the join ~6h and made every pair "no match".)
    dt = datetime.fromisoformat(ts)
    return dt.timestamp() * 1000.0


def first_request_after(timeline_ms, t_ms):
    """First request whose time > t_ms (apply fires before the request)."""
    for time_ms, rid, sent, routed in timeline_ms:
        if time_ms > t_ms:
            return (time_ms, rid, sent, routed)
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--audit", default=DEFAULT_AUDIT)
    ap.add_argument("--ccr-log-dir", default=DEFAULT_CCR_LOG_DIR)
    ap.add_argument("--ccr-log", default=None, help="Single CCR log file (overrides --ccr-log-dir). "
                     "Recommended: use --session-id + the matching day's CCR log to avoid "
                     "cross-era noise from old config/provider combos.")
    ap.add_argument("--session-id", default=None, help="Filter applies to one session (strongly recommended)")
    args = ap.parse_args()

    applies = load_live_applies(args.audit, session_id=args.session_id)
    timeline = load_ccr_request_timeline(args.ccr_log_dir, single_log=args.ccr_log)
    print(f"live apply events: {len(applies)}")
    print(f"CCR request bodies: {len(timeline)}")
    if not applies or not timeline:
        print("VERDICT: insufficient evidence (need live applies AND CCR logs).")
        return 1

    t_min = timeline[0][0]
    t_max = timeline[-1][0]
    print(f"CCR log window: {datetime.fromtimestamp(t_min/1000)} .. "
          f"{datetime.fromtimestamp(t_max/1000)}")

    matched = 0       # CC sent exactly new_model (write propagated)
    sent_current = 0  # CC sent current_model (the pre-write value; write inert)
    sent_other = 0    # CC sent neither (CCR-slot relabel or third value)
    skipped = 0
    evidence = []

    for r in applies:
        try:
            t_ms = iso_to_epoch_ms(r["ts"])
        except (KeyError, ValueError):
            skipped += 1
            continue
        nxt = first_request_after(timeline, t_ms)
        if not nxt:
            skipped += 1
            continue
        _, rid, sent, routed = nxt
        new_m = r.get("new_model")
        cur_m = r.get("current_model")
        if sent == new_m:
            verdict = "PROPAGATED"
            matched += 1
        elif sent == cur_m:
            verdict = "INERT (sent pre-write current_model)"
            sent_current += 1
        else:
            verdict = f"OTHER (sent={sent!r})"
            sent_other += 1
        evidence.append((r["ts"][:19], r.get("session_id", "")[:8],
                         cur_m, new_m, sent, routed, verdict))

    total = matched + sent_current + sent_other
    print(f"\njoinable apply->request pairs: {total} (skipped {skipped})")
    print(f"  PROPAGATED (CC sent new_model):           {matched}")
    print(f"  INERT (CC sent pre-write current_model):  {sent_current}")
    print(f"  OTHER (CC sent neither):                  {sent_other}")

    print("\nsample evidence (first 12):")
    print(f"  {'apply_ts':<19} {'sess':<8} {'current':<22} {'new':<22} {'cc_sent':<22} {'routed':<22} verdict")
    for row in evidence[:12]:
        ts, sess, cur, new, sent, routed, v = row
        print(f"  {ts:<19} {sess:<8} {(cur or '')[:21]:<22} {(new or '')[:21]:<22} "
              f"{(sent or '')[:21]:<22} {(routed or '')[:21]:<22} {v}")

    if total == 0:
        print("\nVERDICT: no overlap between apply timestamps and CCR log window.")
        return 1
    prop_rate = matched / total
    if prop_rate > 0.8:
        print(f"\nVERDICT: H-A likely FALSE ({prop_rate:.0%} propagated) — CC honors the "
              "settings.json write within the turn. Apply path is NOT inert.")
    elif sent_current / total > 0.8:
        print(f"\nVERDICT: H-A likely TRUE ({sent_current/total:.0%} inert) — CC sent the "
              "pre-write current_model, ignoring the hook's write. Apply path IS inert "
              "for same-turn routing.")
    else:
        print(f"\nVERDICT: AMBIGUOUS — mixed signal. Inspect the OTHER rows; CCR slot "
              "relabeling (think/background/longContext) may be masking the comparison.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
