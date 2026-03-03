import os, asyncio, math, time
from scoring import cosine
from db import pool, insert_memory
from llm import get_embedding, chat_completion

async def consolidate():
    p = await pool()
    rows = await p.fetch(
        """select id,user_id,content,embedding from memory
           where type='Moment' and ts > now()-interval '1 day'"""
    )
    used = set()
    for i, r in enumerate(rows):
        if r['id'] in used:
            continue
        group = [r]
        emb_i = r['embedding']
        for s in rows[i+1:]:
            if s['id'] in used:
                continue
            if cosine(emb_i, s['embedding']) > 0.93:
                group.append(s)
                used.add(s['id'])
        if len(group) > 1:
            text = "\n".join(g['content'] for g in group)
            messages = [
                {"role": "system", "content": "Summarize into one sentence."},
                {"role": "user", "content": text}
            ]
            summ = await chat_completion(messages)
            emb = await get_embedding(summ)
            rec = {
                "id": str(__import__('uuid').uuid4()),
                "user_id": group[0]['user_id'],
                "type": "Module",
                "content": summ,
                "tags": [],
                "persona": None,
                "embedding": emb,
                "thread_id": None,
                "turn": None,
            }
            await insert_memory(rec)
            for g in group:
                await p.execute(
                    "update memory set merged_into=$1 where id=$2",
                    rec["id"], g['id']
                )
            used.update(g['id'] for g in group)

if __name__ == "__main__":
    asyncio.run(consolidate())
