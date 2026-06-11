from fastapi import APIRouter, File, Form, Query, UploadFile

from app.schemas.resume import ResumeIngestJsonBody, ResumeIngestResponse
from app.services.resume_ingest import ingest_resume
from app.services.resume_parser import normalize_resume_text

router = APIRouter(prefix="/api/resume", tags=["resume"])


def _to_response(parsed) -> ResumeIngestResponse:
    words = parsed.raw_text.split()
    preview = parsed.raw_text[:240]
    if len(parsed.raw_text) > 240:
        preview += "…"

    return ResumeIngestResponse(
        text_length=len(parsed.raw_text),
        word_count=len(words),
        preview=preview,
        signals=parsed.signals,
        embedding_dimensions=len(parsed.embedding) if parsed.embedding else None,
        has_embedding=parsed.embedding is not None,
    )


@router.post(
    "/ingest",
    response_model=ResumeIngestResponse,
    summary="Parse resume (form: paste or PDF)",
)
async def ingest_resume_form(
    resume_text: str | None = Form(default=None),
    resume_file: UploadFile | None = File(default=None),
    embed: bool = Query(default=True, description="Generate OpenAI embedding"),
) -> ResumeIngestResponse:
    if resume_text is not None:
        resume_text = normalize_resume_text(resume_text) or None

    parsed = await ingest_resume(resume_text=resume_text, resume_file=resume_file, embed=embed)
    return _to_response(parsed)


@router.post(
    "/ingest/json",
    response_model=ResumeIngestResponse,
    summary="Parse resume (JSON body)",
)
async def ingest_resume_json(body: ResumeIngestJsonBody) -> ResumeIngestResponse:
    parsed = await ingest_resume(resume_text=body.resume_text, resume_file=None, embed=body.embed)
    return _to_response(parsed)
