"""Simulated external tool. Receives ONLY redacted payload.
Logs what it saw so judges can verify 0 real PII leakage."""
from datetime import datetime

TOOL_LOG: list[dict] = []

def simulate_tool(tool_name: str, redacted_payload):
    entry = {
        "time": datetime.utcnow().isoformat() + "Z",
        "tool": tool_name,
        "received": redacted_payload,
    }
    TOOL_LOG.append(entry)
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

def get_logs():
    return TOOL_LOG[-50:]
