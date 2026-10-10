"""Veil Guard Python SDK — use the middleware without running the server.

    from sdk import protect, veil

    @protect("send_sms")
    def send_sms(to, body):
        ...real delivery...

    send_sms(to="9876543210", body="hi")   # tool receives fakes only

Or explicit: redacted, restore = veil.redact(payload); ...; veil.restore(answer)
Sessions: pass session_id to reuse fakes across calls in one conversation.
"""
import functools

import policy
from vault import SessionVaultStore

_STORE = SessionVaultStore()


class Veil:
    def __init__(self, store=None):
        self.store = store or _STORE

    def _cfg(self, types):
        pol = policy.active()
        want = types or policy.enabled_types()
        allowed = set(policy.enabled_types())
        return ([t for t in want if t in allowed],
                bool(pol["defaults"].get("ner", True)),
                policy.ner_thresholds(),
                pol["defaults"].get("aadhaar_strict", False),
                pol["defaults"].get("card_strict", True))

    def redact(self, payload, tool="default", types=None, session_id=None):
        from app import sanitize_obj, policy_door
        wanted, ner, thresh, aadhaar_strict, card_strict = self._cfg(types)
        sid, vault = self.store.get(session_id)
        redacted, dets = sanitize_obj(payload, vault, wanted, aadhaar_strict,
                                      card_strict, ner, thresh)
        ok, reason = policy_door(tool, dets)
        if not ok:
            return {"blocked": True, "reason": reason, "session_id": sid}
        from app import leak_check
        real = [d.value for d in dets]
        if not leak_check(str(redacted), real):
            return {"blocked": True, "reason": "leak check failed", "session_id": sid}
        return {"blocked": False, "redacted": redacted,
                "detections": [(d.type, d.value) for d in dets],
                "session_id": sid}

    def restore(self, obj, session_id):
        _, vault = self.store.get(session_id)
        return vault.restore_obj(obj)

    def wipe(self, session_id=None):
        return self.store.wipe(session_id)


veil = Veil()


def protect(tool, types=None):
    """Decorator: the wrapped tool only ever receives redacted arguments."""
    def deco(fn):
        @functools.wraps(fn)
        def inner(*args, **kwargs):
            bound = {"args": list(args), "kwargs": dict(kwargs)}
            r = veil.redact(bound, tool=tool, types=types)
            if r["blocked"]:
                raise PermissionError(f"Veil Guard blocked call to '{tool}': {r['reason']}")
            out = fn(*r["redacted"]["args"], **r["redacted"]["kwargs"])
            return veil.restore(out, r["session_id"])
        return inner
    return deco
