# Overview — PII-Guard Middleware

Privacy layer between AI agent and external tools: detect PII, send fakes
out, restore reals back. Web demo + measurable test results. Synthetic data only.

## Architecture

```
[React Vite :5173] --POST /api/invoke--> [FastAPI :8000]
  pages/Playground presets/input         detectors.py (EMAIL/PHONE/PAN/AADHAAR/CARD)
                                       vault.py (tokenize: real -> fake)
                                       fake_tool.py (receives fakes, TOOL_LOG)
                                       restore (fake -> real) + leak_check + latency_ms
```

Flow: `Agent payload -> INTERCEPT -> DETECT -> TOKENIZE -> fake to tool ->
tool response (tokens) -> RESTORE -> agent/user`.

## Repo map

- `backend/app.py` — routes (`/api/invoke`, `/api/agent/chat`, `/api/restore`,
  `/api/tool-logs`, `/api/health`), recursive `sanitize_obj`, fail-closed `leak_check`.
- `backend/detectors.py` — 5 detectors (EMAIL/PHONE/PAN/AADHAAR/CARD) + `detect_all()`.
- `backend/vault.py` — `TokenVault` with format-preserving fakes + restore.
- `backend/fake_tool.py` — `simulate_tool()` + `TOOL_LOG` audit.
- `backend/demo_agent.py` — scripted agent; every planned call forced through the guard.
- `backend/tests/generate_synthetic.py` — seeded 100-case generator (no real PII).
- `backend/tests/test_basic.py`, `test_metrics.py` — sanity + P/R/leak/restore/perf.
- `frontend/src/pages/Playground.jsx` — redaction desk, presets, exhibits table, ledger.
- `frontend/src/pages/AgentDemo.jsx` — agent wiretap: chat + intercepted-call inspector.
- `frontend/src/pages/Tests.jsx`, `AuditLogs.jsx`, `ApiHealth.jsx`, `Overview.jsx`.
- `frontend/.env.example` — `VITE_API_URL` override.
- `start.bat`, `README.md`, `PRD.md`, `OVERVIEW.md`.

## Run

```
start.bat
```
Or manually:
```
cd backend && pip install -r requirements.txt && python -m uvicorn app:app --port 8000
cd frontend && npm install && npm run dev   # open http://localhost:5173
```

## API

- `POST /api/invoke {tool, payload, types?, aadhaar_strict?, card_strict?}`
- `POST /api/agent/chat {message, types?, guard?}` — guard:false bypasses (contrast demo)
- `POST /api/restore {text, mapping}`
- `GET /api/tool-logs` — what the outside tool actually received
- `GET /api/health`

## Test results (100 synthetic cases)

```
pytest tests/ -> 2 passed
detection=100.0% leaks=0 restore=100/100 avg_ms=0.04 p95_ms=0.10
EMAIL / PHONE / PAN / AADHAAR / CARD: P=1.00 R=1.00
```

Run: `cd backend && python -m pytest tests/ -q` or `python tests/test_metrics.py`.

## 2-minute demo script

1. Click `All combined` → `Protect & Send` → show `SAFE + 4 hidden` + chips.
2. Point at red panel (real stayed) vs yellow panel (tool got fakes only).
3. Open audit log — no real values present. Click `Run 5 tests`.
4. Admit one failure (order-ID vs Aadhaar) and flip the strict toggle.
