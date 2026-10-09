"""Simulated external tool. Receives ONLY redacted payload.
Logs what it saw so judges can verify 0 real PII leakage.

Persistence: every entry is appended to audit.jsonl (path overridable via
VEIL_AUDIT_FILE, used by tests) and reloaded on startup, so evidence
survives backend restarts. Sanitized payloads only — never vault mappings.
"""
import json
import os
from datetime import datetime

TOOL_LOG: list[dict] = []


def _audit_path():
    return os.environ.get(
        "VEIL_AUDIT_FILE",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "audit.jsonl"),
    )


def _load():
    path = _audit_path()
    if not os.path.exists(path):
        return
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    TOOL_LOG.append(json.loads(line))
    except (OSError, ValueError):
        pass  # corrupt/partial trailing line must never break startup


_load()


def _append(entry):
    TOOL_LOG.append(entry)
    try:
        with open(_audit_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except OSError:
        pass  # audit write failure must never block the request path


def simulate_tool(tool_name: str, redacted_payload, verdict="PASS"):
    entry = {
        "time": datetime.utcnow().isoformat() + "Z",
        "tool": tool_name,
        "verdict": verdict,
        "received": redacted_payload,
    }
    _append(entry)
    # Echo back a response that may contain tokens (needs restoration upstream)
    if isinstance(redacted_payload, dict):
        text = str(redacted_payload)
    else:
        text = str(redacted_payload)
    return {
        "status": "ok",
        "tool": tool_name,
        "result": f"Processed: {text[:500]}",
        "received_keys": list(redacted_payload.keys()) if isinstance(redacted_payload, dict) else [],
    }


def record_blocked(tool_name: str):
    _append({
        "time": datetime.utcnow().isoformat() + "Z",
        "tool": tool_name,
        "verdict": "BLOCKED",
        "received": {"blocked": True, "reason": "leak check failed; nothing forwarded"},
    })


def get_logs():
    return TOOL_LOG[-50:]


def evidence():
    calls = [e for e in TOOL_LOG if e.get("verdict") != "BLOCKED"]
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "product": "Veil Guard",
        "note": "Sanitized payloads only. No original values or vault mappings stored.",
        "summary": {
            "total_tool_calls": len(calls),
            "passed_leak_check": sum(1 for e in calls if e.get("verdict") == "PASS"),
            "blocked_before_send": sum(1 for e in TOOL_LOG if e.get("verdict") == "BLOCKED"),
        },
        "logs": TOOL_LOG[-200:],
    }
