"""Simulated external tool. Receives ONLY redacted payload.
Logs what it saw so judges can verify 0 real PII leakage.

Persistence: every entry is appended to audit.jsonl (path overridable via
VEIL_AUDIT_FILE, used by tests) and reloaded on startup, so evidence
survives backend restarts. Sanitized payloads only — never vault mappings.

Integrity: hash-chained ledger. Each entry stores sha256(prev_hash + canonical
entry); verify_chain() detects any tampering, deletion, or reordering.
"""
import hashlib
import json
import os
from datetime import datetime, timezone

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


def _hash(entry_without_hash: dict) -> str:
    canonical = json.dumps(entry_without_hash, sort_keys=True, separators=(",", ":"),
                           default=str)
    return hashlib.sha256(canonical.encode()).hexdigest()


def _append(entry):
    last = TOOL_LOG[-1] if TOOL_LOG else None
    entry["prev"] = last.get("hash", "LEGACY") if last else "GENESIS"
    entry["hash"] = _hash({k: v for k, v in entry.items() if k != "hash"})
    TOOL_LOG.append(entry)
    try:
        with open(_audit_path(), "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")
    except OSError:
        pass  # audit write failure must never block the request path


def verify_chain(entries=None):
    """Returns (ok, bad_index). Recomputes every link; catches edits/deletes/reorders.
    Pre-chain legacy entries (no hash) are skipped, not condemned."""
    log = entries if entries is not None else TOOL_LOG
    last_hash, seen = None, False
    for i, e in enumerate(log):
        if "hash" not in e:
            seen = True
            continue
        expected = last_hash if last_hash else ("LEGACY" if seen else "GENESIS")
        if e.get("prev") != expected:
            return False, i
        if _hash({k: v for k, v in e.items() if k != "hash"}) != e.get("hash"):
            return False, i
        last_hash, seen = e["hash"], True
    return True, -1


def simulate_tool(tool_name: str, redacted_payload, verdict="PASS"):
    entry = {
        "time": datetime.now(timezone.utc).isoformat(),
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
        "time": datetime.now(timezone.utc).isoformat(),
        "tool": tool_name,
        "verdict": "BLOCKED",
        "received": {"blocked": True, "reason": "leak check failed; nothing forwarded"},
    })


def record_reveal(token: str):
    """Accountability: every server-side reveal leaves a trace (token only, never the value)."""
    _append({
        "time": datetime.now(timezone.utc).isoformat(),
        "tool": "vault",
        "verdict": "REVEAL",
        "received": {"revealed_token": token},
    })


def get_logs():
    return TOOL_LOG[-50:]


def evidence():
    calls = [e for e in TOOL_LOG if e.get("verdict") not in ("BLOCKED", "REVEAL")]
    ok, bad = verify_chain()
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "product": "Veil Guard",
        "note": "Sanitized payloads only. No original values or vault mappings stored.",
        "chain": {"intact": ok, "bad_index": bad, "entries": len(TOOL_LOG)},
        "summary": {
            "total_tool_calls": len(calls),
            "passed_leak_check": sum(1 for e in calls if e.get("verdict") == "PASS"),
            "blocked_before_send": sum(1 for e in TOOL_LOG if e.get("verdict") == "BLOCKED"),
            "audited_reveals": sum(1 for e in TOOL_LOG if e.get("verdict") == "REVEAL"),
        },
        "logs": TOOL_LOG[-200:],
    }
