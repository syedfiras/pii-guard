"""Policy engine: YAML rulebook for what is detected and what each tool may receive.

- Per-type enable/action/threshold. action=block refuses the whole payload.
- Per-tool deny lists (fail-closed): denied type present -> BLOCKED, audited.
- Hot-reload via POST /api/policy/reload. Safe defaults if file is missing.
"""
import os

try:
    import yaml
except Exception:
    yaml = None

from detectors import ALL_TYPES

DEFAULTS = {
    "action": "tokenize",
    "aadhaar_strict": False,
    "card_strict": True,
    "ner": True,
}
TYPE_DEFAULT = {"enabled": True, "action": "tokenize", "min_score": None}

_policy = {"defaults": dict(DEFAULTS), "types": {}, "tools": {}}


def _path():
    return os.environ.get(
        "VEIL_POLICY_FILE",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "policy.yaml"),
    )


def load(path=None):
    """(Re)load policy from YAML. Returns the active policy dict."""
    global _policy
    pol = {"defaults": dict(DEFAULTS), "types": {}, "tools": {}}
    data = {}
    try:
        if yaml and os.path.exists(path or _path()):
            with open(path or _path(), encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
    except Exception as e:
        print(f"policy load failed ({e}); running on safe defaults.", flush=True)
        data = {}
    if not isinstance(data, dict):
        print("policy file is not a mapping; running on safe defaults.", flush=True)
        data = {}
    if isinstance(data.get("defaults"), dict):
        pol["defaults"].update(data["defaults"])
    for t, cfg in (data.get("types") or {}).items():
        if t in ALL_TYPES and isinstance(cfg, dict):
            merged = dict(TYPE_DEFAULT)
            merged.update(cfg)
            pol["types"][t] = merged
    for tool, cfg in (data.get("tools") or {}).items():
        if isinstance(cfg, dict):
            pol["tools"][tool] = {"deny": list(cfg.get("deny") or [])}
    _policy = pol
    return pol


def active():
    return _policy


def enabled_types():
    return [t for t in ALL_TYPES
            if _policy["types"].get(t, TYPE_DEFAULT).get("enabled", True)]


def type_cfg(t):
    cfg = dict(TYPE_DEFAULT)
    cfg.update(_policy["types"].get(t, {}))
    return cfg


def ner_thresholds():
    out = {}
    for t in ("PERSON", "LOCATION"):
        out[t] = type_cfg(t).get("min_score")
    return out


def check_tool(tool, found_types):
    """Returns (allowed: bool, reason). Deny-list + block-action enforcement."""
    deny = _policy["tools"].get(tool, {}).get("deny", [])
    hit = [t for t in found_types if t in deny]
    if hit:
        return False, f"policy denies {','.join(hit)} to tool '{tool}'"
    blocked = [t for t in found_types
               if type_cfg(t).get("action") == "block"]
    if blocked:
        return False, f"policy action=block for {','.join(blocked)}"
    return True, "ok"


load()
