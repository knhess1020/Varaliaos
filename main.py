import os, uuid, math, time
from datetime import datetime
from typing import List, Optional

import httpx
from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel, Field
from collections import defaultdict

from db import insert_memory, search_memories, get_or_create_thread, increment_turn, log_audit
from subai import Persona
from prompt import build_prompt
from llm import get_embedding, chat_completion

app = FastAPI(title="Varaliaos API", version="0.5")

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
    type: Optional[str] = None
    persona: Optional[str] = None
    top_k: int = 5

class ChatIn(BaseModel):
    user_id: str
    message: str
    persona: Optional[str] = "nova"
    thread_id: Optional[str] = None

class ChatOut(BaseModel):
    reply: str
    thread_id: str
    turn: int
    memories_used: List[str]

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active: defaultdict = defaultdict(list)

    async def connect(self, user_id: str, ws: WebSocket):
        await ws.accept()
        self.active[user_id].append(ws)

    def disconnect(self, user_id: str, ws: WebSocket):
        self.active[user_id].remove(ws)

    async def broadcast(self, user_id: str, message: dict):
        for ws in list(self.active[user_id]):
            try:
                await ws.send_json(message)
            except Exception:
                self.active[user_id].remove(ws)

manager = ConnectionManager()

@app.post("/memories", response_model=MemoryOut)
async def store_memory(mem: MemoryIn):
    embedding = await get_embedding(mem.content)
    rec = {
        "id": str(uuid.uuid4()),
        "user_id": mem.user_id,
        "type": mem.type,
        "content": mem.content,
        "tags": mem.tags,
        "persona": mem.persona,
        "embedding": embedding,
        "thread_id": None,
        "turn": None,
    }
    mem_id = await insert_memory(rec)
    await log_audit(mem.user_id, "insert", mem_id)
    return MemoryOut(id=mem_id)

@app.post("/search")
async def search(req: SearchIn):
    embedding = await get_embedding(req.query)
    results = await search_memories(
        user_id=req.user_id,
        embedding=embedding,
        k=req.top_k,
        m_type=req.type,
        persona=req.persona,
    )
    return {"results": results}

@app.post("/chat", response_model=ChatOut)
async def chat(req: ChatIn):
    persona = Persona.get(req.persona or "nova")
    thread_id = req.thread_id or str(uuid.uuid4())
    turn = await increment_turn(req.user_id, thread_id)

    prompt_data = await build_prompt(
        user_id=req.user_id,
        message=req.message,
        persona=persona,
        thread_id=thread_id,
        turn=turn,
    )

    reply_text = await chat_completion(prompt_data["messages"])

    # Store user message as memory
    embedding = await get_embedding(req.message)
    rec = {
        "id": str(uuid.uuid4()),
        "user_id": req.user_id,
        "type": "episodic",
        "content": req.message,
        "tags": [],
        "persona": req.persona,
        "embedding": embedding,
        "thread_id": thread_id,
        "turn": turn,
    }
    mem_id = await insert_memory(rec)
    await log_audit(req.user_id, "chat", mem_id)
    await manager.broadcast(req.user_id, {"event": "memory_stored", "id": mem_id})

    return ChatOut(
        reply=reply_text,
        thread_id=thread_id,
        turn=turn,
        memories_used=prompt_data.get("memories_used", []),
    )

@app.websocket("/ws/{user_id}")
async def websocket_endpoint(websocket: WebSocket, user_id: str):
    await manager.connect(user_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
