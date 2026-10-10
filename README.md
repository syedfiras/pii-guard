# Veil Guard — Privacy Middleware for AI Agents

> Real data goes in. Only fakes go out. Originals are restored inside.

## 1. Problem statement

AI agents may use personal information — such as phone numbers, email addresses, and
identification numbers — to link user tools through prompts and tool parameters.
When an agent calls an external tool (sending an SMS, looking up an account, charging
a card), real personal values travel inside those tool requests and end up stored in
third-party logs, dashboards, and support tickets — far outside the application that
collected them.

A privacy layer is needed to **detect and protect sensitive values before outgoing
requests leave the application**.

## 2. How we solve it

Veil Guard is an invisible checkpoint that sits between the AI agent and every
external tool:

```
YOU  -->  [VEIL GUARD CHECKPOINT]  -->  OUTSIDE TOOL
           real kept inside (locked)      only fakes arrive
```

Every outgoing agent-to-tool payload goes through 4 steps:

1. **Intercept** — the middleware captures the payload, both structured JSON and
   natural-language text.
2. **Detect** — finds 10 kinds of private details: email addresses, Indian phone
   numbers, PAN, Aadhaar, debit/credit cards, UPI IDs, Indian passports, dates,
   plus person names and places via on-device AI (Microsoft Presidio + spaCy —
   free, local, no network). ID numbers get checksum double-checks (Verhoeff for
   Aadhaar, Luhn for cards) so random numbers don't trigger false alarms.
3. **Protect** — swaps each real value for a same-shaped fake
   (`4111 1111 1111 1111` → `4111 0000 0000 0024`), so tools keep working while
   their logs stay worthless to attackers. A second scan blocks the request
   entirely if any real value survives (fail-closed).
4. **Restore** — tool answers containing fakes are mapped back to the real values
   before the agent or user sees them.

A demo dashboard (this repo's website) makes the invisible visible: it shows your
message, what the tool actually got, and what you got back — plus a step where a
scripted demo agent uses tools by itself while you watch what each tool received.

## 3. Overall architecture

```
                        +-----------------------------+
                        |      VEIL GUARD (FastAPI)   |
                        |  detectors + vault + audit  |
 [React UI :5173] ---> |                             | ---> [simulated tool]
  dashboard             |  POST /api/invoke           |      sees FAKES only
  (proof screens)       |  POST /api/agent/chat       |
                        |  GET  /api/evidence         |
                        +-----------------------------+
```

- **Frontend** (`frontend/`, React + Vite) never does detection — it only displays
  what the backend returns: findings, side-by-side panels, test runs, the proof log.
- **Backend** (`backend/`, FastAPI) owns all privacy logic:
  - `detectors.py` — 5 pattern + checksum detectors, overlap resolution.
  - `vault.py` — in-memory real↔fake mapping, format-preserving fake generation.
  - `demo_agent.py` — scripted demo agent; every planned tool call is forced
    through the guard (`guard:false` bypasses, to show the leak contrast).
  - `fake_tool.py` — simulated external tool; appends every received payload to
    `audit.jsonl` (persisted, git-ignored) so the evidence survives restarts.
- **History** — dashboard counts persist in the browser (localStorage, counts only,
  never messages); audit entries persist on disk server-side.

## 4. Technologies used

| Layer    | Technology | Used for |
|----------|-----------|----------|
| Backend  | Python + FastAPI, Uvicorn, Pydantic | API, request validation, server |
| Detection| Python `re` + Verhoeff/Luhn + Presidio NER (spaCy) | 10 types, all on-device and free — deterministic rules for IDs, ML for names/places, degrades to rules-only if models missing |
| Hiding   | Fernet (AES) encrypted vault + `secrets`-random tokens, optional NIST FF3-1 format-preserving encryption | Same-shape fakes; real values exist only as ciphertext, key fresh every boot unless `VEIL_VAULT_KEY` is set; FPE mode (`VEIL_TOKEN_MODE=fpe`) makes card/phone fakes indistinguishable valid numbers with zero stored secrets |
| Frontend | React 19 + Vite | Dashboard: check-a-message, agent demo, tests, proof log |
| Styling  | Plain CSS, paper-and-ink dossier theme | No UI framework, zero new dependencies |
| Tests    | pytest + seeded synthetic generator | 100 made-up cases incl. tricky negatives |
| Docs     | `PRD.md`, `OVERVIEW.md`, `submission/` | Requirements, architecture, prototype PDF |

No external network calls. No database. Synthetic test data only.

## 5. Key features
- **10 PII types**: email, Indian phone, PAN, Aadhaar, debit/credit card (one honest
  card detector), UPI IDs, Indian passports, dates, plus person names and places
  via on-device AI.
- **Policy rulebook** (`backend/policy.yaml`): which details are looked for,
  per-tool deny lists (e.g. cards never reach analytics - enforced fail-closed),
  hot-reload without restart.
- **Two token modes**: obvious fakes (demo clarity) or NIST FF3-1
  format-preserving encryption (`VEIL_TOKEN_MODE=fpe`) whose tokens are
  indistinguishable valid numbers with zero stored secrets.
- **Tamper-evident proof log**: hash-chained entries (`GET /api/chain` verifies),
  persisted to disk, downloadable - fakes only, always.
- **Enforcement demo**: the scripted agent can't bypass the guard; flip protection
  OFF to watch a leak happen on purpose.
- **Fail-closed second scan**: any surviving real value blocks the request.
- **Proof log + evidence file**: every payload the tool got, searchable in the UI
  and downloadable as JSON — sanitized copies only, never originals or mappings.
- **Refresh-proof history**: past checks and test results stay on the computer,
  with per-row and clear-all delete.
- **Plain-words UI**: written so a non-technical person understands every screen;
  limits ("what it can't do yet") stated openly in the app.
- **Fast**: ~0.04 ms average added per check.

## 6. Protection layers (why stolen fakes are useless)

1. **Unpredictable fakes** — every token is cryptographically random (`secrets`),
   never sequential. Seeing one fake reveals nothing about the next.
2. **Locked storage** — real values are stored only as AES-encrypted ciphertext
   (Fernet). The lookup index is an HMAC, so no plaintext exists anywhere — not
   even as dictionary keys.
3. **Fresh lock key every restart** — unless `VEIL_VAULT_KEY` is set, rebooting
   orphans all old fakes. A wrong key restores nothing (never garbage).
4. **Separate locked boxes per session** — each client session gets its own vault
   (30-minute expiry + auto-sweep), so one leaked session exposes nothing else.
5. **Masked by default, audited reveal** — API responses carry only masked
   mappings (`98....10`). Real values are returned solely via
   `POST /api/vault/reveal`, and every reveal is written to the proof log.
6. **Shred on demand** — `POST /api/vault/wipe` (or the Connection page button)
   destroys mappings; shredded fakes can never be turned back, by anyone.
7. **Proof log holds fakes only** — the audit file never contains originals or
   mappings, and blocked requests are logged as `BLOCKED` with nothing forwarded.

## 7. Quick start (Windows)

```
start.bat
```

Or manually:

```
cd backend && pip install -r requirements.txt && python -m uvicorn app:app --port 8000
cd frontend && npm install && npm run dev   # open http://localhost:5173
```

API base override: `frontend/.env` → `VITE_API_URL=http://127.0.0.1:8000`
(see `frontend/.env.example`).

## 8. API

- `POST /api/invoke {tool, payload, types?, aadhaar_strict?, card_strict?, session_id?}` →
  `{session_id, detections, redacted_payload, tool_saw, tool_response, restored_response, mapping (MASKED), leak_check, latency_ms}`
- `POST /api/agent/chat {message, types?, guard?, session_id?}` → scripted agent run with
  per-call trace (`attempted` vs `sent` + verdict per tool); reusing `session_id`
  keeps the same fakes across turns.
- `POST /api/vault/reveal {session_id, tokens}` → real values; every reveal is
  written to the proof log.
- `POST /api/vault/wipe {session_id?}` → destroys mappings (all sessions if omitted).
- `POST /api/vault/rotate` → fresh master key + shred everything.
- `GET /api/policy` → active rulebook; `POST /api/policy/reload` → reload from file.
- `GET /api/chain` → hash-chain integrity `{intact, bad_index, entries}`.
- `POST /api/restore {text, mapping}` → direct restore with a caller-supplied mapping.
- `GET /api/tool-logs` → what the outside tool received (last 50).
- `GET /api/evidence` → downloadable proof file (summary + up to 200 entries).
- `GET /api/health`

Lock key: set `VEIL_VAULT_KEY` to a Fernet key to keep mappings across restarts;
otherwise a fresh key is generated on every boot (old fakes become unrestorable).

## 9. Test results (synthetic data only, 100 cases)

```
pytest tests/ → 21 passed
detection=100.0%  leaks=0  restore=100/100  avg_ms=0.04  p95_ms=0.10
EMAIL / PHONE / PAN / AADHAAR / CARD: precision=1.00 recall=1.00
```

Run: `cd backend && python -m pytest tests/ -q`.
Generator: `backend/tests/generate_synthetic.py` (seeded, no real personal data).
Product-layer tests: `test_product.py` (policy, chain, FPE, rotation, SDK),
`test_vault.py` (8 vault-layer proofs).

## 10. Deploy with Docker

```
docker compose up --build   # backend :8000, frontend :5173
```

Audit log lives in a `veil-audit` volume. Set `VEIL_VAULT_KEY` in
`docker-compose.yml` to keep vault mappings across restarts, or omit it for a
fresh key every boot. NER models download during the image build
(`en_core_web_sm`; Presidio auto-fetches its model on first use).

## 11. Use it from Python (no server needed)

```python
from sdk import protect

@protect("send_sms")          # the function below only ever sees fakes
def send_sms(to, body):
    ...real delivery...

send_sms(to="9876543210", body="hi")
```

Policy deny-lists are enforced here too — a denied call raises `PermissionError`
and nothing is sent.

## 12. Fairness & scope note

Designed, built, and tested with **synthetic personal data only**. No real personal
or confidential information was used, submitted, or sent to any external service.
Names and places now use on-device ML (Presidio + spaCy); still out of scope:
CVV/expiry codes (any 3-digit number alone is too ambiguous). Mappings live in
server memory only — restart, wipe, or rotation destroys them; for production,
back the vault with a KMS-held key and a persistent encrypted store.
