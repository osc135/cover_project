import logging
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.db import get_db
from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm import chat_followup

logger = logging.getLogger(__name__)
router = APIRouter()


def _parse_json_field(val):
    if val is None:
        return []
    if isinstance(val, (list, dict)):
        return val
    if isinstance(val, str):
        return json.loads(val)
    return val


@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, db: AsyncSession = Depends(get_db)):
    # Get the most recent assessment for this parcel as context
    row = await db.execute(
        text("SELECT * FROM assessments WHERE apn = :apn ORDER BY created_at DESC LIMIT 1"),
        {"apn": req.apn},
    )
    assessment = row.fetchone()
    if not assessment:
        raise HTTPException(status_code=404, detail="No assessment found for this parcel")

    try:
        context = json.dumps({
            "apn": assessment.apn,
            "building_type": assessment.building_type,
            "summary": assessment.summary,
            "constraints": _parse_json_field(assessment.constraints),
            "open_questions": _parse_json_field(assessment.open_questions),
        }, indent=2, default=str)
    except Exception as e:
        logger.error(f"Failed to build chat context: {e}")
        context = f"Assessment for {assessment.apn}: {assessment.summary}"

    try:
        reply = await chat_followup(req.apn, req.message, context)
        return ChatResponse(reply=reply)
    except Exception as e:
        logger.error(f"Chat failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
