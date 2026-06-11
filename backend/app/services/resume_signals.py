import re

from app.schemas.resume import ResumeSignals

COMMON_SKILLS = [
    "Python",
    "FastAPI",
    "TypeScript",
    "JavaScript",
    "React",
    "Node.js",
    "PostgreSQL",
    "Redis",
    "Kafka",
    "AWS",
    "Docker",
    "Kubernetes",
    "LangChain",
    "LangGraph",
    "OpenAI",
    "Anthropic",
    "PyTorch",
    "SQL",
    "Java",
    "Go",
    "Ruby",
    "Celery",
    "GraphQL",
    "MongoDB",
    "Terraform",
    "MLOps",
    "RAG",
    "LLM",
    "Microservices",
    "asyncio",
    "Sentry",
    "Git",
]

INDIAN_CITIES = [
    "Bengaluru",
    "Bangalore",
    "Mumbai",
    "Delhi",
    "Gurgaon",
    "Gurugram",
    "Hyderabad",
    "Chennai",
    "Pune",
    "Noida",
    "Kolkata",
]

YEARS_PATTERN = re.compile(
    r"(?i)(\d{1,2})\+?\s*(?:years?|yrs?)(?:\s+of)?\s+(?:experience|exp)",
)
SENIORITY_PATTERN = re.compile(r"(?i)\b(senior|staff|principal|lead)\b")


def extract_years_experience(text: str) -> int | None:
    matches = [int(match.group(1)) for match in YEARS_PATTERN.finditer(text)]
    if matches:
        return max(matches)

    summary_match = re.search(r"(?i)with\s+(\d{1,2})\+?\s+years?", text)
    if summary_match:
        return int(summary_match.group(1))

    if SENIORITY_PATTERN.search(text):
        return 5
    return None


def extract_location(text: str) -> str | None:
    for city in INDIAN_CITIES:
        if re.search(rf"\b{re.escape(city)}\b", text, flags=re.IGNORECASE):
            return "Bengaluru, India" if city.lower() == "bangalore" else f"{city}, India"

    remote_match = re.search(r"(?i)\b(remote|hybrid|onsite)\b", text)
    if remote_match:
        return remote_match.group(1).lower()
    return None


def extract_skills(text: str) -> list[str]:
    found: list[str] = []
    lowered = text.lower()
    for skill in COMMON_SKILLS:
        pattern = rf"\b{re.escape(skill.lower())}\b"
        if re.search(pattern, lowered):
            found.append(skill)
    return found[:20]


def extract_resume_signals(text: str) -> ResumeSignals:
    return ResumeSignals(
        years_experience=extract_years_experience(text),
        location=extract_location(text),
        skills=extract_skills(text),
    )
