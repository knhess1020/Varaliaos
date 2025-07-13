# NovaOS Backend v0.4

FastAPI + Postgres/pgvector backend powering the NovaOS personal AI.

## Quick Start

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL=postgresql://user:pass@host/db
export OPENAI_API_KEY=sk-...
uvicorn main:app --reload
```

## Nightly Consolidation

Run manually:

```bash
python consolidate.py
```

Or schedule via Supabase Edge Function CRON at 03:30 UTC.

## WebSocket

Connect: `ws://HOST/ws/{user_id}` to receive new memory JSON in real time.

