"""Normalize Postgres URLs for SQLAlchemy + asyncpg (Neon, local Docker, etc.)."""

from urllib.parse import parse_qs, urlencode, urlparse, urlunparse


def prepare_async_database_url(database_url: str) -> tuple[str, dict]:
    """
    asyncpg does not accept libpq params like sslmode= in the URL.
    Strip them and pass SSL via connect_args when required.
    """
    url = database_url.strip()
    if url.startswith("postgresql://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    parsed = urlparse(url)
    query = parse_qs(parsed.query, keep_blank_values=True)

    sslmode = (query.pop("sslmode", [None])[0] or "").lower()
    query.pop("channel_binding", None)

    needs_ssl = sslmode in {"require", "verify-ca", "verify-full", "prefer"}
    if parsed.hostname and parsed.hostname.endswith(".neon.tech"):
        needs_ssl = True

    flat_query = {key: values[0] for key, values in query.items() if values}
    clean_url = urlunparse(parsed._replace(query=urlencode(flat_query)))

    connect_args: dict = {"ssl": True} if needs_ssl else {}
    return clean_url, connect_args
