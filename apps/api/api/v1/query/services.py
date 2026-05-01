import asyncio
import re
import trino
import trino.exceptions
from fastapi import HTTPException

from core.config import settings
from .schemas import QueryRequest, QueryResponse

_ALLOWED_STARTS = re.compile(r"^\s*(select|with)\s", re.IGNORECASE | re.DOTALL)
_SAFE_IDENTIFIER = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")


def _assert_read_only(sql: str) -> None:
    if not _ALLOWED_STARTS.match(sql):
        raise HTTPException(
            status_code=400,
            detail="Only SELECT queries are allowed. DDL and DML are not permitted.",
        )


def _assert_safe_identifier(name: str) -> None:
    if not _SAFE_IDENTIFIER.match(name):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort column: {name!r}. Must be a plain column name.",
        )


def _build_paginated_sql(sql: str, page: int, page_size: int, sort_by: str | None, sort_dir: str) -> str:
    order_clause = f"ORDER BY {sort_by} {sort_dir.upper()}\n" if sort_by else ""
    offset = (page - 1) * page_size
    return (
        f"SELECT * FROM (\n{sql}\n) AS __q\n"
        f"{order_clause}"
        f"OFFSET {offset}\nLIMIT {page_size + 1}"
    )


def _run_query(sql: str, page: int, page_size: int, sort_by: str | None, sort_dir: str) -> QueryResponse:
    paginated = _build_paginated_sql(sql, page, page_size, sort_by, sort_dir)
    conn = None
    try:
        conn = trino.dbapi.connect(
            host=settings.TRINO_HOST,
            port=settings.TRINO_PORT,
            user=settings.TRINO_USER,
            catalog=settings.TRINO_CATALOG,
            schema=settings.TRINO_SCHEMA,
        )
        cursor = conn.cursor()
        cursor.execute(paginated)
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        has_more = len(rows) > page_size
        rows = rows[:page_size]
        return QueryResponse(
            columns=columns,
            rows=[list(r) for r in rows],
            row_count=len(rows),
            page=page,
            page_size=page_size,
            has_more=has_more,
        )
    except trino.exceptions.TrinoQueryError as e:
        raise HTTPException(status_code=400, detail=str(e))
    finally:
        if conn is not None:
            conn.close()


async def execute_query(request: QueryRequest) -> QueryResponse:
    _assert_read_only(request.sql)
    if request.sort_by:
        _assert_safe_identifier(request.sort_by)
    try:
        return await asyncio.to_thread(
            _run_query,
            request.sql,
            request.page,
            request.page_size,
            request.sort_by,
            request.sort_dir,
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Trino unavailable: {e}")
