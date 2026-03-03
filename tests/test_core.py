import os
import uuid
import pytest
import pytest_asyncio

DATABASE_URL = os.getenv("DATABASE_URL")


@pytest.mark.asyncio
@pytest.mark.skipif(not DATABASE_URL, reason="DATABASE_URL not set")
async def test_insert_and_search_returns_results():
    """Insert a memory with a zero vector and assert the id appears in a subsequent search."""
    from db import insert_memory, search_memories

    zero_vec = [0.0] * 1536
    mem_id = str(uuid.uuid4())
    rec = {
        "id": mem_id,
        "user_id": "test_user",
        "type": "episodic",
        "content": "pytest test memory",
        "tags": [],
        "persona": None,
        "embedding": zero_vec,
        "thread_id": None,
        "turn": None,
    }
    returned_id = await insert_memory(rec)
    assert returned_id == mem_id

    results = await search_memories(
        user_id="test_user",
        embedding=zero_vec,
        k=10,
    )
    ids = [str(r["id"]) for r in results]
    assert mem_id in ids


@pytest.mark.asyncio
async def test_build_prompt_structure(monkeypatch):
    """Monkeypatch search_memories and get_embedding, then assert build_prompt returns correct shape."""
    import prompt as prompt_module

    async def fake_get_embedding(text):
        return [0.0] * 1536

    async def fake_search_memories(*args, **kwargs):
        return []

    monkeypatch.setattr(prompt_module, "get_embedding", fake_get_embedding)
    monkeypatch.setattr(prompt_module, "search_memories", fake_search_memories)

    # Minimal persona stub
    class FakePersona:
        pre = "You are a helpful assistant."

    import prompt
    monkeypatch.setitem(prompt.Persona.registry, "nova", FakePersona())

    result = await prompt.build_prompt(
        uid="test_user",
        user_input="Hello",
        persona_name="nova",
        thread_id=str(uuid.uuid4()),
    )

    assert "messages" in result
    assert isinstance(result["messages"], list)
    assert result["messages"][-1]["role"] == "user"
    assert "memories_used" in result
    assert isinstance(result["memories_used"], list)
