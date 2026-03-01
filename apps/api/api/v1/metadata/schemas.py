from pydantic import BaseModel

class PartitionPayload(BaseModel):
    dataset_name: str
    partition_path: str
    row_count: int
