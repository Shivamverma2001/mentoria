from fastapi import APIRouter, Depends, File, Form, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.match import MatchJsonBody
from app.services.matcher import stream_job_match

router = APIRouter(prefix="/api/match", tags=["match"])


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


@router.post(
    "/stream",
    summary="Match resume to jobs (SSE stream)",
    description=(
        "Upload or paste a resume and receive top 5 job matches as Server-Sent Events. "
        "Events: `status` (parsing/embedding/retrieving/ranking), `match` (JobMatch), "
        "`done` (duration + cache_hit), `error`."
    ),
    responses={
        200: {
            "description": "SSE stream (`text/event-stream`)",
            "content": {"text/event-stream": {"example": 'event: match\ndata: {"job_id":"job_005",...}\n\n'}},
        }
    },
)
async def match_jobs_stream(
    resume_text: str | None = Form(default=None, description="Pasted resume plain text"),
    resume_file: UploadFile | None = File(default=None, description="Resume PDF upload"),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return _stream_response(
        stream_job_match(db, resume_text=resume_text, resume_file=resume_file)
    )


@router.post(
    "/stream/json",
    summary="Match resume to jobs via JSON body (SSE stream)",
    description="Same SSE stream as `/stream`, with `{\"resume_text\": \"...\"}` JSON body.",
)
async def match_jobs_stream_json(
    body: MatchJsonBody,
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    return _stream_response(stream_job_match(db, resume_text=body.resume_text))
