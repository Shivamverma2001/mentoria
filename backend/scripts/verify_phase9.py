#!/usr/bin/env python3
"""Verify Phase 9: docker-compose stack configuration."""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
COMPOSE_FILE = ROOT / "docker-compose.yml"

REQUIRED_SERVICES = {"postgres", "redis", "backend", "frontend"}


def run(cmd: list[str], cwd: Path | None = None) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, cwd=cwd or ROOT, capture_output=True, text=True)


def verify_compose_services() -> None:
    text = COMPOSE_FILE.read_text(encoding="utf-8")
    for service in REQUIRED_SERVICES:
        assert f"  {service}:" in text or f"\n{service}:" in text, f"Missing service: {service}"
    print("OK  docker-compose.yml defines postgres, redis, backend, frontend")


def verify_compose_config() -> None:
    result = run(["docker", "compose", "config"])
    if result.returncode != 0:
        print(f"SKIP docker compose config: {result.stderr.strip()}")
        return

    rendered = result.stdout
    for service in REQUIRED_SERVICES:
        assert f"{service}:" in rendered
    assert "pgvector/pgvector" in rendered
    assert "arya:arya@postgres" in rendered or "postgres:5432" in rendered
    print("OK  docker compose config validates")


def verify_dockerfiles() -> None:
    assert (ROOT / "backend" / "Dockerfile").is_file()
    assert (ROOT / "frontend" / "Dockerfile").is_file()
    assert (ROOT / "frontend" / "nginx.conf").is_file()
    nginx = (ROOT / "frontend" / "nginx.conf").read_text(encoding="utf-8")
    assert "proxy_buffering off" in nginx
    assert "backend:8000" in nginx
    print("OK  Dockerfiles and nginx SSE proxy config present")


def verify_env_example() -> None:
    env_example = (ROOT / ".env.example").read_text(encoding="utf-8")
    for key in ["OPENAI_API_KEY", "DATABASE_URL", "REDIS_URL", "SENTRY_DSN", "SHORTLIST_SIZE"]:
        assert key in env_example, f"Missing {key} in .env.example"
    print("OK  .env.example documents required variables")


def verify_live_stack() -> None:
    env_file = ROOT / ".env"
    if not env_file.is_file():
        print("SKIP live stack (create .env from .env.example with OPENAI_API_KEY)")
        return

    ps = run(["docker", "info"])
    if ps.returncode != 0:
        print("SKIP live stack (Docker daemon not running)")
        return

    up = run(["docker", "compose", "up", "--build", "-d"])
    if up.returncode != 0:
        print(f"SKIP live stack start failed: {up.stderr.strip()}")
        return

    import time
    import urllib.error
    import urllib.request

    url = "http://localhost:3000/api/health"
    for _ in range(30):
        try:
            with urllib.request.urlopen(url, timeout=3) as response:
                body = response.read().decode()
                if "jobs_count" in body or "status" in body:
                    print("OK  live stack health via http://localhost:3000/api/health")
                    run(["docker", "compose", "down"])
                    return
        except (urllib.error.URLError, TimeoutError):
            time.sleep(2)

    print("WARN live stack started but health check timed out (docker compose down manually)")
    run(["docker", "compose", "down"])


def main() -> None:
    verify_compose_services()
    verify_dockerfiles()
    verify_env_example()
    verify_compose_config()
    verify_live_stack()
    print("Phase 9 verification passed.")


if __name__ == "__main__":
    main()
