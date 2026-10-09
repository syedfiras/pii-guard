# PII-Guard Middleware — 24h Hackathon MVP
AI agent → privacy middleware (detect + tokenize) → simulated tool → restore.

```
[React UI :5173] --POST /api/invoke--> [FastAPI :8000: detectors + vault] --> [fake_tool: logs only fakes]
```

## Quick start (Windows)
```
start.bat
```
Or manually:
```
cd backend && pip install -r requirements.txt && python -m uvicorn app:app --port 8000
cd frontend && npm install && npm run dev   # open http://localhost:5173
```
Set API URL via `frontend/.env`: `VITE_API_URL=http://127.0.0.1:8000` (see `.env.example`).

## API
- `POST /api/invoke {tool, payload, types?, aadhaar_strict?, card_strict?}` → `{detections, redacted_payload, tool_saw, tool_response, restored_response, mapping, leak_check, latency_ms}`
- `POST /api/agent/chat {message, types?, guard?}` → scripted demo agent; every planned tool call forced through the guard (`guard:false` = bypass contrast mode)
- `POST /api/restore {text, mapping}`
- `GET /api/tool-logs` → audit of what the outside tool received
- `GET /api/health`

## Test results (synthetic only, 100 cases)
```
pytest tests/ → 2 passed
detection=100.0% leaks=0 restore=100/100 avg_ms=0.04 p95_ms=0.10
EMAIL / PHONE / PAN / AADHAAR / CARD: P=1.00 R=1.00
```
Run: `cd backend && python tests/test_metrics.py` or `python -m pytest tests/ -q`.
Generator: `backend/tests/generate_synthetic.py` (seeded, no real PII).

## Judging mapping
- Detection: regex + Verhoeff (Aadhaar strict mode) + overlap resolution; noisy cases (order-ID, lowercase PAN, bad prefix) documented in UI.
- Leakage prevention: fail-closed second scan + `/api/tool-logs` audit shown in UI.
- Restoration: format-preserving vault `{token: real}`, longest-first replace, verified 100/100.
- Performance: `latency_ms` per call + avg/p95 from suite.

## Synthetic data only — no real PII. No external network calls.
