from uuid import UUID
from fastapi import APIRouter
from api.v1.metadata.schemas import FeaturePayload, PartitionPayload
from api.v1.metadata.services import (
    list_datasets,
    list_features_for_dataset,
    list_partitions_for_dataset,
    register_feature_in_db,
    register_partition_in_db,
)

router = APIRouter()


@router.get("/datasets", summary="List all datasets")
async def get_datasets():
    """
    Returns all datasets registered in the metadata catalog.

    Response: list of
        - id              (UUID)    — unique dataset identifier
        - name            (str)     — dataset name
        - storage_location (str)   — MinIO path where Parquet files live
        - created_at      (datetime)
    """
    return await list_datasets()


@router.get("/datasets/{dataset_id}/partitions", summary="List partitions for a dataset")
async def get_partitions(dataset_id: UUID):
    """
    Returns all partitions registered under the given dataset.

    Path param:
        - dataset_id (UUID) — the dataset to query

    Response: list of
        - id             (int)      — partition row id
        - dataset_id     (UUID)
        - partition_path (str)      — MinIO object path for this partition
        - row_count      (int|null) — number of rows in the Parquet file
        - processed_at   (datetime) — when the partition was registered
    """
    return await list_partitions_for_dataset(dataset_id)


@router.get("/datasets/{dataset_id}/features", summary="List features for a dataset")
async def get_features(dataset_id: UUID):
    """
    Returns all feature definitions scoped to the given dataset.

    Path param:
        - dataset_id (UUID) — the dataset to query

    Response: list of
        - id             (UUID)
        - name           (str)  — feature name
        - sql_definition (str)  — Trino SQL that computes this feature
        - dataset_id     (UUID)
        - created_at     (datetime)
    """
    return await list_features_for_dataset(dataset_id)


@router.post("/partitions", summary="Register a partition")
async def register_partition(payload: PartitionPayload):
    """
    Registers a newly written Parquet partition in the metadata catalog.
    Called by the bootstrap script (and later the stream consumer) after
    each MinIO write.

    Request body (PartitionPayload):
        - dataset_name    (str) — must match an existing datasets.name
        - partition_path  (str) — MinIO object path of the Parquet file
        - row_count       (int) — number of rows written

    Response:
        - status  (str)
        - message (str)
        - data    (PartitionPayload echo)
    """
    return await register_partition_in_db(payload)


@router.post("/features", summary="Register a feature definition")
async def register_feature(payload: FeaturePayload):
    """
    Registers a new feature definition tied to a dataset.

    Request body (FeaturePayload):
        - name           (str) — unique feature name
        - sql_definition (str) — Trino SQL that computes this feature
        - dataset_name   (str) — must match an existing datasets.name

    Response:
        - status  (str)
        - message (str)
        - data    (FeaturePayload echo)
    """
    return await register_feature_in_db(payload)
