-- Migration: deduplicate partition_path entries and enforce uniqueness.
-- Safe to run on both fresh and existing databases.

-- Remove duplicate partition_path rows, keeping the most recent (highest id).
DELETE FROM partitions
WHERE id NOT IN (SELECT MAX(id) FROM partitions GROUP BY partition_path);

-- Add unique constraint if not already present.
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint
        WHERE conname = 'partitions_partition_path_key'
          AND conrelid = 'partitions'::regclass
    ) THEN
        ALTER TABLE partitions
            ADD CONSTRAINT partitions_partition_path_key UNIQUE (partition_path);
    END IF;
END $$;
