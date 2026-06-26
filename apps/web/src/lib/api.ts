const BASE = '/api/v1';

export interface Dataset {
	id: string;
	name: string;
	storage_location: string;
	created_at: string;
}

export interface Partition {
	id: number;
	dataset_id: string;
	partition_path: string;
	row_count: number | null;
	processed_at: string;
}

export interface Feature {
	id: string;
	name: string;
	sql_definition: string;
	dataset_id: string;
	created_at: string;
}

export interface FeatureWithDataset extends Feature {
	dataset_name: string;
}

export interface DatasetMetrics {
	partition_count: number;
	total_rows: number;
	last_ingested_at: string | null;
}

export interface QueryResult {
	columns: string[];
	rows: unknown[][];
	row_count: number;
	page: number;
	page_size: number;
	has_more: boolean;
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
	const res = await fetch(`${BASE}${path}`, init);
	if (!res.ok) {
		const body = await res.json().catch(() => ({ detail: res.statusText }));
		throw new Error((body as { detail?: string }).detail ?? res.statusText);
	}
	return res.json() as Promise<T>;
}

export const getDatasets = () => request<Dataset[]>('/metadata/datasets');

export const getPartitions = (datasetId: string) =>
	request<Partition[]>(`/metadata/datasets/${datasetId}/partitions`);

export const getFeatures = (datasetId: string) =>
	request<Feature[]>(`/metadata/datasets/${datasetId}/features`);

export const getAllFeatures = () => request<FeatureWithDataset[]>('/metadata/features');

export async function createFeature(name: string, sqlDefinition: string, datasetName: string): Promise<void> {
	const result = await request<{ status: string; message: string }>('/metadata/features', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ name, sql_definition: sqlDefinition, dataset_name: datasetName })
	});
	if (result.status === 'error') {
		throw new Error(result.message);
	}
}

export const getMetrics = (datasetId: string) =>
	request<DatasetMetrics>(`/metadata/datasets/${datasetId}/metrics`);

export async function deleteFeature(featureId: string): Promise<void> {
	const result = await request<{ status: string; message: string }>(`/metadata/features/${featureId}`, {
		method: 'DELETE'
	});
	if (result.status === 'error') {
		throw new Error(result.message);
	}
}

export async function runQuery(
	sql: string,
	page = 1,
	pageSize = 100
): Promise<QueryResult> {
	return request<QueryResult>('/query', {
		method: 'POST',
		headers: { 'Content-Type': 'application/json' },
		body: JSON.stringify({ sql, page, page_size: pageSize })
	});
}
