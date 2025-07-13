import os, uuid, math, time
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from collections import defaultdict

from db import insert_memory, search_memories, get_or_create_thread, increment_turn, log_audit
from subai import Persona
from prompt import build_prompt, get_embedding

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBED_MODEL = "text-embedding-3-small"
EMBED_ENDPOINT = "https://api.openai.com/v1/embeddings"

app = FastAPI(title="NovaOS API", version="0.4")

class MemoryIn(BaseModel):
    user_id: str
    type: str
    content: str
    tags: Optional[List[str]] = Field(default_factory=list)
    persona: Optional[str] = None

class MemoryOut(BaseModel):
    id: str
    status: str = "stored"

class SearchIn(BaseModel):
    user_id: str
    query: str
    top_k: int = Field(5, gt=0, le=50)
    type: Optional[str] = None
    persona: Optional[str] = None

class SearchHit(BaseModel):
    id: str
    content: str
    similarity: float
    confidence: float
    type: str
    tags: List[str]
    persona: Optional[str]
    timestamp: str

class ChatIn(BaseModel):
    user_id: str
    message: str
    persona: str = "Nova"

class ChatOut(BaseModel):
    reply: str
    memories: List[str]

async def get_embedding(text: str) -> List[float]:
    payload = {"input": text, "model": EMBED_MODEL}
    headers = {"Authorization": f"Bearer {OPENAI_API_KEY}"}
    async with httpx.AsyncClient(timeout=15) as c:
        r = await c.post(EMBED_ENDPOINT, json=payload, headers=headers)
        if r.status_code != 200:
            raise HTTPException(502, f"OpenAI error: {r.text}")
        return r.json()["data"][0]["embedding"]

# ----------------- API Routes ---------------- #
@app.post("/memory", response_model=MemoryOut)
async def add_memory(m: MemoryIn):
    emb = await get_embedding(m.content)
    mem_id = await insert_memory({
        "id": str(uuid.uuid4()), "user_id": m.user_id, "type": m.type,
        "content": m.content, "tags": m.tags, "persona": m.persona,
        "embedding": emb
    })
    await log_audit(m.user_id, "write", mem_id)
    await broadcast_memory(m.user_id, {"id": mem_id, "type": m.type, "content": m.content})
    return MemoryOut(id=mem_id)

@app.post("/search", response_model=List[SearchHit])
async def search(q: SearchIn):
    vec = await get_embedding(q.query)
    rows = await search_memories(q.user_id, vec, q.top_k, q.type, q.persona)
    now = time.time()
    from scoring import hybrid_score
    hits = []
    for r in rows:
        conf = hybrid_score(r["similarity"], r["ts"].timestamp(), now)
        hits.append(SearchHit(
            id=r["id"], content=r["content"], similarity=round(r["similarity"],4),
            confidence=round(conf,3), type=r["type"], tags=r["tags"],
            persona=r["persona"], timestamp=r["ts"].isoformat()
        ))
        await log_audit(q.user_id, "read", r["id"])
    return hits

@app.post("/chat", response_model=ChatOut)
async def chat(c: ChatIn):
    thread_id = await get_or_create_thread(c.user_id, c.persona)
    payload   = await build_prompt(c.user_id, c.message, c.persona, thread_id)
    # call OpenAI chat
    async with httpx.AsyncClient(timeout=30) as cli:
        r = await cli.post("https://api.openai.com/v1/chat/completions",
                           headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
                           json={"model": os.getenv("CHAT_MODEL","gpt-4o-mini"),
                                 "messages": payload["messages"]})
        r.raise_for_status()
    raw = r.json()["choices"][0]["message"]["content"]
    styled = Persona.registry[c.persona].wrap_output(raw)
    # store user message as memory
    turn = await increment_turn(thread_id)
    mem_id = await insert_memory({
        "id": str(uuid.uuid4()), "user_id": c.user_id, "type":"Moment",
        "content": c.message, "tags":[], "persona": c.persona,
        "thread_id": thread_id, "turn": turn,
        "embedding": await get_embedding(c.message)
    })
    await log_audit(c.user_id, "write", mem_id)
    return ChatOut(reply=styled, memories=payload["memories_used"])

# ------------- WebSocket ---------------
active_ws = defaultdict(set)

@app.websocket("/ws/{user_id}")
async def ws_mem(user_id: str, ws: WebSocket):
    await ws.accept(); active_ws[user_id].add(ws)
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        active_ws[user_id].discard(ws)

async def broadcast_memory(uid: str, mem_json: dict):
    for ws in list(active_ws.get(uid, [])):
        try:
            await ws.send_json(mem_json)
        except:
            active_ws[uid].discard(ws)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
