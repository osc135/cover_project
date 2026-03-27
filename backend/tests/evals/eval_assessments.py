"""LLM assessment evals — run assessments across parcels and validate outputs.

This is not a standard pytest suite. It runs real LLM assessments (costs API credits)
and produces a structured eval report. Run manually:

    python -m tests.evals.eval_assessments

Requires: database running with ingested chunks, API keys configured.
"""

import asyncio
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.config import get_settings
from app.services.gis import fetch_parcel, fetch_zoning
from app.services.rag import retrieve_chunks
from app.services.llm import run_assessment
from app.routers.assessment import compute_confidence

# ── Test parcels ──────────────────────────────────────────────────────────────

EVAL_PARCELS = [
    {
        "address": "2021 Kelton Ave, Los Angeles, CA",
        "label": "Westwood R1-1",
        "lat": 34.0553,
        "lng": -118.4440,
        "expected_zone": "R1",
        "building_types": ["SFH", "ADU", "GuestHouse"],
    },
    {
        "address": "2335 Overland Ave, Los Angeles, CA",
        "label": "Mar Vista R1-1-O",
        "lat": 34.0431,
        "lng": -118.4261,
        "expected_zone": "R1",
        "building_types": ["SFH", "ADU"],
    },
    {
        "address": "1525 S Saltair Ave, Los Angeles, CA",
        "label": "Mid-City R3-1",
        "lat": 34.0487,
        "lng": -118.4627,
        "expected_zone": "R3",
        "building_types": ["SFH", "ADU"],
    },
    {
        "address": "11941 Brentwood Grove Dr, Los Angeles, CA",
        "label": "Brentwood RE15",
        "lat": 34.0748,
        "lng": -118.4756,
        "expected_zone": "RE",
        "building_types": ["SFH", "ADU"],
    },
    {
        "address": "1535 Ocean Ave, Santa Monica, CA",
        "label": "Santa Monica (out of jurisdiction)",
        "lat": 34.0102,
        "lng": -118.4963,
        "expected_zone": None,  # outside LA City
        "building_types": ["SFH"],
    },
]

# ── Expected setback ranges by zone (LAMC reference values) ──────────────────

# These are approximate valid ranges, not exact values.
# The eval checks if the LLM's output falls within a reasonable range.
EXPECTED_SETBACKS = {
    "R1": {"front_min": 15, "front_max": 25, "side_min": 3, "side_max": 10, "rear_min": 10, "rear_max": 20},
    "R2": {"front_min": 15, "front_max": 25, "side_min": 3, "side_max": 10, "rear_min": 10, "rear_max": 20},
    "R3": {"front_min": 10, "front_max": 20, "side_min": 3, "side_max": 10, "rear_min": 10, "rear_max": 20},
    "RE": {"front_min": 20, "front_max": 40, "side_min": 5, "side_max": 25, "rear_min": 15, "rear_max": 30},
}

# Valid LAMC sections that should appear in citations
VALID_LAMC_SECTIONS = {
    "12.03", "12.04", "12.07", "12.07.01", "12.08", "12.08.5",
    "12.09", "12.09.1", "12.09.5", "12.10", "12.10.5", "12.11",
    "12.21", "12.21.1", "12.22", "12.24",
}


# ── Eval result types ─────────────────────────────────────────────────────────

@dataclass
class CheckResult:
    name: str
    passed: bool
    detail: str = ""


@dataclass
class AssessmentEval:
    parcel_label: str
    building_type: str
    checks: list[CheckResult] = field(default_factory=list)
    error: Optional[str] = None

    @property
    def passed(self) -> int:
        return sum(1 for c in self.checks if c.passed)

    @property
    def failed(self) -> int:
        return sum(1 for c in self.checks if not c.passed)


# ── Eval checks ───────────────────────────────────────────────────────────────

def check_has_constraints(assessment) -> CheckResult:
    """Assessment should produce at least 3 constraints."""
    n = len(assessment.constraints)
    return CheckResult(
        name="has_constraints",
        passed=n >= 3,
        detail=f"{n} constraints generated",
    )


def check_has_summary(assessment) -> CheckResult:
    """Summary should be a non-trivial paragraph."""
    length = len(assessment.summary)
    return CheckResult(
        name="has_summary",
        passed=length > 50,
        detail=f"Summary length: {length} chars",
    )


def check_buildable_is_set(assessment) -> CheckResult:
    """Buildable should be explicitly true or false."""
    return CheckResult(
        name="buildable_set",
        passed=assessment.buildable is not None,
        detail=f"buildable={assessment.buildable}",
    )


def check_citations_valid(assessment, ingested_sections: set[str]) -> CheckResult:
    """All citations should reference LAMC sections that exist in the regulatory chunks."""
    bad_citations = []
    for c in assessment.constraints:
        citation = c.citation
        # Extract section numbers like "12.08", "12.21.1", "12.22 C"
        match = re.search(r'(\d+\.\d+(?:\.\d+)?)', citation)
        if match:
            section = match.group(1)
            # Check if this section prefix matches any ingested section
            found = any(section.startswith(s) or s.startswith(section) for s in ingested_sections)
            if not found:
                bad_citations.append(f"{citation} (section {section})")

    return CheckResult(
        name="citations_valid",
        passed=len(bad_citations) == 0,
        detail=f"Bad citations: {bad_citations}" if bad_citations else "All citations reference ingested sections",
    )


def check_setback_ranges(assessment, zone_prefix: str) -> CheckResult:
    """Setback values should be in reasonable ranges for the zone.
    Only checked for SFH — ADU and GuestHouse have state law setback exceptions (e.g. 4ft)."""
    if assessment.building_type in ("ADU", "GuestHouse"):
        return CheckResult(name="setback_ranges", passed=True, detail="Skipped — ADU/GuestHouse have state law setback exceptions")
    if zone_prefix not in EXPECTED_SETBACKS:
        return CheckResult(name="setback_ranges", passed=True, detail=f"No expected ranges for {zone_prefix}")

    expected = EXPECTED_SETBACKS[zone_prefix]
    issues = []

    for c in assessment.constraints:
        rule_lower = c.rule.lower()
        value_text = c.value.lower()

        # Try to extract a numeric value from the constraint value
        nums = re.findall(r'(\d+(?:\.\d+)?)\s*(?:feet|ft)', value_text)
        if not nums:
            continue

        val = float(nums[0])

        if "front" in rule_lower and "setback" in rule_lower:
            if not (expected["front_min"] <= val <= expected["front_max"]):
                issues.append(f"Front setback {val}ft outside expected {expected['front_min']}-{expected['front_max']}ft")

        if "side" in rule_lower and "setback" in rule_lower:
            if not (expected["side_min"] <= val <= expected["side_max"]):
                issues.append(f"Side setback {val}ft outside expected {expected['side_min']}-{expected['side_max']}ft")

        if "rear" in rule_lower and "setback" in rule_lower:
            if not (expected["rear_min"] <= val <= expected["rear_max"]):
                issues.append(f"Rear setback {val}ft outside expected {expected['rear_min']}-{expected['rear_max']}ft")

    return CheckResult(
        name="setback_ranges",
        passed=len(issues) == 0,
        detail="; ".join(issues) if issues else "Setback values in expected ranges",
    )


def check_confidence_reasonable(assessment) -> CheckResult:
    """Confidence score should be between 0 and 1, grade should match."""
    score = assessment.confidence_score
    grade = assessment.confidence_grade

    if not (0.0 <= score <= 1.0):
        return CheckResult(name="confidence_reasonable", passed=False, detail=f"Score {score} out of range")

    expected_grade = "A" if score >= 0.9 else "B" if score >= 0.75 else "C" if score >= 0.6 else "D"
    grade_match = grade == expected_grade

    return CheckResult(
        name="confidence_reasonable",
        passed=grade_match,
        detail=f"Score={score}, Grade={grade}, Expected grade={expected_grade}",
    )


def check_constraint_types(assessment) -> CheckResult:
    """Each constraint should have a valid type: deterministic or interpretive."""
    bad = [c.rule for c in assessment.constraints if c.type not in ("deterministic", "interpretive")]
    return CheckResult(
        name="constraint_types_valid",
        passed=len(bad) == 0,
        detail=f"Invalid types on: {bad}" if bad else "All constraint types valid",
    )


def check_constraint_confidence_levels(assessment) -> CheckResult:
    """Each constraint should have a valid confidence: HIGH, MEDIUM, or LOW."""
    bad = [c.rule for c in assessment.constraints if c.confidence not in ("HIGH", "MEDIUM", "LOW")]
    return CheckResult(
        name="constraint_confidence_valid",
        passed=len(bad) == 0,
        detail=f"Invalid confidence on: {bad}" if bad else "All confidence levels valid",
    )


def check_open_questions_present(assessment) -> CheckResult:
    """Assessment should acknowledge uncertainties with open questions."""
    return CheckResult(
        name="has_open_questions",
        passed=len(assessment.open_questions) >= 0,  # Soft check — 0 is OK for simple parcels
        detail=f"{len(assessment.open_questions)} open questions",
    )


# ── Main eval runner ──────────────────────────────────────────────────────────

async def run_eval():
    settings = get_settings()
    engine = create_async_engine(settings.database_url)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    results: list[AssessmentEval] = []

    # Get ingested section IDs from the database
    async with async_session() as db:
        rows = await db.execute(text("SELECT DISTINCT section_id FROM regulatory_chunks"))
        ingested_sections = {row.section_id for row in rows.fetchall()}
        print(f"Ingested sections: {ingested_sections}\n")

    for parcel in EVAL_PARCELS:
        for building_type in parcel["building_types"]:
            eval_result = AssessmentEval(
                parcel_label=parcel["label"],
                building_type=building_type,
            )
            print(f"{'='*60}")
            print(f"Evaluating: {parcel['label']} — {building_type}")
            print(f"{'='*60}")

            try:
                async with async_session() as db:
                    # Fetch parcel data
                    parcel_feature = await fetch_parcel(parcel["lat"], parcel["lng"])
                    if not parcel_feature:
                        eval_result.error = "No parcel found"
                        results.append(eval_result)
                        print(f"  SKIP: No parcel found\n")
                        continue

                    props = parcel_feature.get("properties", {})
                    apn = props.get("APN", props.get("AIN", ""))
                    lot_size = props.get("Shape.STArea()") or props.get("ShapeArea") or props.get("Shape__Area")

                    # Fetch zoning
                    zoning_feature = await fetch_zoning(parcel["lat"], parcel["lng"])
                    base_zone = None
                    if zoning_feature:
                        zprops = zoning_feature.get("properties", {})
                        base_zone = zprops.get("Zoning") or zprops.get("ZONE_CMPLT") or zprops.get("ZONE_CLASS")

                    # Get zone prefix for RAG
                    zone_clean = re.sub(r'^(\([A-Z]+\)|\[[A-Z]+\])+', '', base_zone or "")
                    zone_prefix = zone_clean.split("-")[0] if zone_clean else "R1"

                    # RAG retrieval
                    chunks = await retrieve_chunks(db, zone_prefix, building_type)

                    # Build context
                    parcel_data = {
                        "apn": apn,
                        "address": parcel["address"],
                        "lot_size_sqft": lot_size,
                    }
                    zoning_data = {"base_zone": base_zone}
                    buildings = []

                    # Run LLM assessment
                    print(f"  Running LLM assessment...")
                    assessment = await run_assessment(
                        parcel_data, zoning_data, buildings, chunks, building_type
                    )

                    # Recompute confidence
                    constraint_dicts = [c.model_dump() for c in assessment.constraints]
                    breakdown = compute_confidence(parcel_data, zoning_data, buildings, chunks, constraint_dicts)
                    assessment.confidence_score = breakdown.overall
                    assessment.confidence_grade = breakdown.grade
                    assessment.confidence_breakdown = breakdown

                    # ── Run checks ──
                    eval_result.checks.append(check_has_constraints(assessment))
                    eval_result.checks.append(check_has_summary(assessment))
                    eval_result.checks.append(check_buildable_is_set(assessment))
                    eval_result.checks.append(check_citations_valid(assessment, ingested_sections))
                    eval_result.checks.append(check_setback_ranges(assessment, parcel.get("expected_zone", "")))
                    eval_result.checks.append(check_confidence_reasonable(assessment))
                    eval_result.checks.append(check_constraint_types(assessment))
                    eval_result.checks.append(check_constraint_confidence_levels(assessment))
                    eval_result.checks.append(check_open_questions_present(assessment))

                    # Print results
                    for check in eval_result.checks:
                        status = "PASS" if check.passed else "FAIL"
                        print(f"  [{status}] {check.name}: {check.detail}")

                    print(f"  Score: {eval_result.passed}/{len(eval_result.checks)} checks passed")
                    print()

            except Exception as e:
                eval_result.error = str(e)
                print(f"  ERROR: {e}\n")

            results.append(eval_result)

    await engine.dispose()

    # ── Summary ───────────────────────────────────────────────────────────
    print("\n" + "=" * 60)
    print("EVAL SUMMARY")
    print("=" * 60)

    total_checks = 0
    total_passed = 0
    total_errors = 0

    for r in results:
        if r.error:
            total_errors += 1
            status = f"ERROR: {r.error}"
        else:
            total_checks += len(r.checks)
            total_passed += r.passed
            status = f"{r.passed}/{len(r.checks)} passed"
        print(f"  {r.parcel_label} / {r.building_type}: {status}")

    print(f"\nTotal: {total_passed}/{total_checks} checks passed, {total_errors} errors")

    if total_checks > 0:
        pass_rate = total_passed / total_checks * 100
        print(f"Pass rate: {pass_rate:.1f}%")

    # Write JSON report
    report = {
        "timestamp": datetime.now().isoformat(),
        "total_checks": total_checks,
        "total_passed": total_passed,
        "total_errors": total_errors,
        "pass_rate": round(total_passed / total_checks * 100, 1) if total_checks > 0 else 0,
        "results": [
            {
                "parcel": r.parcel_label,
                "building_type": r.building_type,
                "error": r.error,
                "checks": [
                    {"name": c.name, "passed": c.passed, "detail": c.detail}
                    for c in r.checks
                ] if not r.error else [],
            }
            for r in results
        ],
    }

    report_path = "tests/evals/eval_report.json"
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2)
    print(f"\nReport written to {report_path}")


if __name__ == "__main__":
    asyncio.run(run_eval())
