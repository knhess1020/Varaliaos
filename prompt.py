import time
from typing import List
from scoring import hybrid_score
from db import search_memories
from subai import Persona
from main import get_embedding

async def build_prompt(uid: str, user_input: str, persona_name: str,
                       thread_id: str, top_k: int = 8):
    p = Persona.registry[persona_name]
    qvec = await get_embedding(user_input)
    rows = await search_memories(uid, qvec, top_k*3, None, None, thread_id)
    now = time.time()
    ranked = sorted(rows, key=lambda r:
                    hybrid_score(r['similarity'], r['ts'].timestamp(), now), reverse=True)
    mems = ranked[:top_k]
    snippets = []
    for m in mems:
        txt = m['content'][:197]+'…' if len(m['content'])>200 else m['content']
        tag = m['type'].lower()
        snippets.append(f"- ({tag}) {txt}")
    ctx = "\n".join(snippets) if snippets else "None"
    system_ctx = f"Date: {time.strftime('%Y-%m-%d')}\nMemories:\n{ctx}"
    messages = [
        {"role":"system", "content": p.pre},
        {"role":"system", "content": system_ctx},
        {"role":"user",   "content": user_input}
    ]
    return {"messages": messages,
            "memories_used":[m["id"] for m in mems]}
