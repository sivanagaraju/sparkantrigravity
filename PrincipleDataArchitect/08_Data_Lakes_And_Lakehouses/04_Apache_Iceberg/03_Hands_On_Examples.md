# Apache Iceberg — Hands-On Examples

The immense power of Apache Iceberg is how heavily it is standardized into pure ANSI SQL. Unlike Spark's proprietary DataFrame DataFrame hooks in older Data Lakes, Iceberg natively hooks exactly how a standard DBA would expect.

## Scenario 1: Creating a Table with Hidden Partitioning

In standard Hive, if you partitioned by date, you had to physically generate a `date_string` column in your data logic. Iceberg does this mathematically behind the scenes.

### Execution (Spark SQL / Athena / Trino)

```sql
-- Notice we are NOT creating a custom partition column string.
-- We are extracting the 'days' mathematical metric from the existing pure timestamp.
CREATE TABLE datalake.events (
    event_id bigint,
    user_id bigint,
    event_time timestamp,
    action string
)
USING iceberg
PARTITIONED BY (days(event_time));

-- We can change the partition strategy to 'hours' next month dynamically
-- without rewriting any of the old data. Iceberg tracks this in the metadata JSON.
ALTER TABLE datalake.events 
REPLACE PARTITION FIELD days(event_time) WITH hours(event_time);
```

---

## Scenario 2: Time Travel and Snapshot Reading

Iceberg's manifest-list topology preserves absolute historical states of the Data Lake precisely.

### Execution (SQL)

```sql
-- 1. Identify what happened to the table over the past week
SELECT * FROM datalake.events.history;
-- Returns a list of Snapshot IDs, Parent IDs, and explicitly what operation occurred (e.g. 'append', 'overwrite')

-- 2. Query the exact state of the Data Lake as it existed precisely at noon yesterday
SELECT * FROM datalake.events 
FOR SYSTEM_TIME AS OF '2023-10-01 12:00:00';

-- 3. Query based on the exact long integer Snapshot ID returned from the history table
SELECT * FROM datalake.events 
FOR SYSTEM_VERSION AS OF 109823749812739812;
```

---

## Scenario 3: Copy-On-Write Deletions (GDPR / PII)

When standard Parquet required 48 hours to rewrite a billion-row table to delete a single user, Iceberg uses its column-statistic Manifest files to rewrite only the specific microscopic MB chunks housing the user.

### Execution (SQL)

```sql
-- This looks like a standard PostgreSQL deletion.
-- Behind the scenes, Iceberg executes intense Min/Max file skipping.
-- It ignores 99.9% of the S3 files completely, downloads the 2 Parquet files 
-- containing User 4029, creates 2 new Parquet files excluding them, and generates 
-- a new metadata.json commit swapping the active file pointers.
DELETE FROM datalake.users WHERE user_id = 4029;
```

---

## Scenario 4: Maintenance Procedures (Rewrite & Expire)

Just like Delta Lake requires `OPTIMIZE` and `VACUUM`, Iceberg requires explicit structural maintenance to prevent the metadata tree from exploding in size over thousands of streaming commits.

### Execution (Spark Call)

```sql
-- 1. The Equivalent of Delta's OPTIMIZE
-- Reads 10,000 tiny 5 KB streaming Parquet files and merges them into optimal massive 1GB chunks.
CALL catalog.system.rewrite_data_files('datalake.events');

-- 2. The Equivalent of Delta's VACUUM
-- Destroys physically deleted Parquet files and orphaned JSON metadata files older than 5 days
-- off the S3 hard drives to save massive cloud storage costs.
CALL catalog.system.expire_snapshots('datalake.events', TIMESTAMP '2023-10-01 00:00:00.000');

-- 3. Rewrite Manifest Lists
-- Over time, the metadata layer (the Manifests) gets highly fragmented.
-- This command consolidates the JSON/Avro metadata tree mathematically to speed up query planning.
CALL catalog.system.rewrite_manifests('datalake.events');
```
