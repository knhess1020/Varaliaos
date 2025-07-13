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
    return await (await pool()).fetchval(q, *rec.values())

async def search_memories(user_id: str, vec: List[float], k: int,
                          m_type: str | None, persona: str | None,
                          thread_id: str | None = None):
    filt, args = ["user_id=$2"], [vec, user_id]
    if m_type:   filt.append(f"type=$${len(args)+2}");    args.append(m_type)
    if persona:  filt.append(f"persona=$${len(args)+2}"); args.append(persona)
    if thread_id:filt.append(f"thread_id=$${len(args)+2}");args.append(thread_id)
    q = f"""select id,content,type,tags,persona,ts,
                   1-(embedding<=>$1)::float as similarity
            from memory where {' and '.join(filt)}
            order by embedding<=>$1 limit {k}"""
    return await (await pool()).fetch(q, *args)

async def get_or_create_thread(uid:str, persona:str)->str:
    q = "select id from conversation_thread where user_id=$1 and persona=$2 order by started_at desc limit 1"
    p = await pool()
    tid = await p.fetchval(q, uid, persona)
    if tid:
        return tid
    return await p.fetchval("insert into conversation_thread(user_id,persona) values($1,$2) returning id",
                            uid, persona)

async def increment_turn(tid: str)->int:
    q = "update conversation_thread set last_turn=last_turn+1 where id=$1 returning last_turn"
    return await (await pool()).fetchval(q, tid)

async def log_audit(uid:str, action:str, mem_id:str):
    await (await pool()).execute("insert into audit_log(user_id,action,mem_id) values($1,$2,$3)",
                                 uid, action, mem_id)
