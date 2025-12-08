# Delta Lake Advanced - Lead Engineer Interview

## 1. Delta Lake Architecture

### Transaction Log (_delta_log/)
```
my_table/
├── _delta_log/
│   ├── 00000000000000000000.json  # Version 0
│   ├── 00000000000000000001.json  # Version 1
│   ├── 00000000000000000002.json  # Version 2
│   └── 00000000000000000010.checkpoint.parquet  # Checkpoint every 10
├── part-00000-xxx.parquet
├── part-00001-xxx.parquet
└── ...
```

Each JSON contains:
- `add`: Files added
- `remove`: Files removed (tombstones)
- `metaData`: Schema changes
- `txn`: Application transaction IDs
- `commitInfo`: Who, when, what operation

---

## 2. ACID Properties in Delta Lake

### Atomicity
- Each commit is atomic
- All-or-nothing writes
- If write fails, table unchanged

### Consistency
- Schema enforcement
- Constraints (CHECK, NOT NULL)
- Data validation

### Isolation
- **Optimistic Concurrency Control (OCC)**
- Writers check conflicts at commit time
- Readers see consistent snapshot (MVCC)

### Durability
- Data in Parquet (cloud storage durability)
- Transaction log replicated
- Checkpoints every 10 commits

---

## 3. Time Travel

```python
# Read specific version
df = spark.read.format("delta").option("versionAsOf", 5).load("/path")

# Read as of timestamp
df = spark.read.format("delta").option("timestampAsOf", "2024-01-15").load("/path")

# SQL syntax
SELECT * FROM my_table VERSION AS OF 5
SELECT * FROM my_table TIMESTAMP AS OF '2024-01-15'

# Restore to previous version
RESTORE TABLE my_table TO VERSION AS OF 5
```

---

## 4. MERGE (Upsert)

```python
from delta.tables import DeltaTable

target = DeltaTable.forPath(spark, "/path/to/table")

target.alias("t").merge(
    source.alias("s"),
    "t.id = s.id"
).whenMatchedUpdate(set={
    "name": "s.name",
    "updated_at": "current_timestamp()"
}).whenMatchedDelete(
    condition="s.deleted = true"
).whenNotMatchedInsert(values={
    "id": "s.id",
    "name": "s.name",
    "created_at": "current_timestamp()"
}).execute()
```

### Merge Conditions
- `whenMatchedUpdate`: Update existing rows
- `whenMatchedDelete`: Delete matching rows
- `whenNotMatchedInsert`: Insert new rows
- `whenNotMatchedBySourceDelete`: Delete rows not in source (full sync)

---

## 5. OPTIMIZE & Z-ORDER

### OPTIMIZE (Compaction)
```sql
-- Compact small files into larger ones
OPTIMIZE my_table

-- Optimize specific partition
OPTIMIZE my_table WHERE date = '2024-01-15'
```

### Z-ORDER (Multi-dimensional clustering)
```sql
-- Colocate data by multiple columns
OPTIMIZE my_table ZORDER BY (region, date)
```

**When to use Z-ORDER:**
- Queries filter on multiple columns
- Columns have high cardinality
- Read-heavy workloads

**Z-ORDER Internals:**
- Interleaves bits of column values
- Similar values stored together
- Enables data skipping on multiple columns

---

## 6. VACUUM (Cleanup)

```sql
-- Remove files older than 7 days (default)
VACUUM my_table

-- Remove files older than 24 hours
VACUUM my_table RETAIN 24 HOURS

-- DRY RUN (see what would be deleted)
VACUUM my_table DRY RUN
```

**⚠️ CAUTION:**
- Default retention: 7 days
- Cannot time travel before vacuum
- Concurrent readers may fail if vacuum too aggressive

```python
# Allow shorter retention (dangerous!)
spark.conf.set("spark.databricks.delta.retentionDurationCheck.enabled", "false")
```

---

## 7. Schema Evolution

```python
# Merge schema (add new columns)
df.write.format("delta") \
    .option("mergeSchema", "true") \
    .mode("append") \
    .save("/path")

# Overwrite schema (replace entirely)
df.write.format("delta") \
    .option("overwriteSchema", "true") \
    .mode("overwrite") \
    .save("/path")
```

### Auto Schema Evolution (Delta 2.0+)
```sql
ALTER TABLE my_table SET TBLPROPERTIES (
    'delta.columnMapping.mode' = 'name',
    'delta.minReaderVersion' = '2',
    'delta.minWriterVersion' = '5'
)
```

---

## 8. Change Data Feed (CDC)

```sql
-- Enable CDF
ALTER TABLE my_table SET TBLPROPERTIES (delta.enableChangeDataFeed = true)
```

```python
# Read changes
changes = spark.read.format("delta") \
    .option("readChangeFeed", "true") \
    .option("startingVersion", 5) \
    .table("my_table")

# Columns added:
# _change_type: insert, update_preimage, update_postimage, delete
# _commit_version: Version number
# _commit_timestamp: When changed
```

---

## 9. Deletion Vectors (Delta 3.0+)

**Problem:** DELETE/UPDATE rewrites entire files
**Solution:** Mark deleted rows, skip during read

```sql
ALTER TABLE my_table SET TBLPROPERTIES (
    'delta.enableDeletionVectors' = true
)
```

**Benefits:**
- Faster DELETE/UPDATE (no file rewrite)
- Lazy cleanup during OPTIMIZE

---

## 10. Liquid Clustering (Delta 3.0+)

**Replaces:** Partitioning + Z-ORDER

```sql
CREATE TABLE my_table (id INT, date DATE, region STRING)
CLUSTER BY (region, date)
USING DELTA
```

**Benefits over Z-ORDER:**
- Incremental clustering
- No need for explicit OPTIMIZE
- Automatic data layout optimization

---

## 11. COPY INTO (Incremental Load)

```sql
COPY INTO my_table
FROM '/path/to/files'
FILEFORMAT = PARQUET
FORMAT_OPTIONS ('mergeSchema' = 'true')
COPY_OPTIONS ('mergeSchema' = 'true')
```

**Idempotent:** Tracks processed files, won't reload

---

## 12. Auto Optimize

```sql
-- Table-level
ALTER TABLE my_table SET TBLPROPERTIES (
    delta.autoOptimize.optimizeWrite = true,
    delta.autoOptimize.autoCompact = true
)

-- Session-level
SET spark.databricks.delta.optimizeWrite.enabled = true
SET spark.databricks.delta.autoCompact.enabled = true
```

**optimizeWrite:** Coalesce small files during write
**autoCompact:** Run OPTIMIZE after writes

---

## 13. Cloning

### Shallow Clone
```sql
CREATE TABLE new_table SHALLOW CLONE source_table
```
- Only copies metadata
- Points to same data files
- Fast, no data copy
- Use for: Testing, experiments

### Deep Clone
```sql
CREATE TABLE new_table DEEP CLONE source_table
```
- Full data copy
- Independent table
- Use for: Backup, migration, DR

---

## 14. Constraints

```sql
-- NOT NULL
ALTER TABLE my_table ALTER COLUMN name SET NOT NULL

-- CHECK constraint
ALTER TABLE my_table ADD CONSTRAINT valid_amount CHECK (amount > 0)

-- Drop constraint
ALTER TABLE my_table DROP CONSTRAINT valid_amount
```

---

## 15. Photo Predicate / Data Skipping

**How it works:**
- Delta stores min/max stats per file
- Queries skip files that can't match filter

```python
# See file statistics
spark.read.format("delta").load("/path")._jdf.queryExecution().optimizedPlan()
```

**Best for:**
- Sorted data
- Z-ORDERed data
- Date/timestamp columns

---

## 16. Bloom Filters

```sql
-- Create bloom filter index
CREATE BLOOMFILTER INDEX ON TABLE my_table FOR COLUMNS(user_id)
```

**Use for:**
- High-cardinality columns
- Point lookups (WHERE id = 'abc')
- MERGE operations (finding matches)

---

## 17. Delta Table Properties Cheat Sheet

```sql
-- View all properties
SHOW TBLPROPERTIES my_table

-- Key properties
ALTER TABLE my_table SET TBLPROPERTIES (
    'delta.enableChangeDataFeed' = 'true',
    'delta.autoOptimize.optimizeWrite' = 'true',
    'delta.autoOptimize.autoCompact' = 'true',
    'delta.enableDeletionVectors' = 'true',
    'delta.logRetentionDuration' = 'interval 30 days',
    'delta.deletedFileRetentionDuration' = 'interval 7 days',
    'delta.checkpoint.writeStatsAsStruct' = 'true',
    'delta.checkpoint.writeStatsAsJson' = 'false'
)
```

---

## 18. Common Delta Lake Errors

| Error | Cause | Fix |
|-------|-------|-----|
| ConcurrentAppendException | Two writers on same partition | Retry or use merge |
| ConcurrentDeleteException | Conflict with delete | Check concurrent operations |
| ProtocolChangedException | Version mismatch | Upgrade reader/writer |
| SchemaEvolutionException | Column type change | Use overwriteSchema |
| FileNotFoundException | VACUUM removed in-use file | Increase retention |

---

## 19. Delta Lake vs Parquet

| Feature | Parquet | Delta Lake |
|---------|---------|------------|
| ACID | ❌ | ✅ |
| Time Travel | ❌ | ✅ |
| Schema Evolution | Manual | Auto |
| MERGE/UPSERT | ❌ | ✅ |
| Concurrent Writes | Overwrite | Safe |
| File Compaction | Manual | OPTIMIZE |
| CDC | ❌ | CDF |
