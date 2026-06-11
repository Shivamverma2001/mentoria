from pydantic import BaseModel, Field


class ResumeIngestJsonBody(BaseModel):
    resume_text: str = Field(min_length=1)
    embed: bool = True


class ResumeSignals(BaseModel):
    years_experience: int | None = None
    location: str | None = None
    skills: list[str] = Field(default_factory=list)


class ResumeIngestResponse(BaseModel):
    text_length: int
    word_count: int
    preview: str
    signals: ResumeSignals
    embedding_dimensions: int | None = None
    has_embedding: bool
