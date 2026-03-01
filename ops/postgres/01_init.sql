-- create the dataset table 
CREATE TABLE IF NOT EXISTS datasets (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL, 
    storage_location VARCHAR(512) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

-- create the partitions table 
CREATE TABLE IF NOT EXISTS partitions (
    id SERIAL PRIMARY KEY,
    dataset_id UUID REFERENCES datasets(id),
    partition_path VARCHAR(512) NOT NULL,
    row_count INTEGER,
    processed_at TIMESTAMP DEFAULT NOW()
);

-- create the features table 
CREATE TABLE IF NOT EXISTS features (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) UNIQUE NOT NULL,
    sql_definition TEXT NOT NULL,
    dataset_id UUID REFERENCES datasets(id),
    created_at TIMESTAMP DEFAULT NOW()
);
