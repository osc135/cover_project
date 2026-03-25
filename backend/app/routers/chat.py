from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
import json

from app.db import get_db
from app.models.schemas import ChatRequest, ChatResponse
from app.services.llm import chat_followup

router = APIRouter()


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

    context = json.dumps({
        "apn": assessment.apn,
        "building_type": assessment.building_type,
        "summary": assessment.summary,
        "constraints": assessment.constraints if isinstance(assessment.constraints, dict) else json.loads(assessment.constraints),
        "open_questions": assessment.open_questions if isinstance(assessment.open_questions, list) else json.loads(assessment.open_questions),
    }, indent=2)

    reply = await chat_followup(req.apn, req.message, context)
    return ChatResponse(reply=reply)
