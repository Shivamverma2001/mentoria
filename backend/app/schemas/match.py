from typing import Literal

from pydantic import BaseModel, Field


class MatchJsonBody(BaseModel):
    """JSON body for POST /api/match/stream/json."""

    resume_text: str = Field(min_length=1, description="Full resume plain text")


class JobMatch(BaseModel):
    job_id: str
    title: str
    company: str
    location: str
    remote: str
    match_score: int = Field(ge=0, le=100)
    reasoning: str
    highlight_bullet: str


class StatusEvent(BaseModel):
    stage: Literal["parsing", "embedding", "retrieving", "ranking"]


class DoneEvent(BaseModel):
    total: int
    duration_ms: int
    cache_hit: bool = False


class ErrorEvent(BaseModel):
    message: str


class MatchStreamEvent(BaseModel):
    event: Literal["status", "match", "done", "error"]
    data: StatusEvent | JobMatch | DoneEvent | ErrorEvent
