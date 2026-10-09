# PRD — PII-Guard Middleware (24h Hackathon MVP)

## 1. Problem
AI agents send user data to external tools via prompts/tool params.
Phone numbers, email addresses, PAN, and Aadhaar numbers can leak to
third-party tools and logs. A privacy layer is needed that intercepts
outgoing agent-to-tool payloads, detects PII, replaces real values with
reversible tokens, and restores correct values in responses — without
breaking payload meaning, and with proof that real PII never reached
the simulated external tool.

## 2. Goals
- Intercept agent → tool payloads (structured JSON + natural-language text).
- Detect 5 PII types: EMAIL, PHONE-IN, PAN, AADHAAR, CARD (debit/credit).
- Replace real values with format-preserving reversible tokens.
- Guarantee 0 real protected PII reaches the simulated tool (fail-closed).
- Restore tokens to originals in tool responses.
- Demonstrate redaction, re-hydration, and test results in a web demo.
- Score on Detection / Leakage prevention / Restoration / Performance.

## Non-goals (24h scope cut)
- No real PII, no external network calls, no persistent database.
- No person-name NER, addresses, or regional-language detection (regex MVP).
- No encryption-at-rest, no multi-tenant auth, no session persistence.
- No LangChain / OpenAI dependency — mocked agent + simulated tool only.

## 3. Users
- Hackathon judges (score the 4 criteria + live demo).
- Presenters (run the 2-minute demo).
- Developers (extend detectors / add types).

## 4. Functional scope
1. `POST /api/invoke {tool, payload, types?, aadhaar_strict?}` →
   `{detections, redacted_payload, tool_saw, tool_response,
     restored_response, mapping, leak_check, latency_ms}`
2. Detection (`backend/detectors.py`):
   EMAIL regex, PHONE-IN with +91/0 prefix + 6-9 start rule,
   PAN `ABCDE1234F` uppercase spec, AADHAAR format + Verhoeff checksum
   in strict mode, CARD 13–19 digits + Luhn checksum (debit and credit
   share one type — numbers alone cannot distinguish them),
   overlap resolution (longest wins).
3. Vault (`backend/vault.py`): in-memory `{token: real}` with fakes
   `user_0001@redacted.test`, `+91-00000-00001`, `QWERT0001Z`,
   `2999-8888-0001`, brand-preserving Luhn-valid test card numbers.
   Longest-first restore.
4. Simulated tool (`backend/fake_tool.py`): receives redacted only,
   appends to `TOOL_LOG`. `GET /api/tool-logs` exposes audit.
5. Fail-closed second scan (`leak_check`); `POST /api/restore`,
   `GET /api/health`.
6. Web UI (`frontend/src/`): pipeline bar
   (You type → Guard scans → Tool sees FAKE → You get REAL),
   7 presets (all/email/phone/pan/aadhaar/debit/credit), type toggles + strict
   Aadhaar toggle, 3 plain-language cards
   (typed=red / tool-got=yellow / restored=green),
   Fake↔Real table, preset test runner + audit-log viewer + failure list.
7. Tests (`backend/tests/`): `generate_synthetic.py` (seed 42, 100 cases
   incl. card + noisy negatives), `test_basic.py`, `test_metrics.py`
   (per-type precision/recall, leak count, restore check, avg/p95 ms).

## 5. UX flow
Pick preset or type → Protect & Send → verdict `SAFE + N hidden + ms` →
compare 3 panels → open Fake↔Real mapping → Run tests / Show audit log.

## 6. Acceptance (maps to judging criteria)
- Detection ≥ 80% on common test set (current: 100% on 100 synthetic).
- Leakage prevention: `leak_check: PASS` + audit log contains 0 real values.
- Restoration: 100/100 round-trips via vault.
- Performance: per-call `latency_ms` + suite avg ~0.03ms / p95 ~0.07ms,
  plus documented failure cases.

## 7. Known failure cases (shown in UI, be honest with judges)
- 12-digit order ID (e.g. `123456789012`) resembles Aadhaar — rejected by
  Verhoeff/sequence filter in strict mode; format-only mode may flag it.
- Lowercase PAN (`abcde1234f`) ignored — PAN is uppercase-only by spec.
- Numbers starting 1-5 (e.g. `5123456789`) are not Indian mobiles — ignored.
- 16-digit numbers with a bad Luhn checksum are not cards — ignored.
- CVV/expiry are out of scope: any 3-digit number is too ambiguous to detect alone.
- Overlapping spans keep the longest match; handwritten / regional names
  not covered by this regex MVP.

## 8. Constraints & fairness
- Synthetic data only. No real personal or confidential information.
- Local run: backend `:8000`, frontend `:5173`,
  override via `frontend/.env` `VITE_API_URL` (see `.env.example`).
- Windows quick start: `start.bat`. No external service calls.

## 9. Milestones
Done: backend → understandable UI → 100-case metrics → packaging/README.
Optional next: session-persistent vault (multi-turn), latency chart,
Docker image.
