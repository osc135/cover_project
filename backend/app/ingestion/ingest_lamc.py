"""
Offline script: Parse LAMC PDFs, chunk by subsection, embed, and store in PGVector.

Usage:
    python -m app.ingestion.ingest_lamc --pdf-dir ./data/lamc_pdfs
"""

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
    "12.22": None,   # Accessory uses / ADU — applies to all zones
}

# Regex to split on subsection headers like "12.08 A.", "12.08 C.1.", etc.
SUBSECTION_RE = re.compile(r"((?:SEC\.\s*)?12\.\d{2}(?:\.\d)?\s+[A-Z]\.(?:\d+\.)?)")


def extract_text_from_pdf(pdf_path: Path) -> str:
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text += page_text + "\n"
    return text


def chunk_by_subsection(text: str, section_id: str, overlap_chars: int = 200) -> list[dict]:
    """Split text by subsection headers with overlap."""
    parts = SUBSECTION_RE.split(text)
    chunks = []

    # Parts alternate: [preamble, header1, body1, header2, body2, ...]
    # Handle preamble
    if parts[0].strip():
        chunks.append({
            "section_id": section_id,
            "topic": f"{section_id} (preamble)",
            "text": parts[0].strip(),
        })

    for i in range(1, len(parts) - 1, 2):
        header = parts[i].strip()
        body = parts[i + 1].strip() if i + 1 < len(parts) else ""
        chunk_text = f"{header} {body}"

        # Add overlap from previous chunk
        if chunks and overlap_chars > 0:
            prev_text = chunks[-1]["text"]
            overlap = prev_text[-overlap_chars:] if len(prev_text) > overlap_chars else prev_text
            chunk_text = f"...{overlap}\n\n{chunk_text}"

        topic_label = header.rstrip(".")
        chunks.append({
            "section_id": section_id,
            "topic": topic_label,
            "text": chunk_text,
        })

    # If no subsection headers found, treat whole text as one chunk
    if not chunks:
        chunks.append({
            "section_id": section_id,
            "topic": section_id,
            "text": text.strip(),
        })

    return chunks


def embed_chunks(chunks: list[dict], api_key: str) -> list[dict]:
    client = OpenAI(api_key=api_key)
    texts = [c["text"] for c in chunks]

    # Batch embed (max 2048 per call)
    all_embeddings = []
    for i in range(0, len(texts), 100):
        batch = texts[i : i + 100]
        resp = client.embeddings.create(model="text-embedding-3-small", input=batch)
        all_embeddings.extend([d.embedding for d in resp.data])

    for chunk, emb in zip(chunks, all_embeddings):
        chunk["embedding"] = emb

    return chunks


def store_chunks(chunks: list[dict], zone: str | None, db_url: str, source_url: str = ""):
    conn = psycopg2.connect(db_url.replace("+asyncpg", "").replace("postgresql+asyncpg", "postgresql"))
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
    parser = argparse.ArgumentParser(description="Ingest LAMC PDFs into PGVector")
    parser.add_argument("--pdf-dir", type=str, required=True, help="Directory containing LAMC PDF files")
    parser.add_argument("--db-url", type=str, default="postgresql://cover:cover@localhost:5432/cover")
    parser.add_argument("--openai-key", type=str, required=True)
    args = parser.parse_args()

    pdf_dir = Path(args.pdf_dir)

    for pdf_file in sorted(pdf_dir.glob("*.pdf")):
        # Try to match filename to a known section (e.g., "12.08.pdf" or "section_12.08.pdf")
        name = pdf_file.stem.replace("section_", "").replace("Section_", "")
        section_id = None
        for sid in SECTION_ZONE_MAP:
            if sid in name:
                section_id = sid
                break

        if not section_id:
            print(f"Skipping {pdf_file.name} — no matching LAMC section")
            continue

        zone = SECTION_ZONE_MAP[section_id]
        print(f"Processing {pdf_file.name} → section {section_id} (zone: {zone or 'all'})")

        text = extract_text_from_pdf(pdf_file)
        chunks = chunk_by_subsection(text, section_id)
        print(f"  {len(chunks)} chunks extracted")

        chunks = embed_chunks(chunks, args.openai_key)
        print(f"  Embeddings generated")

        source_url = f"https://codelibrary.amlegal.com/codes/los_angeles/latest/lamc/0-0-0-{section_id.replace('.', '-')}"
        store_chunks(chunks, zone, args.db_url, source_url)
        print(f"  Stored in DB")

    print("Done.")


if __name__ == "__main__":
    main()
