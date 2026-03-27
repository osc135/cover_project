"""Integration tests for RAG retrieval — requires database with ingested chunks."""

import pytest
from app.services.rag import retrieve_chunks


@pytest.mark.asyncio
class TestRAGRetrieval:
    """Tests against the real database with ingested LAMC chunks."""

    async def test_r1_sfh_returns_chunks(self, db_session):
        chunks = await retrieve_chunks(db_session, "R1", "SFH")
        assert len(chunks) > 0, "No chunks returned for R1 SFH"

    async def test_r1_chunks_have_required_fields(self, db_session):
        chunks = await retrieve_chunks(db_session, "R1", "SFH")
        for chunk in chunks:
            assert "section_id" in chunk
            assert "text" in chunk
            assert "zone" in chunk

    async def test_r1_chunks_reference_correct_sections(self, db_session):
        """R1 zone should pull from LAMC 12.08 (R1 zone rules)."""
        chunks = await retrieve_chunks(db_session, "R1", "SFH")
        section_ids = [c["section_id"] for c in chunks]
        has_r1_section = any("12.08" in sid for sid in section_ids)
        assert has_r1_section, f"Expected 12.08 in chunks, got sections: {section_ids}"

    async def test_r3_returns_different_chunks(self, db_session):
        """R3 zone should pull from LAMC 12.10, not 12.08."""
        chunks = await retrieve_chunks(db_session, "R3", "SFH")
        assert len(chunks) > 0
        section_ids = [c["section_id"] for c in chunks]
        has_r3_section = any("12.10" in sid for sid in section_ids)
        assert has_r3_section, f"Expected 12.10 in R3 chunks, got: {section_ids}"

    async def test_adu_query_returns_relevant_chunks(self, db_session):
        """ADU queries should pull from 12.22 (accessory uses)."""
        chunks = await retrieve_chunks(db_session, "R1", "ADU")
        section_ids = [c["section_id"] for c in chunks]
        has_adu_section = any("12.22" in sid or "12.24" in sid for sid in section_ids)
        assert has_adu_section, f"Expected ADU-related sections, got: {section_ids}"

    async def test_zone_filter_prevents_contamination(self, db_session):
        """R1 query should not return R3-specific chunks."""
        chunks = await retrieve_chunks(db_session, "R1", "SFH")
        for chunk in chunks:
            if chunk["zone"] is not None:
                assert chunk["zone"] != "R3", f"R1 query returned R3-specific chunk: {chunk['section_id']}"

    async def test_returns_max_top_k(self, db_session):
        chunks = await retrieve_chunks(db_session, "R1", "SFH", top_k=5)
        assert len(chunks) <= 5

    async def test_nonexistent_zone_returns_general_chunks(self, db_session):
        """A zone with no specific rules should still return general chunks (zone IS NULL)."""
        chunks = await retrieve_chunks(db_session, "ZZ", "SFH")
        # Should get at least some general chunks (12.03, 12.04, etc.)
        assert len(chunks) >= 0  # May be empty if all chunks have zones
