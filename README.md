# Varaliaos

![Python](https://img.shields.io/badge/Python-3.9%2B-blue) ![FastAPI](https://img.shields.io/badge/FastAPI-Backend-green) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-pgvector-blue) ![License](https://img.shields.io/badge/License-MIT-yellow)

> Modular AI operating system using the M3 Memory Model, Sub-AI personas, and agentic memory.

Varialiaos (formerly NovaOS) is a FastAPI + PostgreSQL/pgvector backend that powers a personal AI with persistent, scored, and automatically consolidated vector memory. It supports multiple Sub-AI personas, real-time memory streaming via WebSocket, and nightly memory consolidation via scheduled jobs.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Database Setup](#database-setup)
- [Running the Server](#running-the-server)
- [API Usage](#api-usage)
- [WebSocket](#websocket)
- [Nightly Consolidation](#nightly-consolidation)
- [Project Structure](#project-structure)

---

## Features

- **M3 Memory Model** - Persistent, scored, and semantically searchable memory using pgvector
- **Sub-AI Personas** - Multiple specialized AI agents routed through a single backend
- **Agentic Memory** - Autonomous memory organization without constant user input
- **Real-time Streaming** - WebSocket support for live memory event delivery
- **Nightly Consolidation** - Scheduled memory summarization and optimization at 03:30 UTC
- **FastAPI Backend** - Full REST API with interactive Swagger docs

---

## Architecture

```
Client
  |
  |-- REST API (FastAPI) --> main.py
  |-- WebSocket --> ws://HOST/ws/{user_id}
       |
       |-- db.py         (PostgreSQL + pgvector storage)
       |-- subai.py      (Sub-AI persona routing)
       |-- scoring.py    (Memory relevance scoring)
       |-- prompt.py     (Prompt templates)
       |-- consolidate.py (Nightly memory consolidation)
```

---

## Prerequisites

- Python 3.9+
- PostgreSQL with the `pgvector` extension installed
- An OpenAI API key (or compatible LLM provider)
- *(Optional)* Supabase project for scheduling nightly consolidation via Edge Function CRON

---

## Installation

**1. Clone the repository**

```bash
git clone https://github.com/knhess1020/Varaliaos.git
cd Varaliaos
```

**2. Create and activate a virtual environment**

```bash
python -m venv .venv
source .venv/bin/activate
# Windows: .venv\Scripts\activate
```

**3. Install dependencies**

```bash
pip install -r requirements.txt
```

---

## Configuration

Set the following environment variables in your shell or a `.env` file:

```bash
export DATABASE_URL=postgresql://user:pass@host/db
export OPENAI_API_KEY=sk-...
```

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string (must have pgvector enabled) |
| `OPENAI_API_KEY` | Your LLM API key |

---

## Database Setup

**1. Enable pgvector in your PostgreSQL instance:**

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

**2. Apply the migration files** from the `migrations/` directory to create required tables and vector columns.

```bash
# Example using psql
psql $DATABASE_URL -f migrations/<migration_file>.sql
```

---

## Running the Server

```bash
uvicorn main:app --reload
```

- REST API: `http://localhost:8000`
- Interactive Swagger Docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

---

## API Usage

Once running, visit `http://localhost:8000/docs` to explore all available endpoints via the Swagger UI.

Key areas covered by the API:

- **Memory** - Create, retrieve, and search memory entries
- **Personas** - Manage Sub-AI persona configurations
- **Scoring** - Query memory relevance scores
- **Prompts** - Read and update prompt templates

---

## WebSocket

Connect to the live memory stream to receive new memory events in real time:

```
ws://HOST/ws/{user_id}
```

Replace `HOST` with your server address (e.g., `localhost:8000`) and `{user_id}` with a unique user or agent identifier.

**Example (Python):**

```python
import asyncio
import websockets

async def listen():
    uri = "ws://localhost:8000/ws/my_user"
    async with websockets.connect(uri) as ws:
        async for message in ws:
            print("New memory event:", message)

asyncio.run(listen())
```

---

## Nightly Consolidation

Memory consolidation summarizes and optimizes stored memories to prevent bloat.

**Run manually:**

```bash
python consolidate.py
```

**Schedule automatically via Supabase Edge Function CRON:**

1. Create a Supabase Edge Function that calls your consolidation endpoint or runs `consolidate.py`.
2. Schedule it for `03:30 UTC` in your Supabase CRON configuration.

---

## Project Structure

```
Varialiaos/
├── migrations/              # SQL migration files for DB schema
├── novaos_backend_v0_5/     # Previous version reference
├── main.py                  # FastAPI app entry point and route definitions
├── db.py                    # Database operations and vector storage
├── subai.py                 # Sub-AI persona management and routing
├── consolidate.py           # Nightly memory consolidation logic
├── scoring.py               # Memory relevance and importance scoring
├── prompt.py                # Prompt engineering and template management
├── requirements.txt         # Python dependencies
├── .gitignore
└── README.md
```

---

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

---

## License

MIT
