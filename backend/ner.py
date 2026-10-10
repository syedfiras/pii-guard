"""Optional ML layer: Microsoft Presidio + spaCy NER for PERSON / LOCATION / DATE.

Free, local, no network. Lazy singleton: models load on first use, and any
failure (missing model, no memory) degrades to regex-only instead of crashing.
Thresholds are policy-overridable; see policy.yaml.
"""
import threading

_AVAILABLE = None
_ENGINE = None
_LOCK = threading.Lock()

ENTITY_MAP = {
    "PERSON": "PERSON",
    "LOCATION": "LOCATION",
    "GPE": "LOCATION",
    "DATE_TIME": "DATE",
}

DEFAULT_THRESHOLDS = {"PERSON": 0.60, "LOCATION": 0.65, "DATE": 0.70}


def available():
    global _AVAILABLE
    if _AVAILABLE is None:
        try:
            import presidio_analyzer  # noqa: F401
            import spacy  # noqa: F401
            _AVAILABLE = True
        except Exception:
            _AVAILABLE = False
    return _AVAILABLE


def _engine():
    global _ENGINE
    if _ENGINE is None:
        with _LOCK:
            if _ENGINE is None:
                from presidio_analyzer import AnalyzerEngine
                _ENGINE = AnalyzerEngine()
    return _ENGINE


def analyze(text, thresholds=None):
    """Returns list of dicts {type, value, start, end, score}. Empty on any failure."""
    if not text or not text.strip() or not available():
        return []
    th = dict(DEFAULT_THRESHOLDS)
    if thresholds:
        th.update({k: v for k, v in thresholds.items() if v is not None})
    try:
        results = _engine().analyze(
            text=text, language="en",
            entities=list({e for e in ENTITY_MAP}),
        )
    except Exception:
        return []
    out = []
    for r in results:
        mapped = ENTITY_MAP.get(r.entity_type)
        if not mapped or r.score < th.get(mapped, 0.6):
            continue
        out.append({"type": mapped, "value": text[r.start:r.end],
                    "start": r.start, "end": r.end, "score": round(float(r.score), 3)})
    return out
