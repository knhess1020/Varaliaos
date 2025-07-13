# Varaliaos
Modular AI operating system using the M3 Memory Model, Sub-AI personas, and agentic memory.
# VaraliaOS

**Modular AI Operating System**  
Powered by the M3 Memory Model, Sub-AI Personas, Hybrid Vector Memory, and Agentic AI processes like RAG.

---

## 🧠 Core Features

- **M3 Memory System**: Moments → Modules → Meta-Arcs
- **Sub-AI Persona Layer**: Each persona (Nova, Thumper, etc.) has scoped memory and style
- **Hybrid Vector Search**: Cosine similarity + temporal decay scoring
- **Semantic Memory Chat**: Embedded prompt generator from real memories
- **FastAPI Backend**: `/memory`, `/chat`, `/search` endpoints
- **Postgres + pgvector**: Durable vector store with memory embedding
- **Thread Management**: Session continuity with `conversation_thread`
- **Audit Log**: All actions tracked (`audit_log`)
- **Real-Time WebSocket**: `/ws/{user}` + mobile AsyncStorage fallback

---

## 📦 Repo Contents
