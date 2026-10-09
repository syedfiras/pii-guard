# PII-Guard Middleware — 24h Hackathon MVP
AI agent -> middleware (detect+tokenize) -> simulated tool -> restore.

## Run backend
```
cd backend
pip install -r requirements.txt
python -m uvicorn app:app --port 8000 --reload
```
Health: http://127.0.0.1:8000/api/health

## Run frontend (React+Vite, see /frontend after scaffold)
```
cd frontend
npm install
npm run dev
```

## API
- POST /api/invoke {tool, payload, types?, aadhaar_strict?}
- POST /api/restore {text, mapping}
- GET /api/tool-logs

## Synthetic data only — no real PII.
