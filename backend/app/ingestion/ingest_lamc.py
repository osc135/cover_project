"""
Offline script: Parse LAMC PDF, chunk by section/subsection, embed, and store in PGVector.

Usage:
    cd backend
    source .venv/bin/activate
    python -m app.ingestion.ingest_lamc --pdf ./data/lamc_pdfs/lamc_all.pdf
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

import pdfplumber
from openai import OpenAI
import psycopg2

# LAMC sections we care about and their zone mappings
SECTION_ZONE_MAP = {
    "12.03": None,   # Definitions — applies to all zones
    "12.04": None,   # Zone hierarchy — applies to all zones
    "12.08": "R1",   # R1 One-Family Zone
    "12.09": "R2",   # R2 Two-Family Zone
    "12.09.1": "RD", # RD Restricted Density
    "12.21": None,   # Height districts — applies to all zones
    "12.21.1": None, # Height of buildings
    "12.22": None,   # Exceptions / accessory uses / ADU
}

# Regex to detect section headers
SECTION_HEADER_RE = re.compile(r"SEC\.\s*(12\.\d{2}(?:\.\d+)?)\.")


def extract_text_from_pdf(pdf_path: Path) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def split_by_section(full_text: str) -> dict[str, str]:
    """Split the full text into sections based on SEC. headers."""
    sections = {}
    positions = []

    for match in SECTION_HEADER_RE.finditer(full_text):
        sec_id = match.group(1)
        if sec_id in SECTION_ZONE_MAP:
            positions.append((match.start(), sec_id))

    for i, (start, sec_id) in enumerate(positions):
        end = positions[i + 1][0] if i + 1 < len(positions) else len(full_text)
        sections[sec_id] = full_text[start:end].strip()

    return sections


def chunk_text(text: str, section_id: str, max_chars: int = 1500, overlap: int = 200) -> list[dict]:
    """Split section text into overlapping chunks by newline boundaries."""
    chunks = []
    lines = text.split("\n")
    current_chunk = ""
    current_topic = section_id

    for line in lines:
        # Check if this line has a subsection header
        sub_match = re.match(r"(?:SEC\.\s*)?(\d+\.\d+(?:\.\d+)?\s+[A-Z]\.(?:\d+\.)?)", line)
        if sub_match:
            current_topic = sub_match.group(1).strip().rstrip(".")

        if len(current_chunk) + len(line) > max_chars and current_chunk:
            chunks.append({
                "section_id": section_id,
                "topic": current_topic,
                "text": current_chunk.strip(),
            })
            current_chunk = current_chunk[-overlap:] + "\n" + line
        else:
            current_chunk += "\n" + line if current_chunk else line

    if current_chunk.strip():
        chunks.append({
            "section_id": section_id,
            "topic": current_topic,
            "text": current_chunk.strip(),
        })

    return chunks


def embed_chunks(chunks: list[dict], api_key: str) -> list[dict]:
    client = OpenAI(api_key=api_key)
    texts = [c["text"] for c in chunks]

    all_embeddings = []
    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        resp = client.embeddings.create(model="text-embedding-3-small", input=batch)
        all_embeddings.extend([d.embedding for d in resp.data])
        print(f"  Embedded batch {i // 100 + 1} ({len(batch)} chunks)")

    for chunk, emb in zip(chunks, all_embeddings):
        chunk["embedding"] = emb

    return chunks


def store_chunks(chunks: list[dict], zone: str | None, db_url: str, source_url: str = ""):
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()

    for chunk in chunks:
        cur.execute(
            """
            INSERT INTO regulatory_chunks (section_id, zone, topic, text, source_url, embedding)
            VALUES (%s, %s, %s, %s, %s, %s::vector)
            """,
            (
                chunk["section_id"],
                zone,
                chunk["topic"],
                chunk["text"],
                source_url,
                str(chunk["embedding"]),
            ),
        )

    conn.commit()
    cur.close()
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Ingest LAMC PDF into PGVector")
    parser.add_argument("--pdf", type=str, required=True, help="Path to the LAMC PDF")
    parser.add_argument("--db-url", type=str, default="postgresql://cover:cover@localhost:5432/cover")
    parser.add_argument("--openai-key", type=str, default=None)
    args = parser.parse_args()

    # Try to load key from .env if not provided
    if not args.openai_key:
        from dotenv import dotenv_values
        env = dotenv_values(Path(__file__).resolve().parent.parent.parent.parent / ".env")
        args.openai_key = env.get("OPENAI_API_KEY", "")

    if not args.openai_key:
        print("ERROR: No OpenAI key. Pass --openai-key or set OPENAI_API_KEY in .env")
        return

    pdf_path = Path(args.pdf)
    print(f"Reading {pdf_path.name}...")
    full_text = extract_text_from_pdf(pdf_path)
    print(f"  {len(full_text)} characters extracted")

    print("Splitting into sections...")
    sections = split_by_section(full_text)
    print(f"  Found sections: {list(sections.keys())}")

    total_chunks = 0
    for sec_id, sec_text in sections.items():
        zone = SECTION_ZONE_MAP.get(sec_id)
        print(f"\nProcessing {sec_id} (zone: {zone or 'all'})...")

        chunks = chunk_text(sec_text, sec_id)
        print(f"  {len(chunks)} chunks")

        chunks = embed_chunks(chunks, args.openai_key)

        source_url = f"https://codelibrary.amlegal.com/codes/los_angeles/latest/lapz"
        store_chunks(chunks, zone, args.db_url, source_url)
        print(f"  Stored in DB")
        total_chunks += len(chunks)

    print(f"\nDone. {total_chunks} total chunks ingested.")


if __name__ == "__main__":
    main()
