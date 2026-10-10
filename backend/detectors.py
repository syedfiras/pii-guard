"""PII detectors for 8 types: EMAIL, PHONE-IN, PAN, AADHAAR, CARD,
UPI_ID, PASSPORT_IN, DATE — plus optional Presidio NER (PERSON/LOCATION).
Pure regex + checksum core. No network. Deterministic for hackathon judging.
Works on free text and (via app.py) recursively on JSON.
"""
import re
from dataclasses import dataclass

EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+\-]+@[a-zA-Z0-9.\-]+\.[a-zA-Z]{2,}')
# Indian mobile: optional +91 / 0 prefix, separators allowed. Must start 6-9.
PHONE_RE = re.compile(r'(?:\+91[\s\-]?|91[\s\-]?|0)?[6-9]\d{4}[\s\-]?\d{5}\b')
PAN_RE = re.compile(r'\b[A-Z]{5}[0-9]{4}[A-Z]\b')
# Aadhaar: 12 digits, first 2-9, optional spaces/dashes. Verhoeff checked separately.
AADHAAR_RE = re.compile(r'\b[2-9]\d{3}[\s\-]?\d{4}[\s\-]?\d{4}\b')
# Card (debit/credit): 13-19 digits with optional spaces/dashes. Luhn checked separately.
# Debit vs credit cannot be distinguished by number format alone — one CARD type.
CARD_RE = re.compile(r'\b(?:\d[\s\-]?){13,19}\b')
# UPI: handle@bank with known Indian bank/app suffixes (keeps emails for EMAIL).
_UPI_BANKS = ("okhdfcbank|okicici|okaxis|oksbi|okhdfc|aubank|idfcbank|jupiteraxis|"
              "fbl|dbl|ubi|citi|hsbc|rbl|yesbank|kotak|indus|bandhan|federal|"
              "canara|unionbank|pnb|bob|hdfc|icici|axis|sbi|ybl|paytm|upi")
UPI_RE = re.compile(r'\b[\w.\-]{2,}@(?:' + _UPI_BANKS + r')\b', re.IGNORECASE)
# Indian passport: 1 letter + 7 digits.
PASSPORT_RE = re.compile(r'\b[A-Z][0-9]{7}\b')
# Calendar date DD/MM/YYYY (or with - .) — DOB/address-proof context.
DATE_RE = re.compile(r'\b(?:0?[1-9]|[12]\d|3[01])[/\-.](?:0?[1-9]|1[0-2])[/\-.](?:19|20)\d{2}\b')

# Verhoeff tables for Aadhaar checksum validation
_D = [
    [0,1,2,3,4,5,6,7,8,9],[1,2,3,4,0,6,7,8,9,5],[2,3,4,0,1,7,8,9,5,6],
    [3,4,0,1,2,8,9,5,6,7],[4,0,1,2,3,9,5,6,7,8],[5,9,8,7,6,0,4,3,2,1],
    [6,5,9,8,7,1,0,4,3,2],[7,6,5,9,8,2,1,0,4,3],[8,7,6,5,9,3,2,1,0,4],
    [9,8,7,6,5,4,3,2,1,0],
]
_P = [
    [0,1,2,3,4,5,6,7,8,9],[1,5,7,6,2,8,3,0,9,4],[5,8,0,3,7,9,6,1,4,2],
    [8,9,1,6,0,4,3,7,2,5],[9,4,5,3,1,2,6,8,7,0],[4,2,8,6,5,7,3,9,0,1],
    [2,7,9,3,8,0,6,4,1,5],[7,0,4,6,9,1,3,2,5,8],
]
_INV = [0,4,3,2,1,5,6,7,8,9]

def verhoeff_valid(num_str: str) -> bool:
    """Validate 12-digit string with Verhoeff checksum (Aadhaar uses Verhoeff)."""
    c = 0
    digits = [int(d) for d in num_str]
    for i, d in enumerate(reversed(digits)):
        c = _D[c][_P[i % 8][d]]
    return c == 0

def _digits_only(s: str) -> str:
    return re.sub(r'\D', '', s)

def luhn_valid(num_str: str) -> bool:
    """Validate digit string with Luhn checksum (debit/credit cards)."""
    total = 0
    for i, ch in enumerate(reversed(num_str)):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return total % 10 == 0

def luhn_check_digit(prefix: str) -> str:
    """Compute the Luhn check digit for a prefix (to build synthetic tokens)."""
    total = 0
    for i, ch in enumerate(reversed(prefix), start=1):
        d = int(ch)
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        total += d
    return str((10 - total % 10) % 10)

def card_brand(digits: str) -> str:
    """Informational brand from IIN prefix. Empty string if unrecognized."""
    if digits.startswith("4"):
        return "Visa"
    if len(digits) >= 2 and 51 <= int(digits[:2]) <= 55:
        return "Mastercard"
    if len(digits) >= 4 and 2221 <= int(digits[:4]) <= 2720:
        return "Mastercard"
    if digits[:2] in ("34", "37"):
        return "Amex"
    if digits[:2] in ("60", "65") or digits[:2] in ("81", "82"):
        return "RuPay"
    if digits.startswith("6"):
        return "Discover"
    return ""

@dataclass
class Detection:
    type: str
    value: str
    start: int
    end: int

def detect_email(text: str):
    return [Detection("EMAIL", m.group(), m.start(), m.end()) for m in EMAIL_RE.finditer(text)]

def detect_phone(text: str):
    out = []
    for m in PHONE_RE.finditer(text):
        digits = _digits_only(m.group())
        # strip country/prefix: keep last 10
        core = digits[-10:] if len(digits) >= 10 else digits
        if len(core) == 10 and core[0] in "6789":
            out.append(Detection("PHONE", m.group(), m.start(), m.end()))
    return out

def detect_pan(text: str):
    return [Detection("PAN", m.group(), m.start(), m.end()) for m in PAN_RE.finditer(text)]

def detect_aadhaar(text: str):
    out = []
    for m in AADHAAR_RE.finditer(text):
        raw = m.group()
        digits = _digits_only(raw)
        if len(digits) != 12:
            continue
        # reject trivial sequences (1111..., 1234...) to cut false positives
        if len(set(digits)) == 1:
            continue
        if digits in ("123456789012", "012345678901"):
            continue
        if verhoeff_valid(digits):
            out.append(Detection("AADHAAR", raw, m.start(), m.end()))
        # NOTE: for demo/synthetic data without valid checksum, caller can
        # pass strict=False to accept format-only matches. Strict=True by default.
    return out

def detect_card(text: str, strict=True):
    out = []
    for m in CARD_RE.finditer(text):
        raw = m.group().strip()
        digits = _digits_only(raw)
        if not 13 <= len(digits) <= 19:
            continue
        # reject trivial sequences (1111..., 1234...) to cut false positives
        if len(set(digits)) == 1:
            continue
        if digits in ("1234567890123456", "1234567890123456789"):
            continue
        if strict and not luhn_valid(digits):
            continue
        out.append(Detection("CARD", raw, m.start(), m.start() + len(raw)))
    return out

def detect_upi(text: str):
    return [Detection("UPI_ID", m.group(), m.start(), m.end()) for m in UPI_RE.finditer(text)]

def detect_passport(text: str):
    return [Detection("PASSPORT_IN", m.group(), m.start(), m.end()) for m in PASSPORT_RE.finditer(text)]

def detect_date(text: str):
    return [Detection("DATE", m.group(), m.start(), m.end()) for m in DATE_RE.finditer(text)]

def detect_ner(text: str, want=(), thresholds=None):
    """Presidio NER for PERSON/LOCATION/DATE. Empty list if unavailable."""
    if not want:
        return []
    try:
        from ner import analyze
    except Exception:
        return []
    return [Detection(d["type"], d["value"], d["start"], d["end"])
            for d in analyze(text, thresholds)
            if d["type"] in want]

ALL_TYPES = ("EMAIL", "PHONE", "PAN", "AADHAAR", "CARD",
             "UPI_ID", "PASSPORT_IN", "DATE", "PERSON", "LOCATION")
NER_TYPES = ("PERSON", "LOCATION")

def detect_all(text: str, types=ALL_TYPES, aadhaar_strict=True, card_strict=True,
               ner=True, ner_thresholds=None):
    """Run selected detectors. Returns non-overlapping detections sorted by start."""
    found: list[Detection] = []
    if "EMAIL" in types:
        found += detect_email(text)
    if "PHONE" in types:
        found += detect_phone(text)
    if "PAN" in types:
        found += detect_pan(text)
    if "AADHAAR" in types:
        if aadhaar_strict:
            found += detect_aadhaar(text)
        else:
            found += [Detection("AADHAAR", m.group(), m.start(), m.end())
                      for m in AADHAAR_RE.finditer(text)
                      if len(_digits_only(m.group())) == 12 and len(set(_digits_only(m.group()))) > 1]
    if "CARD" in types:
        found += detect_card(text, strict=card_strict)
    if "UPI_ID" in types:
        found += detect_upi(text)
    if "PASSPORT_IN" in types:
        found += detect_passport(text)
    if "DATE" in types:
        found += detect_date(text)
    if ner:
        want = [t for t in NER_TYPES if t in types]
        # local DATE regex already covers machine dates; NER adds human ones
        if "DATE" in types and "DATE" not in want:
            want = want + ["DATE"]
        found += detect_ner(text, want, ner_thresholds)
    # resolve overlaps: keep longest match first
    found.sort(key=lambda d: (d.start, -(d.end - d.start)))
    picked, occupied = [], set()
    for d in found:
        if any(i in occupied for i in range(d.start, d.end)):
            continue
        picked.append(d)
        occupied.update(range(d.start, d.end))
    picked.sort(key=lambda d: d.start)
    return picked
