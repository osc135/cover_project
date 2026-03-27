"""Unit tests for the confidence scoring logic."""

import pytest
from app.routers.assessment import compute_confidence


class TestConfidenceScoring:
    """Tests for compute_confidence — deterministic, no external deps."""

    def _make_constraints(self, levels: list[str]) -> list[dict]:
        return [{"confidence": level} for level in levels]

    def test_perfect_data_all_high_constraints(self):
        """Complete data + all HIGH constraints = grade A."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "R1-1"},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["HIGH", "HIGH", "HIGH"]),
        )
        assert result.grade == "A"
        assert result.overall >= 0.90
        assert result.data_quality == 1.0
        assert result.rule_confidence == 1.0

    def test_missing_lot_size_penalty(self):
        """Missing lot size should reduce data quality by 25%."""
        result = compute_confidence(
            parcel_data={},  # no lot_size_sqft
            zoning_data={"base_zone": "R1-1"},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["HIGH", "HIGH", "HIGH"]),
        )
        assert result.data_quality == 0.75

    def test_unindexed_zone_penalty(self):
        """Zone not in INDEXED_ZONES should reduce data quality by 30%."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "C2-1"},  # commercial, not indexed
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["HIGH", "HIGH"]),
        )
        assert result.data_quality == 0.70

    def test_no_buildings_penalty(self):
        """No building data = -10% data quality."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "R1-1"},
            buildings=[],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["HIGH", "HIGH"]),
        )
        assert result.data_quality == 0.90

    def test_overlay_zones_penalty(self):
        """Each overlay zone costs 5% data quality."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "R1-1", "hillside": True, "hpoz": True},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["HIGH"]),
        )
        assert result.data_quality == 0.90  # -5% per overlay x2

    def test_few_rag_chunks_penalty(self):
        """Fewer than 3 RAG chunks = -15% data quality."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "R1-1"},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}],  # only 2
            constraints=self._make_constraints(["HIGH"]),
        )
        assert result.data_quality == 0.85

    def test_all_low_constraints_grade_d(self):
        """All LOW confidence constraints should produce a low grade."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "R1-1"},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["LOW", "LOW", "LOW"]),
        )
        assert result.grade == "D"
        assert result.rule_confidence < 0.5

    def test_mixed_constraints(self):
        """Mix of HIGH/MEDIUM/LOW should produce intermediate score."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "R1-1"},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["HIGH", "MEDIUM", "LOW"]),
        )
        assert 0.4 < result.rule_confidence < 0.8
        assert result.grade in ("B", "C")

    def test_no_constraints_low_confidence(self):
        """No constraints at all = very low confidence."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "R1-1"},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=[],
        )
        assert result.grade == "D"
        assert result.rule_confidence == 0.3

    def test_zone_prefix_stripping(self):
        """Prefixed zones like [Q]R3-1 should still be recognized as indexed."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "[Q]R3-1"},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["HIGH"]),
        )
        # R3 is indexed, so no zone penalty
        assert result.data_quality == 1.0

    def test_complex_zone_prefix(self):
        """Complex prefixes like (T)(Q) should be stripped."""
        result = compute_confidence(
            parcel_data={"lot_size_sqft": 6000},
            zoning_data={"base_zone": "(T)(Q)R1-1"},
            buildings=[{"building_type": "SFR"}],
            chunks=[{}, {}, {}, {}, {}],
            constraints=self._make_constraints(["HIGH"]),
        )
        assert result.data_quality == 1.0

    def test_cumulative_penalties(self):
        """Multiple data quality issues should stack."""
        result = compute_confidence(
            parcel_data={},  # no lot size (-25%)
            zoning_data={"base_zone": "C2-1", "hillside": True},  # unindexed zone (-30%) + overlay (-5%)
            buildings=[],  # no buildings (-10%)
            chunks=[{}],  # few chunks (-15%)
            constraints=self._make_constraints(["LOW"]),
        )
        # 1.0 - 0.25 - 0.30 - 0.10 - 0.05 - 0.15 = 0.15
        assert result.data_quality == 0.15
        assert result.grade == "D"

    def test_data_quality_floors_at_zero(self):
        """Data quality should never go below 0."""
        result = compute_confidence(
            parcel_data={},
            zoning_data={"base_zone": "C2-1", "hillside": True, "coastal_zone": True, "hpoz": True, "specific_plan": "SP"},
            buildings=[],
            chunks=[],
            constraints=self._make_constraints(["LOW"]),
        )
        assert result.data_quality >= 0.0
        assert result.overall >= 0.0

    def test_grade_boundaries(self):
        """Verify grade boundary logic."""
        # A: >= 0.90
        r = compute_confidence(
            {"lot_size_sqft": 6000}, {"base_zone": "R1-1"}, [{"t": 1}],
            [{}, {}, {}, {}, {}], self._make_constraints(["HIGH", "HIGH", "HIGH", "HIGH"])
        )
        assert r.grade == "A"

        # D: < 0.60 — use LOW constraints
        r = compute_confidence(
            {"lot_size_sqft": 6000}, {"base_zone": "R1-1"}, [{"t": 1}],
            [{}, {}, {}, {}, {}], self._make_constraints(["LOW"])
        )
        assert r.grade == "D"
