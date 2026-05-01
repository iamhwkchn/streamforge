from fastapi import APIRouter
from .schemas import QueryRequest, QueryResponse
from .services import execute_query

router = APIRouter()


@router.post("", response_model=QueryResponse, summary="Execute SQL via Trino")
async def run_query(request: QueryRequest):
    """
    Executes a SQL query against Trino and returns the results.

    Request body:
        - sql (str) — any valid Trino SQL

    Response:
        - columns   (list[str]) — column names from the result set
        - rows      (list[list]) — each row as a list of values
        - row_count (int)       — number of rows returned

    Errors:
        - 400 — invalid SQL (Trino query error)
        - 503 — Trino is unreachable
    """
    return await execute_query(request)
