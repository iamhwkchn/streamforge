from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class PartitionPayload(BaseModel):
    dataset_name: str
    partition_path: str
    row_count: int


class FeaturePayload(BaseModel):
    name: str
    sql_definition: str
    dataset_name: str


class DatasetResponse(BaseModel):
    id: UUID
    name: str
    storage_location: str
    created_at: datetime


class PartitionResponse(BaseModel):
    id: int
    dataset_id: UUID
    partition_path: str
    row_count: int | None
    processed_at: datetime


class FeatureResponse(BaseModel):
    id: UUID
    name: str
    sql_definition: str
    dataset_id: UUID
    created_at: datetime
