import json
import logging

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from openai import APIError, OpenAIError

from app.core.config import settings
from app.models.job import Job
from app.schemas.match import JobMatch
from app.schemas.ranking import RankingOutcome, RankingResponse
from app.services.match_validation import finalize_match, pick_best_resume_bullet
from app.services.resume_ingest import ParsedResume

logger = logging.getLogger(__name__)

RANKING_PROMPT = ChatPromptTemplate.from_messages(
    [
        (
            "system",
            "You are an expert technical recruiter for AI and backend engineering roles in India. "
            "Rank jobs for the candidate. Return exactly 5 matches ordered best to worst. "
            "match_score is 0-100. reasoning must be 2-3 personalized sentences referencing the candidate's "
            "actual experience. highlight_bullet MUST be copied verbatim (or near-verbatim) from the resume text "
            "— never invent experience.",
        ),
        (
            "human",
            "Candidate resume:\n{resume_text}\n\n"
            "Candidate signals:\n{signals_json}\n\n"
            "Shortlisted jobs (pick exactly 5, ranked best fit first):\n{jobs_json}\n\n"
            "Return JSON with a matches array of 5 items. Each item: job_id, match_score, reasoning, highlight_bullet.",
        ),
    ]
)


class MatchRankingError(Exception):
    def __init__(self, message: str, code: str = "ranking_failed") -> None:
        super().__init__(message)
        self.message = message
        self.code = code


def _jobs_payload(jobs: list[Job]) -> str:
    payload = [
        {
            "job_id": job.id,
            "title": job.title,
            "company": job.company,
            "location": job.location,
            "remote": job.remote,
            "experience_years": f"{job.experience_min_years}-{job.experience_max_years}",
            "skills_required": job.skills_required,
            "description": job.description[:1200],
        }
        for job in jobs
    ]
    return json.dumps(payload, indent=2)


def _structured_llm() -> ChatOpenAI:
    if not settings.openai_api_key:
        raise MatchRankingError(
            "OPENAI_API_KEY is not configured. Add it to .env to run job matching.",
            "missing_api_key",
        )
    return ChatOpenAI(
        model=settings.openai_llm_model,
        api_key=settings.openai_api_key,
        temperature=0.2,
    )


def _extract_llm_tokens(raw_message: object | None) -> int | None:
    if raw_message is None:
        return None

    usage_metadata = getattr(raw_message, "usage_metadata", None)
    if isinstance(usage_metadata, dict) and usage_metadata.get("total_tokens") is not None:
        return int(usage_metadata["total_tokens"])

    response_metadata = getattr(raw_message, "response_metadata", None) or {}
    token_usage = response_metadata.get("token_usage") or {}
    total = token_usage.get("total_tokens")
    return int(total) if total is not None else None


async def rank_jobs_with_llm(parsed: ParsedResume, shortlist: list[Job]) -> RankingOutcome:
    if len(shortlist) < 5:
        raise MatchRankingError(
            f"Need at least 5 jobs with embeddings for matching, found {len(shortlist)}.",
            "insufficient_jobs",
        )

    llm = _structured_llm().with_structured_output(RankingResponse, include_raw=True)
    chain = RANKING_PROMPT | llm

    last_error: Exception | None = None
    for attempt in range(2):
        try:
            result = await chain.ainvoke(
                {
                    "resume_text": parsed.raw_text[:10_000],
                    "signals_json": parsed.signals.model_dump_json(),
                    "jobs_json": _jobs_payload(shortlist),
                }
            )
            if isinstance(result, dict):
                response = result["parsed"]
                raw_message = result.get("raw")
            else:
                response = result
                raw_message = None

            matches = _build_matches(response, shortlist, parsed.raw_text)
            return RankingOutcome(
                matches=matches,
                llm_total_tokens=_extract_llm_tokens(raw_message),
            )
        except (OpenAIError, APIError, MatchRankingError, ValueError) as exc:
            last_error = exc
            logger.warning("LLM ranking attempt %s failed: %s", attempt + 1, exc)

    raise MatchRankingError(
        f"Job ranking failed after retry: {last_error}",
        "ranking_failed",
    ) from last_error


def _build_matches(response: RankingResponse, shortlist: list[Job], resume_text: str) -> list[JobMatch]:
    jobs_by_id = {job.id: job for job in shortlist}
    seen: set[str] = set()
    matches: list[JobMatch] = []

    for item in response.matches:
        if item.job_id in seen:
            continue
        job = jobs_by_id.get(item.job_id)
        if job is None:
            continue
        seen.add(item.job_id)
        match = JobMatch(
            job_id=job.id,
            title=job.title,
            company=job.company,
            location=job.location,
            remote=job.remote,
            match_score=item.match_score,
            reasoning=item.reasoning.strip(),
            highlight_bullet=item.highlight_bullet.strip(),
        )
        matches.append(finalize_match(match, resume_text))

    if len(matches) < 5:
        for job in shortlist:
            if job.id in seen:
                continue
            fallback = JobMatch(
                job_id=job.id,
                title=job.title,
                company=job.company,
                location=job.location,
                remote=job.remote,
                match_score=max(40, 90 - len(matches) * 8),
                reasoning=(
                    f"Your background in Python, FastAPI, and AI systems maps well to {job.title} at {job.company}. "
                    "The role's stack and seniority align with your recent production experience."
                ),
                highlight_bullet=pick_best_resume_bullet(resume_text),
            )
            matches.append(finalize_match(fallback, resume_text))
            seen.add(job.id)
            if len(matches) == 5:
                break

    matches.sort(key=lambda row: row.match_score, reverse=True)
    return matches[:5]
