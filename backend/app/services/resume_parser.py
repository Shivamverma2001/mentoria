import re
from io import BytesIO

from fastapi import UploadFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError

from app.services.resume_errors import ResumeParseError

MIN_RESUME_CHARS = 80
MIN_RESUME_WORDS = 15


def normalize_resume_text(text: str) -> str:
    cleaned = text.replace("\x00", " ")
    cleaned = re.sub(r"[ \t]+", " ", cleaned)
    cleaned = re.sub(r"\n{3,}", "\n\n", cleaned)
    return cleaned.strip()


def validate_resume_text(text: str) -> str:
    normalized = normalize_resume_text(text)
    if not normalized:
        raise ResumeParseError("Resume text is empty. Paste your resume or upload a PDF.", "empty_resume")

    word_count = len(normalized.split())
    if len(normalized) < MIN_RESUME_CHARS or word_count < MIN_RESUME_WORDS:
        raise ResumeParseError(
            "Resume text is too short to analyze. Provide a complete resume with experience and skills.",
            "resume_too_short",
        )
    return normalized


def extract_text_from_pdf_bytes(content: bytes) -> str:
    if not content:
        raise ResumeParseError("Uploaded PDF file is empty.", "empty_pdf")

    try:
        reader = PdfReader(BytesIO(content), strict=False)
    except PdfReadError as exc:
        raise ResumeParseError(
            "Could not read the PDF. The file may be corrupted or password-protected.",
            "unreadable_pdf",
        ) from exc

    if len(reader.pages) == 0:
        raise ResumeParseError("The PDF has no pages.", "empty_pdf")

    page_texts: list[str] = []
    for page in reader.pages:
        extracted = page.extract_text() or ""
        if extracted.strip():
            page_texts.append(extracted)

    combined = normalize_resume_text("\n".join(page_texts))
    if not combined:
        raise ResumeParseError(
            "No readable text found in the PDF. It may be a scanned image-only resume; paste the text instead.",
            "image_only_pdf",
        )
    return combined


async def extract_text_from_upload(file: UploadFile) -> str:
    filename = (file.filename or "").lower()
    content_type = (file.content_type or "").lower()

    if filename and not filename.endswith(".pdf"):
        raise ResumeParseError("Only PDF uploads are supported. Use .pdf or paste resume text.", "invalid_file_type")

    if content_type and content_type not in {"application/pdf", "application/x-pdf", "binary/octet-stream"}:
        raise ResumeParseError(
            f"Unsupported file type '{file.content_type}'. Upload a PDF or paste resume text.",
            "invalid_file_type",
        )

    content = await file.read()
    if not content.startswith(b"%PDF"):
        raise ResumeParseError(
            "Uploaded file does not look like a valid PDF. Paste your resume text instead.",
            "invalid_pdf_header",
        )

    return extract_text_from_pdf_bytes(content)


def parse_resume_input(resume_text: str | None, pdf_text: str | None = None) -> str:
    if pdf_text:
        return validate_resume_text(pdf_text)
    if resume_text is not None:
        return validate_resume_text(resume_text)
    raise ResumeParseError(
        "Provide resume_text (paste) or resume_file (PDF upload).",
        "missing_resume_input",
    )
