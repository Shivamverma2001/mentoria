from fastapi import APIRouter

router = APIRouter(tags=["meta"])


@router.get("/api", summary="API index")
async def api_index() -> dict:
    return {
        "name": "Arya Smart Job Matcher API",
        "version": "0.1.0",
        "docs": "/docs",
        "openapi": "/openapi.json",
        "endpoints": {
            "health": "GET /api/health",
            "jobs": "GET /api/jobs",
            "job": "GET /api/jobs/{job_id}",
            "resume_ingest": "POST /api/resume/ingest",
            "match_stream": "POST /api/match/stream",
            "match_stream_json": "POST /api/match/stream/json",
        },
    }
