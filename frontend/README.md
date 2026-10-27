# MediSetu Frontend

Lightweight React + TypeScript + Vite demo frontend for backend smoke testing.
It is intentionally small: the production/team frontend can replace it without
changing the API contract.

## Run

From `frontend/`:

```powershell
npm install
npm run dev
```

The Vite dev server proxies `/api` to `http://localhost:8000`.

Demo accounts seeded by `python -m app.seed_demo`:

- admin@medisetu.dev / Admin@123456
- doctor@medisetu.dev / Doctor@12345
- nurse@medisetu.dev / Nurse@12345
- pharmacy@medisetu.dev / Pharmacy@12345
- patient@medisetu.dev / Patient@12345

## Added intake features

The basic frontend now includes voice recording inside a consultation. The recorded response is sent to MediSetu's local STT pipeline, the transcript is stored, the next follow-up question is returned, and optional local TTS audio can be played in the browser.

For staff users, the consultation view also exposes a doctor-facing summary button.
