"""Layered-protection token vault (all local, no network).

L1 - Unpredictable tokens: `secrets`-random per value, never sequential counters.
L2 - Encrypted at rest: real values stored only as Fernet (AES) ciphertext.
     Key comes from VEIL_VAULT_KEY or is generated fresh on every boot, so a
     restart alone orphans all old tokens (forward secrecy by default).
L3 - No plaintext anywhere: dedup lookup uses an HMAC index, so even dict
     keys contain no recoverable personal data.
L4 - Session isolation + TTL + wipe: each client session gets its own vault;
     expired sessions are swept and anyone can shred mappings on demand, after
     which old tokens can never be restored by anyone.
L5 - Optional FPE mode (VEIL_TOKEN_MODE=fpe): CARD/PHONE digits are encrypted
     with NIST FF3-1 format-preserving encryption instead of mapped. Tokens are
     valid-format numbers carrying zero stored secrets — only a per-token tweak
     (no personal data) is kept for reversal.
L6 - Key rotation: a fresh master key orphans everything (rekey+shred semantics).
"""
import hashlib
import hmac
import os
import re
import secrets
import sys
import time
import uuid

from cryptography.fernet import Fernet, InvalidToken
from ff3 import FF3Cipher

from detectors import luhn_check_digit

FPE_TYPES = ("CARD", "PHONE")


def _process_key():
    raw = os.environ.get("VEIL_VAULT_KEY")
    if raw:
        try:
            Fernet(raw.encode())
            return raw.encode()
        except Exception:
            print("VEIL_VAULT_KEY invalid (need urlsafe-base64 32 bytes); generated fresh key.",
                  file=sys.stderr)
    return Fernet.generate_key()


_MASTER_KEY = _process_key()


def rotate_master_key():
    """Fresh master key. Old ciphertext becomes unrestorable (rekey+shred)."""
    global _MASTER_KEY
    _MASTER_KEY = Fernet.generate_key()
    return True


def _process_key():
    raw = os.environ.get("VEIL_VAULT_KEY")
    if raw:
        try:
            Fernet(raw.encode())
            return raw.encode()
        except Exception:
            print("VEIL_VAULT_KEY invalid (need urlsafe-base64 32 bytes); generated fresh key.",
                  file=sys.stderr)
    return Fernet.generate_key()


def _rand_digits(n):
    return "".join(str(secrets.randbelow(10)) for _ in range(n))


def _rand_letters(n):
    import string
    alpha = string.ascii_uppercase
    return "".join(alpha[secrets.randbelow(26)] for _ in range(n))


def _card_token(real_value: str) -> str:
    """Brand-preserving Luhn-valid test number. Contains zero real digits."""
    digits = re.sub(r"\D", "", real_value)
    if len(digits) == 15:
        prefix, total, groups = "3782", 15, (4, 6, 5)  # Amex shape
    elif digits.startswith("5"):
        prefix, total, groups = "5555", 16, (4, 4, 4, 4)
    elif digits.startswith("6"):
        prefix, total, groups = "6011", 16, (4, 4, 4, 4)
    else:
        prefix, total, groups = "4111", 16, (4, 4, 4, 4)
    middle = _rand_digits(total - 1 - len(prefix))
    full = prefix + middle + luhn_check_digit(prefix + middle)
    parts, i = [], 0
    for g in groups:
        parts.append(full[i:i + g])
        i += g
    return " ".join(parts)


def _fresh_token(pii_type: str, real_value: str) -> str:
    if pii_type == "EMAIL":
        return f"vx-{secrets.token_hex(3)}@redacted.test"
    if pii_type == "PHONE":
        return f"+91-0{_rand_digits(4)}-{_rand_digits(5)}"
    if pii_type == "PAN":
        return f"QWERT{_rand_digits(4)}{_rand_letters(1)}"
    if pii_type == "AADHAAR":
        return f"2999-8888-{_rand_digits(4)}"
    if pii_type == "CARD":
        return _card_token(real_value)
    return f"__{pii_type}_{secrets.token_hex(3)}__"


def mask(value: str) -> str:
    if len(value) <= 4:
        return "...."
    return value[:2] + "...." + value[-2:]


def _fpe_key(master: bytes) -> str:
    return hashlib.sha256(master + b"veil-guard-fpe").hexdigest()


def _apply_template(raw: str, digits: str) -> str:
    out, it = [], iter(digits)
    for ch in raw:
        out.append(next(it) if ch.isdigit() else ch)
    out.extend(it)
    return "".join(out)


def _template_of(raw: str) -> str:
    return "".join("#" if ch.isdigit() else ch for ch in raw)


def _fill_template(template: str, digits: str) -> str:
    out, it = [], iter(digits)
    for ch in template:
        out.append(next(it) if ch == "#" else ch)
    out.extend(it)
    return "".join(out)


class TokenVault:
    """One session's sealed mappings. Holds zero plaintext.

    mode="map": values AES-sealed, random tokens (default, demo-clear fakes).
    mode="fpe": CARD/PHONE digits FF3-encrypted (stateless-looking valid tokens);
                other types fall back to sealed mapping.
    """

    def __init__(self, key: bytes | None = None, mode: str | None = None):
        self._master = key or _MASTER_KEY
        self._fernet = Fernet(self._master)
        self.mode = mode or os.environ.get("VEIL_TOKEN_MODE", "map")
        self._sealed: dict[str, bytes] = {}   # token -> ciphertext
        self._index: dict[str, str] = {}       # hmac(real) -> token (dedup, non-reversible)
        self._fpe: dict[str, dict] = {}        # token -> {tweak, template} (no PII)


    def _tag(self, real_value: str) -> str:
        return hmac.new(self._fernet._signing_key, real_value.encode(),
                        hashlib.sha256).hexdigest()

    def _fpe_encrypt(self, raw: str) -> tuple[str, str, str]:
        digits = re.sub(r"\D", "", raw)
        tweak = secrets.token_hex(7)
        cipher = FF3Cipher(_fpe_key(self._master), tweak)
        return _apply_template(raw, cipher.encrypt(digits)), tweak, _template_of(raw)

    def _fpe_decrypt(self, token: str) -> str | None:
        meta = self._fpe.get(token)
        if not meta:
            return None
        try:
            cipher = FF3Cipher(_fpe_key(self._master), meta["tweak"])
            return _fill_template(meta["template"], cipher.decrypt(re.sub(r"\D", "", token)))
        except Exception:
            return None

    def tokenize(self, pii_type: str, real_value: str) -> str:
        tag = self._tag(real_value)
        if tag in self._index:
            return self._index[tag]
        if self.mode == "fpe" and pii_type in FPE_TYPES:
            token, tweak, template = self._fpe_encrypt(real_value)
            while token in self._sealed or token in self._fpe:
                token, tweak, template = self._fpe_encrypt(real_value)
            self._fpe[token] = {"tweak": tweak, "template": template}
            self._index[tag] = token
            return token
        token = _fresh_token(pii_type, real_value)
        while token in self._sealed or token in self._fpe:  # paranoid; ~impossible
            token = _fresh_token(pii_type, real_value)
        self._sealed[token] = self._fernet.encrypt(real_value.encode())
        self._index[tag] = token
        return token

    def _open(self, token: str) -> str | None:
        if token in self._sealed:
            try:
                return self._fernet.decrypt(self._sealed[token]).decode()
            except (KeyError, InvalidToken):
                return None  # unknown token or wrong key: unrestorable, never garbage
        return self._fpe_decrypt(token)

    def reveal(self, token: str) -> str | None:
        return self._open(token)

    def _all_tokens(self):
        return sorted(set(self._sealed) | set(self._fpe), key=len, reverse=True)

    def restore_text(self, text: str) -> str:
        for token in self._all_tokens():
            if token in text:
                real = self._open(token)
                if real is not None:
                    text = text.replace(token, real)
        return text

    def restore_obj(self, obj):
        if isinstance(obj, str):
            return self.restore_text(obj)
        if isinstance(obj, dict):
            return {k: self.restore_obj(v) for k, v in obj.items()}
        if isinstance(obj, list):
            return [self.restore_obj(v) for v in obj]
        return obj

    def tokens(self):
        """Masked mapping for safe display. Real values NEVER leave via this."""
        out = {}
        for token in self._sealed:
            real = self._open(token)
            out[token] = mask(real) if real is not None else "...."
        for token in self._fpe:
            out[token] = "...."  # FPE: nothing stored that could unmask it
        return out

    def wipe(self):
        n = len(self._sealed) + len(self._fpe)
        self._sealed.clear()
        self._index.clear()
        self._fpe.clear()
        return n


class SessionVaultStore:
    """Session-isolated vaults with TTL. Unknown/expired sid -> fresh vault."""

    def __init__(self, ttl_seconds=1800):
        self.ttl = ttl_seconds
        self._sessions: dict[str, list] = {}  # sid -> [vault, last_used]

    def sweep(self):
        now = time.time()
        for sid in [s for s, (_, t) in self._sessions.items() if now - t > self.ttl]:
            self._sessions[sid][0].wipe()
            del self._sessions[sid]

    def get(self, sid=None):
        self.sweep()
        if sid and sid in self._sessions:
            vault, _ = self._sessions[sid]
            self._sessions[sid][1] = time.time()
            return sid, vault
        sid = uuid.uuid4().hex
        vault = TokenVault()
        self._sessions[sid] = [vault, time.time()]
        return sid, vault

    def reveal(self, sid, tokens):
        self.sweep()
        if sid not in self._sessions:
            return {}
        vault = self._sessions[sid][0]
        self._sessions[sid][1] = time.time()
        out = {}
        for t in tokens:
            real = vault.reveal(t)
            if real is not None:
                out[t] = real
        return out

    def wipe(self, sid=None):
        if sid:
            vault = self._sessions.pop(sid, None)
            return vault[0].wipe() if vault else 0
        n = sum(v.wipe() for v, _ in self._sessions.values())
        self._sessions.clear()
        return n

    def rekey(self):
        """Rotate master key AND shred everything (rekey+shred semantics)."""
        rotate_master_key()
        return self.wipe()
