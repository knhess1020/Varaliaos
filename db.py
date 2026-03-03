import os, asyncpg
from typing import Any, Dict, List

DB_URL = os.getenv("DATABASE_URL")
_pool: asyncpg.Pool | None = None

async def pool():
    global _pool
    if not _pool:
        _pool = await asyncpg.create_pool(DB_URL, min_size=1, max_size=5)
    return _pool

async def insert_memory(rec: Dict[str, Any]) -> str:
    q = """insert into memory(id,user_id,type,content,tags,persona,embedding,thread_id,turn)
           values($1,$2,$3,$4,$5,$6,$7,$8,$9) returning id"""
    return await (await pool()).fetchval(
        q,
        rec["id"],
        rec["user_id"],
        rec["type"],
        rec["content"],
        rec.get("tags", []),
        rec.get("persona"),
        rec["embedding"],
        rec.get("thread_id"),
        rec.get("turn"),
    )

async def search_memories(user_id: str, embedding: List[float], k: int,
                          m_type: str | None = None, persona: str | None = None,
                          thread_id: str | None = None):
    args = [user_id, embedding]
    filt = ["user_id=$1"]
    if m_type:
        args.append(m_type)
        filt.append(f"type=${len(args)}")
    if persona:
        args.append(persona)
        filt.append(f"persona=${len(args)}")
    if thread_id:
        args.append(thread_id)
        filt.append(f"thread_id=${len(args)}")
    q = f"""select id,content,type,tags,persona,ts,
                1-(embedding<=>$2)::float as similarity
           from memory where {' and '.join(filt)}
           order by embedding<=>$2 limit {k}"""
    return await (await pool()).fetch(q, *args)

async def get_or_create_thread(uid: str, persona: str) -> str:
    q = "select id from conversation_thread where user_id=$1 and persona=$2 order by started_at desc limit 1"
    p = await pool()
    row = await p.fetchrow(q, uid, persona)
    if row:
        return str(row["id"])
    import uuid
    new_id = str(uuid.uuid4())
    await p.execute(
        "insert into conversation_thread(id,user_id,persona,started_at,last_turn) values($1,$2,$3,now(),0)",
        new_id, uid, persona
    )
    return new_id

async def increment_turn(uid: str, thread_id: str) -> int:
    p = await pool()
    await p.execute(
        "update conversation_thread set last_turn=last_turn+1 where id=$1",
        thread_id
    )
    row = await p.fetchrow("select last_turn from conversation_thread where id=$1", thread_id)
    return row["last_turn"] if row else 1

async def log_audit(user_id: str, action: str, mem_id: str):
    q = "insert into audit_log(user_id,action,mem_id,ts) values($1,$2,$3,now())"
    await (await pool()).execute(q, user_id, action, mem_id)
