from __future__ import annotations

import json
import anthropic
from openai import AsyncOpenAI
from app.config import get_settings
from app.models.schemas import AssessmentResponse, Constraint

ASSESSMENT_SYSTEM_PROMPT = """You are a zoning and regulatory expert for the City of Los Angeles.
Given parcel data and relevant LAMC regulatory text, produce a structured buildability assessment.

You MUST return valid JSON matching this schema:
{
  "summary": "one paragraph plain English verdict",
  "buildable": true/false,
  "confidence_score": 0.0-1.0,
  "confidence_grade": "A/B/C/D",
  "constraints": [
    {
      "rule": "rule name",
      "value": "regulatory limit",
      "applied_to_parcel": "how it applies to this lot",
      "citation": "LAMC section",
      "confidence": "HIGH/MEDIUM/LOW",
      "type": "deterministic/interpretive"
    }
  ],
  "open_questions": ["uncertainty 1", "uncertainty 2"]
}

Rules:
- Only cite LAMC sections that appear in the provided regulatory text
- Mark constraints as "deterministic" when the rule is directly stated and data is complete
- Mark constraints as "interpretive" when you must infer or the rule is ambiguous
- Confidence score should reflect the proportion of HIGH vs MEDIUM vs LOW constraints
- Grade: A=90%+, B=75-89%, C=60-74%, D=<60%
- If an overlay zone applies but rules aren't provided, add it to open_questions
- When lot_width_ft and lot_depth_ft are provided, USE THEM to calculate exact setback distances
  - Front yard setback: calculate using the formula in the code (e.g., 20% of lot depth, max 20ft) and show the CALCULATED value
  - Side yard setback: calculate using lot width if the code specifies a percentage
  - Show your math in the applied_to_parcel field (e.g., "20% of 95ft depth = 19ft")
- Calculate floor area ratio using lot_size_sqft to show maximum buildable square footage
- Calculate lot coverage percentage limits using lot_size_sqft
- Always show specific numeric values, not just the formula
"""


async def run_assessment(
    parcel_data: dict,
    zoning_data: dict,
    buildings: list[dict],
    regulatory_chunks: list[dict],
    building_type: str,
) -> AssessmentResponse:
    """Run Claude assessment on parcel + regulatory data."""
    settings = get_settings()

    chunks_text = "\n\n---\n\n".join(
        f"[{c['section_id']}] {c['topic']}\n{c['text']}" for c in regulatory_chunks
    )

    user_prompt = f"""Assess buildability for the following parcel.

**Building Type:** {building_type}

**Parcel Data:**
{json.dumps(parcel_data, indent=2)}

**Zoning Designations:**
{json.dumps(zoning_data, indent=2)}

**Existing Buildings:**
{json.dumps(buildings, indent=2)}

**Relevant LAMC Regulations:**
{chunks_text}
"""

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    message = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        system=ASSESSMENT_SYSTEM_PROMPT,
        messages=[{"role": "user", "content": user_prompt}],
    )

    raw_text = message.content[0].text
    # Extract JSON from response (handle markdown code blocks)
    if "```json" in raw_text:
        raw_text = raw_text.split("```json")[1].split("```")[0]
    elif "```" in raw_text:
        raw_text = raw_text.split("```")[1].split("```")[0]

    data = json.loads(raw_text)

    return AssessmentResponse(
        apn=parcel_data.get("apn", ""),
        building_type=building_type,
        buildable=data.get("buildable"),
        confidence_score=data["confidence_score"],
        confidence_grade=data["confidence_grade"],
        summary=data["summary"],
        constraints=[Constraint(**c) for c in data["constraints"]],
        open_questions=data.get("open_questions", []),
    )


async def chat_followup(apn: str, message: str, context: str) -> str:
    """GPT-4o chat for follow-up questions about an assessment."""
    settings = get_settings()
    client = AsyncOpenAI(api_key=settings.openai_api_key)

    resp = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a zoning and regulatory assistant for residential parcels in Los Angeles. "
                    "You ONLY answer questions about zoning, building regulations, setbacks, height limits, "
                    "FAR, lot coverage, ADUs, permits, and buildability for the specific parcel in context. "
                    "If the user asks about anything unrelated to zoning, building regulations, or this parcel, "
                    "politely decline and redirect them to ask about the property assessment. "
                    "Use the provided context to answer. If the answer isn't in the context, say so clearly "
                    "and suggest they consult a licensed architect or the LA Department of Building and Safety.\n\n"
                    f"Context:\n{context}"
                ),
            },
            {"role": "user", "content": message},
        ],
        max_tokens=1024,
    )
    return resp.choices[0].message.content
