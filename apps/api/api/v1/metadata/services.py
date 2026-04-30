from uuid import UUID
from .schemas import PartitionPayload, FeaturePayload
from db.connection import get_db_pool


async def register_partition_in_db(payload: PartitionPayload):
    """
    Resolves the dataset by name and inserts a new partition record.

    Input:
        payload.dataset_name   (str) — looked up in datasets table to get UUID
        payload.partition_path (str) — MinIO object path of the Parquet file
        payload.row_count      (int) — number of rows in the file

    Output (success):
        {"status": "success", "message": str, "data": PartitionPayload}

    Output (error):
        {"status": "error", "message": str}
        — if pool is unavailable or dataset_name is not found in catalog
    """
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


async def list_datasets():
    """
    Fetches all datasets from the catalog, ordered by creation time.

    Input: none

    Output (success):
        list of dicts, each containing:
            id               (UUID)
            name             (str)
            storage_location (str)
            created_at       (datetime)

    Output (error):
        {"status": "error", "message": str}  — if pool is unavailable
    """
    pool = await get_db_pool()
    if not pool:
        return {"status": "error", "message": "Database Connection Error"}

    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, storage_location, created_at FROM datasets ORDER BY created_at")

    return [dict(row) for row in rows]


async def list_partitions_for_dataset(dataset_id: UUID):
    """
    Fetches all partitions registered under a specific dataset.

    Input:
        dataset_id (UUID) — the primary key of the target dataset

    Output (success):
        list of dicts, each containing:
            id             (int)
            dataset_id     (UUID)
            partition_path (str)
            row_count      (int | None)
            processed_at   (datetime)

    Output (error):
        {"status": "error", "message": str}  — if pool is unavailable
    """
    pool = await get_db_pool()
    if not pool:
        return {"status": "error", "message": "Database Connection Error"}

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, dataset_id, partition_path, row_count, processed_at FROM partitions WHERE dataset_id = $1 ORDER BY processed_at",
            dataset_id,
        )

    return [dict(row) for row in rows]


async def list_features_for_dataset(dataset_id: UUID):
    """
    Fetches all feature definitions scoped to a specific dataset.

    Input:
        dataset_id (UUID) — the primary key of the target dataset

    Output (success):
        list of dicts, each containing:
            id             (UUID)
            name           (str)
            sql_definition (str)  — Trino SQL that computes this feature
            dataset_id     (UUID)
            created_at     (datetime)

    Output (error):
        {"status": "error", "message": str}  — if pool is unavailable
    """
    pool = await get_db_pool()
    if not pool:
        return {"status": "error", "message": "Database Connection Error"}

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, name, sql_definition, dataset_id, created_at FROM features WHERE dataset_id = $1 ORDER BY created_at",
            dataset_id,
        )

    return [dict(row) for row in rows]


async def register_feature_in_db(payload: FeaturePayload):
    """
    Resolves the dataset by name and inserts a new feature definition record.

    Input:
        payload.name           (str) — unique feature name
        payload.sql_definition (str) — Trino SQL that computes the feature
        payload.dataset_name   (str) — looked up in datasets table to get UUID

    Output (success):
        {"status": "success", "message": str, "data": FeaturePayload}

    Output (error):
        {"status": "error", "message": str}
        — if pool is unavailable or dataset_name is not found in catalog
    """
    pool = await get_db_pool()
    if not pool:
        return {"status": "error", "message": "Database Connection Error"}

    async with pool.acquire() as conn:
        dataset_row = await conn.fetchrow(
            "SELECT id FROM datasets WHERE name = $1",
            payload.dataset_name,
        )

        if not dataset_row:
            return {"status": "error", "message": f"Dataset {payload.dataset_name} not found in catalog"}

        dataset_id = dataset_row['id']

        await conn.execute(
            """
            INSERT INTO features (name, sql_definition, dataset_id)
            VALUES ($1, $2, $3)
            """,
            payload.name,
            payload.sql_definition,
            dataset_id,
        )

    return {
        "status": "success",
        "message": f"Successfully registered feature '{payload.name}' for {payload.dataset_name}",
        "data": payload,
    }
