from .schemas import PartitionPayload
from db.connection import get_db_pool

async def register_partition_in_db(payload: PartitionPayload):
    pool = await get_db_pool()
    
    if not pool:
        return {"status": "error", "message": "Database Connection Error"}
        
    async with pool.acquire() as conn:
        dataset_row = await conn.fetchrow(
            "SELECT id FROM datasets WHERE name = $1", 
            payload.dataset_name
        )
        
        if not dataset_row:
            return {"status": "error", "message": f"Dataset {payload.dataset_name} not found in catalog"}
            
        dataset_id = dataset_row['id']
        
        await conn.execute(
            """
            INSERT INTO partitions (dataset_id, partition_path, row_count)
            VALUES ($1, $2, $3)
            """,
            dataset_id,
            payload.partition_path,
            payload.row_count
        )

    # TODO: Reach out to Trino to CALL system.sync_partition_metadata(...)
    return {
        "status": "success",
        "message": f"Successfully registered partition for {payload.dataset_name}",
        "data": payload
    }
