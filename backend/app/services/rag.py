from __future__ import annotations

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from openai import AsyncOpenAI
from app.config import get_settings


async def get_embedding(query: str) -> list[float]:
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)
    resp = await client.embeddings.create(
        model="text-embedding-3-small",
        input=query,
    )
    return resp.data[0].embedding


async def retrieve_chunks(
    db: AsyncSession,
    zone: str,
    building_type: str,
    top_k: int = 10,
) -> list[dict]:
    """Retrieve relevant regulatory chunks filtered by zone with semantic search."""
    query_text = f"{zone} {building_type} setbacks height FAR lot coverage ADU"
    embedding = await get_embedding(query_text)

    embedding_str = "[" + ",".join(str(x) for x in embedding) + "]"

    # Split query: zone-specific chunks + general chunks
    # Guarantees zone-specific rules are always included even when
    # outnumbered by general provisions
    zone_k = top_k // 2
    general_k = top_k - zone_k

    zone_sql = text("""
        SELECT section_id, zone, topic, text, source_url,
               embedding <=> cast(:embedding as vector) AS distance
        FROM regulatory_chunks
        WHERE zone = :zone
        ORDER BY embedding <=> cast(:embedding as vector)
        LIMIT :top_k
    """)

    general_sql = text("""
        SELECT section_id, zone, topic, text, source_url,
               embedding <=> cast(:embedding as vector) AS distance
        FROM regulatory_chunks
        WHERE zone IS NULL
        ORDER BY embedding <=> cast(:embedding as vector)
        LIMIT :top_k
    """)

    zone_result = await db.execute(
        zone_sql, {"embedding": embedding_str, "zone": zone, "top_k": zone_k},
    )
    zone_rows = zone_result.fetchall()

    general_result = await db.execute(
        general_sql, {"embedding": embedding_str, "top_k": general_k},
    )
    general_rows = general_result.fetchall()

    # Combine, dedup by text, zone-specific first
    seen = set()
    chunks = []
    for row in list(zone_rows) + list(general_rows):
        if row.text not in seen:
            seen.add(row.text)
            chunks.append({
                "section_id": row.section_id,
                "zone": row.zone,
                "topic": row.topic,
                "text": row.text,
                "source_url": row.source_url,
            })

    return chunks
