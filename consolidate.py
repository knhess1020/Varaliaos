import os, asyncio, asyncpg, math, openai, time
from scoring import cosine
from main import get_embedding

openai.api_key = os.getenv("OPENAI_API_KEY")
DB_URL = os.getenv("DATABASE_URL")

async def consolidate():
    pool = await asyncpg.create_pool(DB_URL)
    rows = await pool.fetch(
        """select id,user_id,content,embedding from memory
           where type='Moment' and ts > now()-interval '1 day'""")
    used = set()
    for i,r in enumerate(rows):
        if r['id'] in used: continue
        group=[r]
        emb_i = r['embedding']
        for s in rows[i+1:]:
            if s['id'] in used: continue
            if cosine(emb_i, s['embedding']) > 0.93:
                group.append(s); used.add(s['id'])
        if len(group) > 1:
            text = "\n".join(g['content'] for g in group)
            summ = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=[{"role":"system","content":"Summarize into one sentence."},
                          {"role":"user","content":text}]
            ).choices[0].message.content
            emb = await get_embedding(summ)
            mod_id = await pool.fetchval(
                """insert into memory(id,user_id,type,content,embedding)
                   values(gen_random_uuid(),$1,'Module',$2,$3) returning id""",
                r['user_id'], summ, emb)
            for g in group:
                await pool.execute("update memory set merged_into=$1 where id=$2", mod_id, g['id'])
    await pool.close()

if __name__ == "__main__":
    asyncio.run(consolidate())
