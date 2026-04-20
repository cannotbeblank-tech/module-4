from __future__ import annotations

import re
import time
from typing import Any

import psycopg2
from psycopg2 import sql
from psycopg2.extras import RealDictCursor

from constants import (
    DB_HOST,
    DB_MOVIE_BY_ID_QUERY,
    DB_MOVIES_TABLE,
    DB_NAME,
    DB_PASSWORD,
    DB_PORT,
    DB_SSLMODE,
    DB_USER,
)


class PostgresClient:
    def __init__(self) -> None:
        self.connection = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD,
            sslmode=DB_SSLMODE,
            cursor_factory=RealDictCursor,
        )
        self.connection.autocommit = True

    @staticmethod
    def is_configured() -> bool:
        return all([DB_HOST, DB_NAME, DB_USER, DB_PASSWORD])

    def close(self) -> None:
        self.connection.close()

    @staticmethod
    def _normalize_row(row: dict[str, Any] | None) -> dict[str, Any] | None:
        if row is None:
            return None

        normalized_row = dict(row)
        roles = normalized_row.get("roles")
        if isinstance(roles, str) and roles.startswith("{") and roles.endswith("}"):
            normalized_row["roles"] = [role for role in roles.strip("{}").split(",") if role]
        return normalized_row

    def get_user_by_email(self, email: str) -> dict[str, Any] | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT
                    id,
                    email,
                    full_name AS "fullName",
                    verified,
                    banned,
                    roles
                FROM public.users
                WHERE email = %s
                """,
                (email,),
            )
            row = cursor.fetchone()
        return self._normalize_row(row)

    def set_user_roles(self, email: str, roles: list[str]) -> dict[str, Any] | None:
        with self.connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE public.users
                SET roles = %s::"Role"[], updated_at = now()
                WHERE email = %s
                RETURNING
                    id,
                    email,
                    full_name AS "fullName",
                    verified,
                    banned,
                    roles
                """,
                (roles, email),
            )
            row = cursor.fetchone()
        return self._normalize_row(row)

    def delete_user_by_email(self, email: str) -> int:
        with self.connection.cursor() as cursor:
            cursor.execute("DELETE FROM public.users WHERE email = %s", (email,))
            return cursor.rowcount

    def get_movie_by_id(self, movie_id: int, retries: int = 5, delay: float = 1.0) -> dict[str, Any] | None:
        for attempt in range(retries):
            movie = self._fetch_movie(movie_id)
            if movie is not None:
                return movie
            if attempt < retries - 1:
                time.sleep(delay)
        return None

    def _fetch_movie(self, movie_id: int) -> dict[str, Any] | None:
        with self.connection.cursor() as cursor:
            if DB_MOVIE_BY_ID_QUERY:
                cursor.execute(DB_MOVIE_BY_ID_QUERY, (movie_id,))
            else:
                if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", DB_MOVIES_TABLE):
                    raise ValueError("DB_MOVIES_TABLE contains an invalid SQL identifier")
                query = sql.SQL(
                    """
                    SELECT
                        id,
                        name,
                        description,
                        image_url AS "imageUrl",
                        price,
                        location::text AS location,
                        published,
                        genre_id AS "genreId",
                        created_at AS "createdAt",
                        rating
                    FROM {table}
                    WHERE id = %s
                    """
                ).format(table=sql.Identifier(DB_MOVIES_TABLE))
                cursor.execute(query, (movie_id,))
            row = cursor.fetchone()
        return self._normalize_row(row)
