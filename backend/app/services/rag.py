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

    sql = text("""
        SELECT section_id, zone, topic, text, source_url,
               embedding <=> :embedding::vector AS distance
        FROM regulatory_chunks
        WHERE zone = :zone OR zone IS NULL
        ORDER BY embedding <=> :embedding::vector
        LIMIT :top_k
    """)

    result = await db.execute(
        sql,
        {"embedding": str(embedding), "zone": zone, "top_k": top_k},
    )
    rows = result.fetchall()

    return [
        {
            "section_id": row.section_id,
            "zone": row.zone,
            "topic": row.topic,
            "text": row.text,
            "source_url": row.source_url,
        }
        for row in rows
    ]
