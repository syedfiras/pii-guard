"""FastAPI middleware: intercept -> detect -> tokenize -> fake tool -> restore."""
import time
from typing import Any, Optional
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from detectors import detect_all, ALL_TYPES
from vault import TokenVault, SessionVaultStore, rotate_master_key
from fake_tool import simulate_tool, get_logs, record_blocked, evidence, record_reveal, verify_chain
from demo_agent import run_agent
import policy

VAULTS = SessionVaultStore(ttl_seconds=1800)  # L4: isolated per session, swept, wipable

app = FastAPI(title="Veil Guard Middleware")
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
    card_strict: bool = True  # True = require Luhn checksum (recommended)
    session_id: Optional[str] = None  # reuse a vault; omitted -> fresh vault

class RestoreReq(BaseModel):
    text: str
    mapping: Optional[dict[str, str]] = None

class AgentChatReq(BaseModel):
    message: str
    types: Optional[list[str]] = None
    guard: bool = True  # False = bypass contrast mode (simulated tool still)
    session_id: Optional[str] = None  # same tokens across turns when reused

class VaultRevealReq(BaseModel):
    session_id: str
    tokens: list[str]

class VaultWipeReq(BaseModel):
    session_id: Optional[str] = None  # omitted -> shred every session

def effective_types(requested):
    """Server policy is authoritative: client wishes intersect policy enables."""
    want = requested or list(ALL_TYPES)
    allowed = set(policy.enabled_types())
    return [t for t in want if t in allowed]


def policy_door(tool, dets):
    """Policy deny-list + block-action gate. Returns (allowed, reason)."""
    return policy.check_tool(tool, [d.type for d in dets])

def sanitize_text(text: str, vault: TokenVault, types, aadhaar_strict, card_strict=True,
                  ner=True, ner_thresholds=None):
    dets = detect_all(text, tuple(types), aadhaar_strict=aadhaar_strict, card_strict=card_strict,
                      ner=ner, ner_thresholds=ner_thresholds)
    # replace from end -> start so offsets stay valid
    redacted = text
    for d in sorted(dets, key=lambda x: x.start, reverse=True):
        tok = vault.tokenize(d.type, d.value)
        redacted = redacted[:d.start] + tok + redacted[d.end:]
    return redacted, dets

def sanitize_obj(obj: Any, vault: TokenVault, types, aadhaar_strict, card_strict=True,
                 ner=True, ner_thresholds=None):
    if isinstance(obj, str):
        return sanitize_text(obj, vault, types, aadhaar_strict, card_strict, ner, ner_thresholds)
    if isinstance(obj, dict):
        out, all_dets = {}, []
        for k, v in obj.items():
            rv, dets = sanitize_obj(v, vault, types, aadhaar_strict, card_strict, ner, ner_thresholds)
            out[k] = rv
            all_dets += dets
        return out, all_dets
    if isinstance(obj, list):
        out_list, all_dets = [], []
        for v in obj:
            rv, dets = sanitize_obj(v, vault, types, aadhaar_strict, card_strict, ner, ner_thresholds)
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
    types = effective_types(req.types)
    ner_on = bool(policy.active()["defaults"].get("ner", True))
    sid, vault = VAULTS.get(req.session_id)
    redacted, dets = sanitize_obj(req.payload, vault, types, req.aadhaar_strict, req.card_strict,
                                  ner_on, policy.ner_thresholds())
    real_values = [d.value for d in dets]
    # policy gate first: denied/blocked types refuse the whole call
    allowed, reason = policy_door(req.tool, dets)
    if not allowed:
        record_blocked(req.tool)
        return {"error": "POLICY_BLOCKED", "reason": reason, "blocked": True}
    # fail-closed second scan: ensure no real value survived
    flat = str(redacted)
    leak_pass = leak_check(flat, real_values)
    if not leak_pass:
        record_blocked(req.tool)
        return {"error": "LEAK_DETECTED", "blocked": True}
    tool_resp = simulate_tool(req.tool, redacted, "PASS")
    restored = vault.restore_obj(tool_resp)
    ms = round((time.perf_counter() - t0) * 1000, 2)
    return {
        "session_id": sid,
        "detections": [{"type": d.type, "value": d.value} for d in dets],
        "redacted_payload": redacted,
        "tool_saw": redacted,
        "tool_response": tool_resp,
        "restored_response": restored,
        "mapping": vault.tokens(),  # MASKED only; reveal via /api/vault/reveal
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

@app.get("/api/evidence")
def evidence_pack():
    """Downloadable evidence: every payload the simulated tool received + summary."""
    return evidence()

@app.post("/api/agent/chat")
def agent_chat(req: AgentChatReq):
    if not req.message or not req.message.strip():
        return {"error": "empty message"}
    types = effective_types(req.types)
    sid, vault = VAULTS.get(req.session_id)
    def _agent_tool(tool, payload, verdict):
        return simulate_tool(tool, payload, verdict)
    out = run_agent(req.message.strip(), types, req.guard, _agent_tool, vault=vault,
                    ner=bool(policy.active()["defaults"].get("ner", True)),
                    ner_thresholds=policy.ner_thresholds())
    out["session_id"] = sid
    return {"guard": req.guard, **out}

@app.post("/api/vault/reveal")
def vault_reveal(req: VaultRevealReq):
    """Audited single-token reveal. Every reveal is written to the audit log."""
    revealed = VAULTS.reveal(req.session_id, req.tokens)
    for tok in revealed:
        record_reveal(tok)
    return {"revealed": revealed}

@app.post("/api/vault/wipe")
def vault_wipe(req: VaultWipeReq):
    """Shred session mappings. Old tokens become unrestorable by anyone."""
    return {"wiped_tokens": VAULTS.wipe(req.session_id)}

@app.post("/api/vault/rotate")
def vault_rotate():
    """Fresh master key + shred everything (rekey+shred semantics)."""
    rotate_master_key()
    return {"rotated": True, "shredded_tokens": VAULTS.wipe()}

@app.get("/api/policy")
def get_policy():
    p = policy.active()
    return {"defaults": p["defaults"], "types": p["types"], "tools": p["tools"]}

@app.post("/api/policy/reload")
def reload_policy():
    policy.load()
    return {"reloaded": True, "enabled_types": policy.enabled_types()}

@app.get("/api/chain")
def chain_status():
    ok, bad = verify_chain()
    return {"intact": ok, "bad_index": bad, "entries": len(get_logs())}
