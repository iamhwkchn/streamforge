from typing import Literal
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    sql: str
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=1000, ge=1, le=10000)
    sort_by: str | None = None
    sort_dir: Literal["asc", "desc"] = "asc"


class QueryResponse(BaseModel):
    columns: list[str]
    rows: list[list]
    row_count: int
    page: int
    page_size: int
    has_more: bool
