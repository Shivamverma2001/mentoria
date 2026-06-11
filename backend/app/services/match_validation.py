import re
from difflib import SequenceMatcher

from app.schemas.match import JobMatch


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def _resume_lines(resume_text: str) -> list[str]:
    lines: list[str] = []
    for line in resume_text.splitlines():
        cleaned = re.sub(r"^[\s•\-\*]+", "", line).strip()
        if len(cleaned) > 20:
            lines.append(cleaned)
    return lines


def highlight_in_resume(highlight_bullet: str, resume_text: str, *, min_ratio: float = 0.72) -> bool:
    bullet_norm = _normalize(highlight_bullet)
    resume_norm = _normalize(resume_text)

    if bullet_norm and bullet_norm in resume_norm:
        return True

    for line in _resume_lines(resume_text):
        line_norm = _normalize(line)
        if bullet_norm in line_norm or line_norm in bullet_norm:
            return True
        if SequenceMatcher(None, bullet_norm, line_norm).ratio() >= min_ratio:
            return True
    return False


def pick_best_resume_bullet(resume_text: str) -> str:
    lines = _resume_lines(resume_text)
    if not lines:
        return resume_text[:200].strip()
    return max(lines, key=len)


def reasoning_is_valid(reasoning: str) -> bool:
    text = reasoning.strip()
    if len(text) < 40:
        return False
    sentences = [part.strip() for part in re.split(r"[.!?]+", text) if part.strip()]
    return 1 <= len(sentences) <= 4


def finalize_match(match: JobMatch, resume_text: str) -> JobMatch:
    reasoning = match.reasoning.strip()
    if not reasoning_is_valid(reasoning):
        reasoning = (
            f"{reasoning} This role aligns with your backend and AI experience, "
            "and the stack overlap makes you a strong candidate."
        ).strip()

    highlight = match.highlight_bullet.strip()
    if not highlight_in_resume(highlight, resume_text):
        highlight = pick_best_resume_bullet(resume_text)

    return match.model_copy(update={"reasoning": reasoning, "highlight_bullet": highlight})
