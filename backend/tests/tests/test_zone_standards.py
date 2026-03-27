"""Unit tests for zone standards lookup data and resolution logic.

These tests verify the correctness of zone standard values and the zone-string
parsing logic defined in the frontend (zoneStandards.ts). The lookup is
reimplemented here in pure Python so the data can be validated independently.
"""

import re
from typing import Optional

import pytest


# ---------------------------------------------------------------------------
# Minimal Python port of the zone standards data + lookup function
# ---------------------------------------------------------------------------

ZONE_STANDARDS: dict[str, dict] = {
    "RE9":   {"zone": "RE9",   "zoneClass": "RE", "maxHeight": "36 ft", "maxStories": 2, "rfa": 0.40, "frontSetback": "25 ft", "sideSetback": "5 ft",  "rearSetback": "25 ft"},
    "RE11":  {"zone": "RE11",  "zoneClass": "RE", "maxHeight": "36 ft", "maxStories": 2, "rfa": 0.35, "frontSetback": "25 ft", "sideSetback": "10 ft", "rearSetback": "25 ft"},
    "RE15":  {"zone": "RE15",  "zoneClass": "RE", "maxHeight": "36 ft", "maxStories": 2, "rfa": 0.35, "frontSetback": "25 ft", "sideSetback": "10 ft", "rearSetback": "25 ft"},
    "RE20":  {"zone": "RE20",  "zoneClass": "RE", "maxHeight": "36 ft", "maxStories": 2, "rfa": 0.30, "frontSetback": "25 ft", "sideSetback": "15 ft", "rearSetback": "25 ft"},
    "RE40":  {"zone": "RE40",  "zoneClass": "RE", "maxHeight": "36 ft", "maxStories": 2, "rfa": 0.25, "frontSetback": "25 ft", "sideSetback": "25 ft", "rearSetback": "25 ft"},
    "RS":    {"zone": "RS",    "zoneClass": "RS", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "20 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "R1":    {"zone": "R1",    "zoneClass": "R1", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "20% \u2264 20 ft", "sideSetback": "5 ft", "rearSetback": "15 ft"},
    "RU":    {"zone": "RU",    "zoneClass": "RU", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "15 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "R2":    {"zone": "R2",    "zoneClass": "R2", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "20% \u2264 20 ft", "sideSetback": "5 ft", "rearSetback": "15 ft"},
    "RD1_5": {"zone": "RD1.5", "zoneClass": "RD", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "15 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "RD2":   {"zone": "RD2",   "zoneClass": "RD", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "15 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "RD3":   {"zone": "RD3",   "zoneClass": "RD", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "15 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "RD4":   {"zone": "RD4",   "zoneClass": "RD", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "15 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "RD5":   {"zone": "RD5",   "zoneClass": "RD", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "20 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "RD6":   {"zone": "RD6",   "zoneClass": "RD", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.40, "frontSetback": "20 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "RW1":   {"zone": "RW1",   "zoneClass": "RW", "maxHeight": "33 ft", "maxStories": 2, "rfa": 0.45, "frontSetback": "15 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "R3":    {"zone": "R3",    "zoneClass": "R3", "maxHeight": "45 ft", "maxStories": 3, "rfa": None, "frontSetback": "10 ft", "sideSetback": "5 ft",  "rearSetback": "15 ft"},
    "R4":    {"zone": "R4",    "zoneClass": "R4", "maxHeight": "75 ft", "maxStories": None, "rfa": None, "frontSetback": "5 ft", "sideSetback": "5 ft", "rearSetback": "15 ft"},
    "R5":    {"zone": "R5",    "zoneClass": "R5", "maxHeight": "No limit", "maxStories": None, "rfa": None, "frontSetback": "5 ft", "sideSetback": "5 ft", "rearSetback": "15 ft"},
}


def get_zone_standards(base_zone: str) -> Optional[dict]:
    """Python port of getZoneStandards from zoneStandards.ts."""
    if not base_zone:
        return None

    # Strip prefixes like (T), (Q), [Q], [T]
    cleaned = re.sub(r"^(\([A-Z]+\)|\[[A-Z]+\])+", "", base_zone)

    # Take the part before the height-district dash
    zone_key = cleaned.split("-")[0]

    # Direct match
    if zone_key in ZONE_STANDARDS:
        return ZONE_STANDARDS[zone_key]

    # RE sub-zones
    if zone_key.startswith("RE"):
        re_key = zone_key  # e.g. "RE15"
        if re_key in ZONE_STANDARDS:
            return ZONE_STANDARDS[re_key]
        return ZONE_STANDARDS["RE9"]  # default

    # RD sub-zones (RD1.5 -> RD1_5)
    if zone_key.startswith("RD"):
        rd_key = "RD" + zone_key[2:].replace(".", "_")
        if rd_key in ZONE_STANDARDS:
            return ZONE_STANDARDS[rd_key]
        return ZONE_STANDARDS["RD1_5"]  # default

    # RW fallback
    if zone_key.startswith("RW"):
        return ZONE_STANDARDS["RW1"]

    return None


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestKnownZoneLookups:
    """Verify well-known zone values match the LAMC source data."""

    def test_r1_front_setback(self):
        std = get_zone_standards("R1")
        assert std is not None
        assert std["frontSetback"] == "20% \u2264 20 ft"

    def test_r1_rfa(self):
        std = get_zone_standards("R1")
        assert std["rfa"] == 0.45

    def test_r3_front_setback(self):
        std = get_zone_standards("R3")
        assert std is not None
        assert std["frontSetback"] == "10 ft"

    def test_r4_front_setback(self):
        std = get_zone_standards("R4")
        assert std is not None
        assert std["frontSetback"] == "5 ft"

    def test_r5_front_setback(self):
        std = get_zone_standards("R5")
        assert std is not None
        assert std["frontSetback"] == "5 ft"

    def test_re15_front_setback(self):
        std = get_zone_standards("RE15")
        assert std is not None
        assert std["frontSetback"] == "25 ft"

    def test_r3_has_no_rfa(self):
        std = get_zone_standards("R3")
        assert std["rfa"] is None

    def test_r5_no_height_limit(self):
        std = get_zone_standards("R5")
        assert std["maxHeight"] == "No limit"


class TestZonePrefixStripping:
    """Prefixes like [Q], (T), (Q) should be stripped before lookup."""

    def test_q_prefix_r3(self):
        std = get_zone_standards("[Q]R3-1")
        assert std is not None
        assert std["zone"] == "R3"

    def test_tq_prefix_r1(self):
        std = get_zone_standards("(T)(Q)R1-1")
        assert std is not None
        assert std["zone"] == "R1"

    def test_t_prefix_re15(self):
        std = get_zone_standards("(T)RE15-1-H")
        assert std is not None
        assert std["zone"] == "RE15"

    def test_q_bracket_prefix_r4(self):
        std = get_zone_standards("[Q]R4-2")
        assert std is not None
        assert std["zone"] == "R4"

    def test_height_district_stripped(self):
        """Height district suffix (e.g. -1) should not affect lookup."""
        std = get_zone_standards("R1-1")
        assert std is not None
        assert std["zone"] == "R1"


class TestRESubZones:
    """RE sub-zone matching: RE9, RE11, RE15, RE20, RE40."""

    @pytest.mark.parametrize(
        "zone_str,expected_zone,expected_rfa",
        [
            ("RE9",  "RE9",  0.40),
            ("RE11", "RE11", 0.35),
            ("RE15", "RE15", 0.35),
            ("RE20", "RE20", 0.30),
            ("RE40", "RE40", 0.25),
        ],
    )
    def test_re_zone_resolves(self, zone_str, expected_zone, expected_rfa):
        std = get_zone_standards(zone_str)
        assert std is not None
        assert std["zone"] == expected_zone
        assert std["rfa"] == expected_rfa

    def test_re_with_height_district(self):
        std = get_zone_standards("RE15-1")
        assert std is not None
        assert std["zone"] == "RE15"

    def test_unknown_re_defaults_to_re9(self):
        std = get_zone_standards("RE50")
        assert std is not None
        assert std["zone"] == "RE9"


class TestRDSubZones:
    """RD sub-zone matching: RD1.5, RD2, RD3, etc."""

    @pytest.mark.parametrize(
        "zone_str,expected_zone",
        [
            ("RD1.5", "RD1.5"),
            ("RD2",   "RD2"),
            ("RD3",   "RD3"),
            ("RD4",   "RD4"),
            ("RD5",   "RD5"),
            ("RD6",   "RD6"),
        ],
    )
    def test_rd_zone_resolves(self, zone_str, expected_zone):
        std = get_zone_standards(zone_str)
        assert std is not None
        assert std["zone"] == expected_zone

    def test_rd_with_height_district(self):
        std = get_zone_standards("RD1.5-1")
        assert std is not None
        assert std["zone"] == "RD1.5"

    def test_unknown_rd_defaults_to_rd1_5(self):
        std = get_zone_standards("RD99")
        assert std is not None
        assert std["zone"] == "RD1.5"


class TestUnknownZones:
    """Unknown / unsupported zones should return None."""

    @pytest.mark.parametrize(
        "zone_str",
        [
            "C2",
            "M1",
            "PF",
            "OS",
            "",
            "ZZZZ",
        ],
    )
    def test_unknown_zone_returns_none(self, zone_str):
        assert get_zone_standards(zone_str) is None
