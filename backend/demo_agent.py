"""Scripted demo agent — proves ENFORCEMENT, not just mechanism.

A real AI agent calls tools directly in code; a textbox demo can't show that.
This module simulates that loop deterministically (no external LLM calls):
  user message -> planner builds tool calls (with real PII in params,
  exactly as a careless agent would) -> every call is FORCED through the
  guard's sanitize path -> simulated tool -> restored reply.

With guard=False the calls bypass sanitization (contrast mode for the demo:
watch the inspector turn red). The tool itself is always simulated.
"""
import time

from detectors import detect_all
from vault import TokenVault
from fake_tool import record_blocked

TRIGGERS_SMS = ("sms", "send", "text", "notify", "otp", "message", "call me", "book", "confirm")


def plan_tools(message: str, types, ner=True, ner_thresholds=None):
    """Deterministic planner. Returns (calls, user_detections)."""
    dets = detect_all(message, tuple(types), aadhaar_strict=False,
                      ner=ner, ner_thresholds=ner_thresholds)
    ids = sorted({d.value for d in dets})
    calls = []
    if ids:
        calls.append(("lookup_account", {"query": message, "identifiers": ids}))
    lowered = message.lower()
    if any(k in lowered for k in TRIGGERS_SMS) or ids:
        phone = next((d.value for d in dets if d.type == "PHONE"), "customer-on-file")
        calls.append(("send_sms", {"to": phone, "body": message}))
    if not calls:
        calls.append(("lookup_account", {"query": message, "identifiers": []}))
    return calls, dets


def _sanitize(params, vault, types, ner=True, ner_thresholds=None):
    from app import sanitize_obj  # local import: app imports this module for the route
    return sanitize_obj(params, vault, types, False, True, ner, ner_thresholds)


def run_agent(message: str, types, guard: bool, tool_fn, vault=None,
              ner=True, ner_thresholds=None):
    """tool_fn(tool_name, payload, verdict) delivers to the (simulated) tool.
    Pass a session vault to keep the same tokens across turns; otherwise a
    fresh vault is used for this message only."""
    t0 = time.perf_counter()
    calls, user_dets = plan_tools(message, types, ner, ner_thresholds)
    vault = vault or TokenVault()
    trace = []
    for tool, params in calls:
        attempted = params
        if guard:
            sent, dets = _sanitize(params, vault, types, ner, ner_thresholds)
            from app import policy_door  # local import: app imports this module
            allowed, reason = policy_door(tool, dets)
            if not allowed:
                record_blocked(tool)
                trace.append({"tool": tool, "attempted": attempted, "sent": None,
                              "detections": [{"type": d.type, "value": d.value} for d in dets],
                              "leak_check": "BLOCKED (policy)", "reason": reason})
                continue
            real = [d.value for d in dets]
            leak = "PASS" if all(r not in str(sent) for r in real) else "FAIL"
        else:
            sent, dets, real = params, [], [d.value for d in user_dets]
            leak = "FAIL (bypassed)" if any(r in str(sent) for r in real) else "PASS"
        resp = tool_fn(tool, sent, leak)
        restored = vault.restore_obj(resp) if guard else resp
        trace.append({
            "tool": tool,
            "attempted": attempted,
            "sent": sent,
            "detections": [{"type": d.type, "value": d.value} for d in dets],
            "leak_check": leak,
        })
    ms = round((time.perf_counter() - t0) * 1000, 2)
    if guard:
        who = next((d.value for d in user_dets if d.type in ("EMAIL", "PHONE")), "customer")
        reply = (f"Done. I looked up the account for {who} and sent the SMS. "
                 f"The tools only ever saw tokenized values ({len(vault.tokens())} protected).")
    else:
        reply = ("Done (UNPROTECTED demo mode). The tools received your real details "
                 "in this run - see the inspector.")
    return {"reply": reply, "trace": trace, "latency_ms": ms,
            "detections": [{"type": d.type, "value": d.value} for d in user_dets]}
