from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv(dotenv_path=Path(__file__).resolve().with_name(".env"))


def _get_required_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Environment variable {name} is required")
    return value


def _parse_db_url(db_url: str) -> dict[str, str | int | None]:
    normalized_url = db_url.removeprefix("jdbc:")
    parsed = urlparse(normalized_url)
    return {
        "host": parsed.hostname,
        "port": parsed.port,
        "dbname": parsed.path.lstrip("/") or None,
    }


AUTH_BASE_URL = os.getenv("AUTH_BASE_URL", "https://auth.dev-cinescope.coconutqa.ru/")
API_BASE_URL = os.getenv("API_BASE_URL", "https://api.dev-cinescope.coconutqa.ru/")

LOGIN_ENDPOINT = "/login"
REGISTER_ENDPOINT = "/register"
USER_ENDPOINT = "/user"
MOVIES_ENDPOINT = "/movies"
GENRES_ENDPOINT = "/genres"

DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json",
}

ADMIN_EMAIL = _get_required_env("ADMIN_EMAIL")
ADMIN_PASSWORD = _get_required_env("ADMIN_PASSWORD")
SUPER_ADMIN_EMAIL = os.getenv("SUPER_ADMIN_EMAIL", "api1@gmail.com")
SUPER_ADMIN_PASSWORD = os.getenv("SUPER_ADMIN_PASSWORD", "asdqwe123Q")

DB_URL = os.getenv("DB_URL")
_db_url_parts = _parse_db_url(DB_URL) if DB_URL else {}

DB_HOST = str(_db_url_parts.get("host") or os.getenv("DB_HOST") or "")
DB_PORT = int(_db_url_parts.get("port") or os.getenv("DB_PORT", "5432"))
DB_NAME = str(_db_url_parts.get("dbname") or os.getenv("DB_NAME") or "")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_SSLMODE = os.getenv("DB_SSLMODE", "prefer")
