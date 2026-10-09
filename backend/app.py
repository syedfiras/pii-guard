"""FastAPI middleware: intercept -> detect -> tokenize -> fake tool -> restore."""
import time
from typing import Any, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from detectors import detect_all
from vault import TokenVault
from fake_tool import simulate_tool, get_logs

app = FastAPI(title="PII-Guard Middleware")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173", "*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class InvokeReq(BaseModel):
    tool: str = "send_sms"
    payload: Any
    types: Optional[list[str]] = None
    aadhaar_strict: bool = False  # False = format-only (demo friendly), True = Verhoeff

class RestoreReq(BaseModel):
    text: str
    mapping: Optional[dict[str, str]] = None

def sanitize_text(text: str, vault: TokenVault, types, aadhaar_strict):
    dets = detect_all(text, tuple(types), aadhaar_strict=aadhaar_strict)
    # replace from end -> start so offsets stay valid
    redacted = text
    for d in sorted(dets, key=lambda x: x.start, reverse=True):
        tok = vault.tokenize(d.type, d.value)
        redacted = redacted[:d.start] + tok + redacted[d.end:]
    return redacted, dets

def sanitize_obj(obj: Any, vault: TokenVault, types, aadhaar_strict):
    if isinstance(obj, str):
        return sanitize_text(obj, vault, types, aadhaar_strict)
    if isinstance(obj, dict):
        out, all_dets = {}, []
        for k, v in obj.items():
            rv, dets = sanitize_obj(v, vault, types, aadhaar_strict)
            out[k] = rv
            all_dets += dets
        return out, all_dets
    if isinstance(obj, list):
        out_list, all_dets = [], []
        for v in obj:
            rv, dets = sanitize_obj(v, vault, types, aadhaar_strict)
            out_list.append(rv)
            all_dets += dets
        return out_list, all_dets
    return obj, []

def leak_check(redacted_str: str, real_values: list[str]) -> bool:
    """True = PASS (no real value present)."""
    return all(rv not in redacted_str for rv in real_values)

@app.get("/api/health")
def health():
    return {"ok": True}

@app.post("/api/invoke")
def invoke(req: InvokeReq):
    t0 = time.perf_counter()
    types = req.types or ["EMAIL", "PHONE", "PAN", "AADHAAR"]
    vault = TokenVault()
    redacted, dets = sanitize_obj(req.payload, vault, types, req.aadhaar_strict)
    real_values = [d.value for d in dets]
    # fail-closed second scan: ensure no real value survived
    flat = str(redacted)
    leak_pass = leak_check(flat, real_values)
    if not leak_pass:
        return {"error": "LEAK_DETECTED", "blocked": True}
    tool_resp = simulate_tool(req.tool, redacted)
    restored = vault.restore_obj(tool_resp)
    ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "detections": [{"type": d.type, "value": d.value} for d in dets],
        "redacted_payload": redacted,
        "tool_saw": redacted,
        "tool_response": tool_resp,
        "restored_response": restored,
        "mapping": vault.tokens(),
        "leak_check": "PASS" if leak_pass else "FAIL",
        "latency_ms": ms,
    }

@app.post("/api/restore")
def restore(req: RestoreReq):
    out = req.text
    if req.mapping:
        for tok in sorted(req.mapping, key=len, reverse=True):
            out = out.replace(tok, req.mapping[tok])
    return {"restored": out}

@app.get("/api/tool-logs")
def tool_logs():
    return {"logs": get_logs()}
