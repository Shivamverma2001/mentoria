from dataclasses import dataclass

from fastapi import UploadFile

from app.schemas.resume import ResumeSignals
from app.services.embeddings import embed_text
from app.services.resume_parser import extract_text_from_upload, parse_resume_input, validate_resume_text
from app.services.resume_signals import extract_resume_signals


@dataclass
class ParsedResume:
    raw_text: str
    signals: ResumeSignals
    embedding: list[float] | None = None


async def ingest_resume(
    *,
    resume_text: str | None = None,
    resume_file: UploadFile | None = None,
    embed: bool = True,
) -> ParsedResume:
    pdf_text: str | None = None
    if resume_file is not None and resume_file.filename:
        pdf_text = await extract_text_from_upload(resume_file)

    raw_text = parse_resume_input(resume_text=resume_text, pdf_text=pdf_text)
    signals = extract_resume_signals(raw_text)

    embedding: list[float] | None = None
    if embed:
        embedding = await embed_text(raw_text)

    return ParsedResume(raw_text=raw_text, signals=signals, embedding=embedding)


def ingest_resume_text_only(resume_text: str, *, embed: bool = False) -> ParsedResume:
    """Synchronous helper for scripts/tests without OpenAI calls."""
    raw_text = validate_resume_text(resume_text)
    signals = extract_resume_signals(raw_text)
    return ParsedResume(raw_text=raw_text, signals=signals, embedding=None)
