from pydantic import BaseModel, Field


class RankingItem(BaseModel):
    job_id: str
    match_score: int = Field(ge=0, le=100)
    reasoning: str = Field(min_length=20)
    highlight_bullet: str = Field(min_length=10)


class RankingResponse(BaseModel):
    matches: list[RankingItem] = Field(min_length=1, max_length=5)
