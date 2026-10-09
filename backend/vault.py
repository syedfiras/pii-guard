"""Reversible format-preserving token vault. In-memory for 24h MVP."""
import re
import uuid

class TokenVault:
    def __init__(self):
        self.token_to_real: dict[str, str] = {}
        self.real_to_token: dict[str, str] = {}
        self.counters = {"EMAIL": 0, "PHONE": 0, "PAN": 0, "AADHAAR": 0}

    def tokenize(self, pii_type: str, real_value: str) -> str:
        if real_value in self.real_to_token:
            return self.real_to_token[real_value]
        self.counters[pii_type] += 1
        n = self.counters[pii_type]
        if pii_type == "EMAIL":
            token = f"user_{n:04d}__@redacted.test"
        elif pii_type == "PHONE":
            token = f"+91-00000-{n:05d}"
        elif pii_type == "PAN":
            token = f"QWERT{n:04d}Z"  # keeps ABCDE1234F shape
        elif pii_type == "AADHAAR":
            token = f"2999-8888-{n:04d}"
        else:
            token = f"__{pii_type}_{uuid.uuid4().hex[:6]}__"
        self.token_to_real[token] = real_value
        self.real_to_token[real_value] = token
        return token

    def restore_text(self, text: str) -> str:
        # longest tokens first so no partial replace
        for token in sorted(self.token_to_real, key=len, reverse=True):
            if token in text:
                text = text.replace(token, self.token_to_real[token])
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
        return dict(self.token_to_real)
