from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.services.matcher import stream_job_match

router = APIRouter(prefix="/api/match", tags=["match"])


class MatchJsonBody(BaseModel):
    resume_text: str = Field(min_length=1)


def _stream_response(generator) -> StreamingResponse:
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/stream")
async def match_jobs_stream(
    resume_text: str | None = Form(default=None),
    resume_file: UploadFile | None = File(default=None),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return _stream_response(
        stream_job_match(db, resume_text=resume_text, resume_file=resume_file)
    )


@router.post("/stream/json")
async def match_jobs_stream_json(
    body: MatchJsonBody,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return _stream_response(stream_job_match(db, resume_text=body.resume_text))
