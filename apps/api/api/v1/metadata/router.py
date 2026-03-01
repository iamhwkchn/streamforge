from fastapi import APIRouter
from api.v1.metadata.schemas import PartitionPayload
from api.v1.metadata.services import register_partition_in_db

router = APIRouter()

@router.post("/partitions", summary="Register a partition")
async def register_partition(payload: PartitionPayload):
    return await register_partition_in_db(payload)
